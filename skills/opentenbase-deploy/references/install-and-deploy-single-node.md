# 多版本安装与单节点部署

> 本文档覆盖：软件包安装（三种途径）、版本选择（2.5 / 2.6 / 5.0）、单节点部署（一键 + 手动）。

---

## 版本与集群管理工具对照

| 版本 | 集群管理工具 | CN 端口 | 说明 |
|------|------------|---------|------|
| **2.5** | `pgxc_ctl` | 5432 | 旧版 Postgres-XL 链路 |
| **2.6** | `pgxc_ctl` | 5432 | 含功能增强 |
| **5.0**（默认） | `opentenbase_ctl` | **11003** | 新版链路，推荐 |

> **核心原则**：用户和脚本只与集群管理工具交互，不直接调用 `pg_ctl`/`initdb`。

---

## 软件包安装

### 途径 A：配置官方仓库后用包管理器装（推荐）

**APT 系（Ubuntu/Debian）**：

```bash
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/setup-apt.sh | sudo bash
sudo apt update && sudo apt install -y opentenbase
sudo apt install -y sshpass
```

**RPM 系（RHEL/Rocky/Alma/Fedora/openEuler）**：

```bash
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/setup-rpm.sh | sudo bash
sudo dnf install -y opentenbase
sudo dnf install -y sshpass
```

> `setup-apt.sh` 支持 `--version 5.0|2.6.0|2.5.0` 指定版本。
> GPG 校验失败时：APT 加 `--allow-unauthenticated`，DNF 加 `--nogpgcheck`。

### 途径 B：通用安装器（已合并入 `opentenbase.sh`）

> **2026-06-30 变更**：官方仓库已将 `install.sh` 删除，功能合并到统一入口 `opentenbase.sh` 中。以下是旧版 `install.sh` 的用法记录（供已下载用户参考，新用户直接使用 `opentenbase.sh install`）。

```bash
# 通过 opentenbase.sh 统一入口安装
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/opentenbase.sh | sudo bash

# 指定版本
sudo bash opentenbase.sh install --yes --version 5.0   # 或 2.6.0 / 2.5.0

# 旧版 install.sh 用法（仅仓库已有副本可用）：
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/install.sh | sudo bash
sudo bash install.sh --version 2.6.0
sudo bash install.sh --build-from-source
sudo bash install.sh /path/to/packages/
sudo bash install.sh --force
```

> 装完会安装 `opentenbase-switch-version` 命令（详见 `version-switch.md`）。

### 途径 C：手动下载 release 包

```bash
# DEB
wget https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/releases/download/v5.0-p32/opentenbase_5.0-p32_amd64.deb
sudo dpkg -i opentenbase_*.deb && sudo apt-get install -f -y

# RPM
wget https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/releases/download/v5.0-p32/opentenbase-5.0-p32.x86_64.rpm
sudo rpm -ivh opentenbase-*.rpm
```

---

## 单节点部署 — 一键自动化（推荐）

### 30 秒极速部署

```bash
# 交互式（推荐新手）
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/opentenbase.sh | sudo bash

# 非交互式（CI 用）
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/opentenbase.sh | sudo bash -s -- --yes

# 带子命令方式
sudo bash opentenbase.sh install --yes
```

### 交互式提示说明

```
? 集群名称 [otb01]:
? GTM 节点 IP [127.0.0.1]:
? Coordinator 节点 IP [127.0.0.1]:
? Datanode 节点 IP [127.0.0.1]:
? SSH 端口 [22]:
? 请输入 opentenbase 用户的 SSH 密码:
? 确认开始部署？ [Y/n]:
```

直接回车使用默认值即可完成单节点部署。

### 脚本自动完成的 6 步

1. **环境检查** — root/内存/磁盘/CPU/OS 检测
2. **安装软件包** — 自动检测 APT/RPM，安装 `opentenbase` + `sshpass`
3. **系统准备** — 创建用户 → 设密码 → sudo 免密 → 启动 sshd → 路径符号链接
4. **集群配置** — 收集参数 → 生成 INI（`chmod 600` 保护密码）
5. **安装集群** — `opentenbase_ctl install -c /tmp/opentenbase_config.ini`（含 GTM 2核自动修复）
6. **启动验证** — `status` + psql 连接测试 + 分布式表 CRUD

