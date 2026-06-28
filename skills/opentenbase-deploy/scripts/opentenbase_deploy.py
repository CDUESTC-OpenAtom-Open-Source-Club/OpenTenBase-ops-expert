#!/usr/bin/env python3
"""
opentenbase-deploy 辅助脚本：OpenTenBase 环境检查与状态验证工具。

用法:
    # 环境检查（部署前）：在目标服务器上执行，输出 JSON
    python3 {baseDir}/scripts/opentenbase_deploy.py --action check

    # 状态验证（部署后）：检查集群节点状态与连接
    python3 {baseDir}/scripts/opentenbase_deploy.py --action status [--port 5432] [--user opentenbase] [--db postgres]

仅依赖标准库，建议 Python 3.10+。
本脚本只做检查与验证，不执行实际安装/部署（由 AI 通过 SSH 接管）。
退出码：0=通过，1=不满足/失败，2=参数错误。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys


def run(cmd):
    """运行命令，返回 (returncode, stdout, stderr)。失败不抛异常。"""
    try:
        p = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def read_os():
    rc, out, _ = run("cat /etc/os-release")
    info = {"name": "", "id": "", "version_id": "", "id_like": ""}
    if rc == 0:
        for line in out.splitlines():
            if line.startswith("NAME="):
                info["name"] = line.split("=", 1)[1].strip('"')
            elif line.startswith("ID="):
                info["id"] = line.split("=", 1)[1].strip('"')
            elif line.startswith("VERSION_ID="):
                info["version_id"] = line.split("=", 1)[1].strip('"')
            elif line.startswith("ID_LIKE="):
                info["id_like"] = line.split("=", 1)[1].strip('"')
    return info


# 官方支持矩阵
SUPPORTED = {
    "ubuntu": ["20.04", "22.04", "24.04", "25.04"],
    "debian": ["11", "12", "13"],
    "rocky": ["8", "9"],
    "almalinux": ["8", "9"],
    "centos": ["8", "9"],
    "fedora": ["40"],
    "openeuler": ["22.03"],
    "opencloudos": ["8", "9"],
    "anolis": ["8", "9"],
    "tencentos": ["2", "3"],
}

# APT 系发行版
APT_FAMILY = {"ubuntu", "debian", "linuxmint", "pop"}


def detect_install_method(osinfo):
    """判断用哪个 setup 脚本：返回 ('apt'/'rpm', script_name) 或 (None, None)。"""
    os_id = osinfo["id"]
    if os_id in APT_FAMILY:
        return "apt", "setup-apt.sh"
    # RHEL 系及所有 RHEL 兼容发行版统一用 setup-rpm.sh（脚本已支持 ID_LIKE 兜底）
    if os_id in SUPPORTED and os_id not in APT_FAMILY:
        return "rpm", "setup-rpm.sh"
    # 未知 ID 但 ID_LIKE 含 rhel/fedora/centos
    like = osinfo.get("id_like", "")
    if any(k in like.lower() for k in ("rhel", "fedora", "centos")):
        return "rpm", "setup-rpm.sh"
    if "debian" in like.lower() or "ubuntu" in like.lower():
        return "apt", "setup-apt.sh"
    return None, None


def check_env():
    result = {
        "status": "ok",
        "action": "check",
        "checks": [],
        "can_deploy": True,
        "blockers": [],
    }

    def add(name, ok, detail, blocker=False):
        result["checks"].append({"name": name, "ok": ok, "detail": detail})
        if blocker and not ok:
            result["blockers"].append(name)
            result["can_deploy"] = False

    # OS
    osinfo = read_os()
    os_supported = osinfo["id"] in SUPPORTED and osinfo["version_id"] in SUPPORTED[osinfo["id"]]
    install_family, setup_script = detect_install_method(osinfo)
    detail = f"{osinfo['name']} {osinfo['version_id']} (id={osinfo['id']})"
    if os_supported:
        detail += " — 官方支持"
    elif install_family:
        detail += f" — {install_family.upper()} 系，setup-rpm.sh 已支持（ID_LIKE 兜底）"
    else:
        detail += " — 不在官方支持列表，可能不兼容"
    result["setup_script"] = setup_script
    result["install_family"] = install_family
    result["os_official"] = os_supported
    add("os", os_supported or install_family is not None, detail, blocker=False)

    # 架构
    rc, arch, _ = run("uname -m")
    arch_ok = arch in ("x86_64", "aarch64")
    add("arch", arch_ok, arch, blocker=False)

    # 内存（硬性 ≥ 4GB）
    rc, out, _ = run("free -m")
    mem_mb = 0
    if rc == 0:
        m = re.search(r"Mem:\s+(\d+)", out)
        if m:
            mem_mb = int(m.group(1))
    mem_ok = mem_mb >= 4096
    add("memory", mem_ok, f"{mem_mb} MB（要求 ≥4096 MB）",
        blocker=True)

    # 磁盘
    rc, out, _ = run("df -m /")
    disk_mb = 0
    if rc == 0:
        lines = out.splitlines()
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 4:
                disk_mb = int(parts[3])
    disk_ok = disk_mb >= 10240
    add("disk", disk_ok, f"剩余 {disk_mb} MB（建议 ≥10240 MB）",
        blocker=False)

    # 端口
    rc, out, _ = run("ss -tlnp")
    occupied = []
    if rc == 0:
        for port in ("5432", "5433", "5434", "5435"):
            if port in out:
                occupied.append(port)
    port_ok = len(occupied) == 0
    add("ports", port_ok,
        "空闲" if port_ok else f"占用: {','.join(occupied)}",
        blocker=True)

    # sudo
    rc, _, _ = run("sudo -n true")
    add("sudo", rc == 0, "免密sudo可用" if rc == 0 else "sudo需密码或不可用",
        blocker=False)

    # 已安装
    rc, _, _ = run("which opentenbase-ctl")
    installed = rc == 0
    add("installed", True, "已安装" if installed else "未安装",
        blocker=False)

    # Docker
    rc, dv, _ = run("docker --version")
    add("docker", rc == 0, dv if rc == 0 else "无 Docker",
        blocker=False)

    result["status"] = "ok" if result["can_deploy"] else "blocked"
    return result


def check_status(port, user, db):
    result = {
        "status": "ok",
        "action": "status",
        "checks": [],
        "deploy_ok": True,
    }

    def add(name, ok, detail, critical=False):
        result["checks"].append({"name": name, "ok": ok, "detail": detail})
        if critical and not ok:
            result["deploy_ok"] = False

    # ctl 存在
    rc, _, _ = run("which opentenbase-ctl")
    add("ctl_exists", rc == 0, "opentenbase-ctl 存在" if rc == 0 else "未找到 opentenbase-ctl",
        critical=True)
    if rc != 0:
        result["status"] = "fail"
        return result

    # status
    rc, out, err = run("sudo opentenbase-ctl status")
    add("cluster_status", rc == 0,
        out if rc == 0 else (err or "status 失败"),
        critical=True)

    # 节点 running 判定
    if rc == 0 and out:
        running = out.lower().count("running")
        add("nodes_running", running >= 3,
            f"running 计数={running}（期望 GTM+Coordinator+Datanode）",
            critical=True)

    # 连接
    psql = shutil.which("opentenbase-psql") or shutil.which("psql")
    if psql:
        rc, out, err = run(
            f"{psql} -h 127.0.0.1 -p {port} -U {user} -d {db} -c 'SELECT version();'"
        )
        add("connection", rc == 0,
            out.splitlines()[0] if rc == 0 and out else (err or "连接失败"),
            critical=True)
    else:
        add("connection", False, "未找到 psql/opentenbase-psql", critical=True)

    result["status"] = "ok" if result["deploy_ok"] else "fail"
    return result


def main():
    parser = argparse.ArgumentParser(description="OpenTenBase 环境检查与状态验证")
    parser.add_argument("--action", type=str, required=True,
                        choices=["check", "status"],
                        help="check=部署前环境检查；status=部署后状态验证")
    parser.add_argument("--port", type=int, default=5432, help="Coordinator 端口")
    parser.add_argument("--user", type=str, default="opentenbase", help="连接用户")
    parser.add_argument("--db", type=str, default="postgres", help="连接数据库")
    parser.add_argument("--output", type=str, default="-", help="输出路径（默认 stdout）")
    args = parser.parse_args()

    if args.action == "check":
        result = check_env()
    else:
        result = check_status(args.port, args.user, args.db)

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(output)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)

    # 退出码：blocked/fail → 1
    sys.exit(0 if result["status"] == "ok" else 1)


if __name__ == "__main__":
    main()
