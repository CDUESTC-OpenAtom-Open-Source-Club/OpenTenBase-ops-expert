#!/usr/bin/env python3
"""
linux-ssh-access 辅助脚本：基于 Paramiko 的 SSH 连接工具。

用法:
    # 从环境变量 SSH_PASSWORD 读取密码（推荐）
    export SSH_PASSWORD="..."
    python3 {baseDir}/scripts/ssh_connect.py --host <host> --port <port> --user <user> --command "hostname && whoami"

    # 使用 SSH Key
    python3 {baseDir}/scripts/ssh_connect.py --host <host> --port <port> --user <user> --key ~/.ssh/id_ed25519 --command "uname -s"

仅依赖标准库 + Paramiko，建议 Python 3.10+。
密码只从环境变量 SSH_PASSWORD 读取，不接受命令行参数，避免泄漏到进程列表。
"""

import argparse
import json
import os
import sys

try:
    import paramiko
except ImportError:
    print(json.dumps({
        "status": "error",
        "message": "Paramiko 未安装。请执行: pip3 install paramiko",
    }, ensure_ascii=False), file=sys.stderr)
    sys.exit(2)


def main():
    parser = argparse.ArgumentParser(description="基于 Paramiko 的 SSH 连接辅助脚本")
    parser.add_argument("--host", type=str, required=True, help="目标主机 IP 或域名")
    parser.add_argument("--port", type=int, default=22, help="SSH 端口，默认 22")
    parser.add_argument("--user", type=str, required=True, help="SSH 用户名")
    parser.add_argument("--command", type=str, default="hostname && whoami && uname -s",
                        help="远程执行的命令")
    parser.add_argument("--key", type=str, default=None, help="SSH 私钥路径（密钥认证）")
    parser.add_argument("--timeout", type=int, default=10, help="连接超时秒数，默认 10")
    args = parser.parse_args()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if args.key:
            ssh.connect(
                hostname=args.host,
                port=args.port,
                username=args.user,
                key_filename=args.key,
                timeout=args.timeout,
                allow_agent=False,
                look_for_keys=False,
            )
        else:
            password = os.environ.get("SSH_PASSWORD")
            if not password:
                print(json.dumps({
                    "status": "error",
                    "message": "未设置 SSH_PASSWORD 环境变量，无法使用密码认证",
                }, ensure_ascii=False), file=sys.stderr)
                sys.exit(2)
            ssh.connect(
                hostname=args.host,
                port=args.port,
                username=args.user,
                password=password,
                timeout=args.timeout,
                allow_agent=False,
                look_for_keys=False,
            )

        stdin, stdout, stderr = ssh.exec_command(args.command)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="replace").strip()
        err = stderr.read().decode("utf-8", errors="replace").strip()

        result = {
            "status": "ok" if exit_code == 0 else "error",
            "exit_code": exit_code,
            "stdout": out,
            "stderr": err,
            "host": args.host,
            "user": args.user,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(exit_code)

    except paramiko.AuthenticationException:
        print(json.dumps({
            "status": "error",
            "message": "认证失败：用户名、密码或密钥错误",
            "host": args.host,
            "user": args.user,
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": f"连接异常: {e}",
            "host": args.host,
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    finally:
        ssh.close()
        # 清理密码环境变量
        if "SSH_PASSWORD" in os.environ:
            del os.environ["SSH_PASSWORD"]


if __name__ == "__main__":
    main()