### 常用命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--yes` / `-y` | 非交互式 | false |
| `--version VER` | OpenTenBase 版本 | `5.0` |
| `--cluster-name NAME` | 集群名称 | `otb01` |
| `--ssh-user USER` | SSH 用户名 | `opentenbase` |
| `--ssh-password PASS` | SSH 密码 | `opentenbase` |
| `--ssh-port PORT` | SSH 端口 | `22` |
| `--skip-install` | 跳过包安装 | false |
| `--no-start` | 只装不启 | false |

### 部署后连接（5.0 CN 端口 = 11003）

```bash
export LD_LIBRARY_PATH=/var/lib/opentenbase/install/opentenbase/5.0/lib
psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres -c "SELECT version();"
```

---

## 单节点部署 — 手动安装

适合需要精细控制配置的用户。以下以 **5.0** 为例。

### Step 1：系统准备

```bash
# 创建 opentenbase 用户
sudo useradd -m -s /bin/bash opentenbase 2>/dev/null || true
sudo passwd opentenbase

# sudo 免密
echo "opentenbase ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/opentenbase

# 启动 SSH
sudo systemctl start sshd 2>/dev/null || sudo systemctl start ssh 2>/dev/null || true

# 路径符号链接（解决 OSS_INSTALL_DIR 硬编码）
sudo mkdir -p /usr/local/install
sudo ln -sf /usr/lib/opentenbase/5.0 /usr/local/install/opentenbase
```

### Step 2：创建部署 tar.gz 包

`opentenbase_ctl` 的 `pre_process_pkg()` 要求 `package=` 是 tar.gz 文件：

```bash
cd /usr/lib/opentenbase/5.0
sudo tar -zcf /tmp/opentenbase-5.0.tar.gz *
tar -tzf /tmp/opentenbase-5.0.tar.gz | grep "bin/opentenbase_ctl"  # 验证
```

### Step 3：创建 INI 配置文件

```bash
sudo cp /etc/opentenbase/5.0/opentenbase_config.ini.example /tmp/otb_config.ini
sudo vi /tmp/otb_config.ini
```

单节点配置示例：

```ini
[instance]
name=opentenbase01
type=distributed
package=/tmp/opentenbase-5.0.tar.gz

[gtm]
master=127.0.0.1

[coordinators]
master=127.0.0.1
nodes-per-server=1

[datanodes]
master=127.0.0.1
nodes-per-server=1

[server]
ssh-user=opentenbase
ssh-port=22

[log]
level=INFO
```

> 单节点本地部署可省略 `ssh-password`（本地 IP 走 `cp` 拷贝不走 SSH）。

### Step 4：安装集群

```bash
sudo -u opentenbase opentenbase_ctl install -c /tmp/otb_config.ini
```

### Step 5：验证

```bash
opentenbase_ctl status
export LD_LIBRARY_PATH=/var/lib/opentenbase/install/opentenbase/5.0/lib
psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres -c "SELECT version();"
```

成功标准：`status` 全 running + `psql` 返回版本号。

---

## 前置条件

- `sudo` 或 `root` 权限
- **内存 ≥ 4GB**（Coordinator 共享内存约 4GB，无法调优降低）
- 磁盘最低 2GB，推荐 10GB+
- 受支持发行版（Ubuntu 18.04–25.04 / Debian 10–13 / CentOS Stream 8/9 / Rocky 8/9 / AlmaLinux 8/9 / Fedora 40 / openEuler 22.03）
- 架构：x86_64 + aarch64

> 内存 < 4GB 不要硬上完整集群，可走低内存 DN 方案（加入远程集群）。

---

## 安装后目录结构

| 路径 | 用途 |
|------|------|
| `/usr/lib/opentenbase/5.0/bin/opentenbase_ctl` | 官方 C++ 集群管理二进制 |
| `/usr/lib/opentenbase/5.0/bin/` | 其他二进制（postgres, gtm_ctl, initdb, psql 等） |
| `/usr/lib/opentenbase/5.0/lib/` | 运行时库（libpq.so, libpqxx.so 等） |
| `/var/lib/opentenbase/install/opentenbase/5.0/` | 运行时部署目录 |
| `/etc/opentenbase/5.0/` | 配置文件目录 |
| `/usr/local/install/opentenbase` | 符号链接 → `/usr/lib/opentenbase/5.0` |
