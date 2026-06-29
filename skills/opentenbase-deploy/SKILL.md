---
name: opentenbase-deploy
description: 当用户表达"部署 OpenTenBase""装一下 OTB""搭建分布式数据库"等意图时使用。引导用户选择部署方式（一键自动化部署 / 手动安装 / Docker Compose），支持单节点和多机多节点拓扑，完成部署并验证，最后给出连接信息。基于开源仓库 OpenTenBase-Packages。
version: 3.2.0
user-invocable: true
---

# OpenTenBase 部署（引导式）

目标：在目标 Linux 服务器上完成 OpenTenBase 分布式数据库部署，验证可用，并返回连接信息。

把用户当作第一次部署的小白：每一步说清楚在做什么、为什么这么做，关键决策点要主动咨询用户，不要替用户拍板。

---

## 部署源仓库

- 仓库：`https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages`
- 维护：CDUESTC 开源社团（blackEvil217 / muzimu217）
- 许可证：Apache 2.0
- 最新版本：`v5.0-p32`（截至 2026-06，含 GTM 2核修复 + 端口修正 + 全命令 `-c` 支持）
- 支持 15+ 发行版（Ubuntu/Debian/Rocky/AlmaLinux/CentOS Stream/Fedora/openEuler），x86_64 与 aarch64

---

## 三种部署方式总览

| # | 方式 | 定位 | 适用场景 | 交互 |
|---|------|------|---------|------|
| **1** | **一键自动化部署** | 白板机器→集群运行，一条命令 | **推荐**，生产/学习/快速体验 | 交互式 + 非交互式 |
| **2** | **手动安装** | APT/RPM 装包 + `opentenbase_ctl install` | 需要精细控制配置的高级用户 | 手动编辑 INI |
| **3** | **Docker Compose** | 容器隔离，每节点独立 IP | 开发/测试/CI/CD | 一键 `docker compose up` |

**默认推荐方式一**。除非用户明确说"我要手动配置"或"用 Docker"，否则直接走一键部署。

---

## 部署拓扑说明

OpenTenBase 是分布式数据库，包含三种节点角色：**GTM**（全局事务管理器）、**Coordinator/CN**（协调节点，客户端入口）、**Datanode/DN**（数据节点，存储数据）。

| 拓扑 | 架构 | 适用场景 | 支持状态 |
|------|------|---------|---------|
| **单节点** | GTM + CN 在同一台机器 | 开发测试、学习 | ✅ 支持（`127.0.0.1`） |
| **多机多节点** | GTM / CN / DN 分布在不同服务器 | 生产环境 | ✅ 支持 |
| **Docker 多节点** | 每个节点一个容器，独立 IP | 开发测试 | ✅ 支持 |
| ~~单机多节点~~ | GTM + CN + DN 在同一台物理机 | — | ❌ **不支持** |

### 为什么单机多节点不支持？

CN 和 DN 都有 **forward manager**（查询转发器），默认绑定 `127.0.0.1:6670`。单机部署时 CN 和 DN 共享 IP，第二个节点启动会报 `Address already in use`。

> **替代方案**：想在一台机器上跑多节点，用 **Docker Compose**（方式三），每个容器有独立 IP。

---

## opentenbase_ctl 命令规则

从 `v5.0-p12` 起，使用官方 C++ 二进制 `opentenbase_ctl`（下划线，非连字符）。

> **重要变更（v3.1.0）**：所有命令都需要 `-c` 配置文件参数，不仅仅是 `install`。

| 命令 | 用途 | 示例 |
|------|------|------|
| `install` | 安装集群（initdb + 配置 + 启动 + 节点注册） | `opentenbase_ctl install -c config.ini` |
| `start` | 启动已安装的集群 | `opentenbase_ctl start -c config.ini` |
| `stop` | 停止集群 | `opentenbase_ctl stop -c config.ini` |
| `status` | 查看各节点状态 | `opentenbase_ctl status -c config.ini` |
| `delete` | 删除集群（停止 + 清理数据） | `opentenbase_ctl delete -c config.ini` |
| `expand` | 扩容（添加新节点） | `opentenbase_ctl expand -c config.ini` |
| `shrink` | 缩容（移除节点） | `opentenbase_ctl shrink -c config.ini` |

**关键**：所有命令都必须带 `-c config.ini`。不带 `-c` 会报 `Failed to extract version from package name` 错误。指定单节点：`opentenbase_ctl start -c config.ini -n cn0001`。

### SSH 方式：sshpass（无需密钥互信）

`opentenbase_ctl` 通过 `sshpass` + SSH 账号密码远程执行命令，**不需要配置 SSH 密钥互信**。在 INI 配置文件 `[server]` section 中填写 `ssh-user` / `ssh-password` / `ssh-port` 即可。

---

## 前置条件

- 拥有 `sudo` 或 `root` 权限
- 内存 **≥ 4GB**（硬性要求；2GB 服务器 GTM 会 OOM）
- 磁盘 ≥ 10GB
- 受支持发行版（Ubuntu 20.04+/Debian 11+/RHEL 8+/Rocky/Alma/Fedora/openEuler）
- 多机部署时：各服务器间网络互通，所有节点使用相同的 SSH 用户名和密码

---

## 处理流程

### 阶段一：环境检查

连接服务器后，先收集环境信息：

```bash
# 操作系统
cat /etc/os-release | grep -E "^(NAME|VERSION_ID|ID)="

# CPU 架构
uname -m

# 内存（必须 ≥ 4GB）
free -h

# 磁盘
df -h /

# 端口占用
ss -tlnp | grep -E ":(11003|6666|15432|6669|6670)" || echo "端口空闲"

# Docker
which docker 2>/dev/null && docker --version || echo "无 Docker"
```

也可使用辅助脚本：

```bash
python3 {baseDir}/scripts/opentenbase_deploy.py --action check
```

**硬性拦截**：
- 内存 < 4GB → 停止，告知"内存不足"
- 端口被占用 → 报告哪个端口被占，询问处理方式

### 阶段二：咨询用户选择部署方式和拓扑

> OpenTenBase 有三种部署方式：
>
> **方式一：一键自动化部署（推荐）**
> 白板机器上一条命令搞定，自动装包、配置、安装集群、验证。支持交互式（问你几个问题）和非交互式（全自动）。
>
> **方式二：手动安装**
> 先装软件包，再编辑 INI 配置文件，最后执行 `opentenbase_ctl install`。适合需要精细控制配置的用户。
>
> **方式三：Docker Compose**
> 每个节点一个容器，独立 IP，互不冲突。适合开发测试。
>
> 另外，你需要哪种拓扑？
> - **单节点**：GTM + CN 在一台机器（默认）
> - **多机多节点**：GTM / CN / DN 分布在不同服务器（生产环境）

根据用户选择进入对应流程。

---

## 方式一：一键自动化部署（推荐）

### 核心脚本：`deploy-opentenbase.sh`

白板机器上一条命令完成全部步骤：安装包 → 创建用户 → 配置 sshpass → 路径符号链接 → 生成 INI → `opentenbase_ctl install` → 启动验证。

### 三种使用模式

**模式 A：交互式（推荐新手）**

```bash
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/deploy-opentenbase.sh | sudo bash
```

运行后会问几个问题（直接回车用默认值）：
```
? 集群名称 [otb01]:
? GTM 节点 IP [127.0.0.1]:
? Coordinator 节点 IP [127.0.0.1]:
? Datanode 节点 IP [127.0.0.1]:
? SSH 端口 [22]:
? 请输入 opentenbase 用户的 SSH 密码:
? 确认开始部署？ [Y/n]:
```

**模式 B：非交互式（CI/自动化）**

```bash
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/deploy-opentenbase.sh | sudo bash -s -- --yes
```

零交互，全部使用默认值（单节点 `127.0.0.1`，密码 `opentenbase`）。

**模式 C：非交互式 + 自定义参数（多机多节点）**

```bash
sudo bash deploy-opentenbase.sh --yes \
    --cluster-name prod01 \
    --gtm-ip 192.168.1.10 \
    --cn-ip 192.168.1.11 \
    --dn-ip 192.168.1.12 \
    --ssh-user opentenbase \
    --ssh-password MyPass123 \
    --ssh-port 22
```

### 脚本命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--yes` / `-y` | 非交互式，使用默认值 | false（交互式） |
| `--ssh-password PASS` | SSH 密码 | 交互式询问或 `opentenbase` |
| `--cluster-name NAME` | 集群名称 | `otb01` |
| `--gtm-ip IP` | GTM 节点 IP | `127.0.0.1` |
| `--cn-ip IP` | Coordinator 节点 IP | 同 gtm-ip |
| `--dn-ip IP` | Datanode 节点 IP | 同 gtm-ip |
| `--ssh-user USER` | SSH 用户名 | `opentenbase` |
| `--ssh-port PORT` | SSH 端口 | `22` |
| `--version VER` | OpenTenBase 版本 | `5.0` |
| `--skip-install` | 跳过包安装（已装时用） | false |
| `--no-start` | 安装后不启动集群 | false（默认启动） |
| `--help` / `-h` | 显示帮助 | — |

### 脚本自动完成的 6 步

1. **环境检查** — root/内存/磁盘/CPU/OS 检测
2. **安装软件包** — 自动检测 APT/RPM，安装 `opentenbase` + `sshpass`
3. **系统准备** — 创建用户 → 设密码 → sudo 免密 → 启动 sshd → 路径符号链接
4. **集群配置** — 交互式收集参数或使用默认值 → 生成 INI 配置（`chmod 600` 保护密码）
5. **安装集群** — `opentenbase_ctl install -c /tmp/opentenbase_config.ini`（含 GTM 2核自动修复）
6. **启动验证** — `opentenbase_ctl status -c` + psql 连接测试（端口 11003）+ 分布式表 CRUD 测试

### 多机多节点部署示例

场景：3 台服务器，GTM 在 .10，CN 在 .11，DN 在 .12。

在任意一台服务器（推荐 GTM 所在机器）执行：

```bash
sudo bash deploy-opentenbase.sh --yes \
    --gtm-ip 192.168.1.10 \
    --cn-ip 192.168.1.11 \
    --dn-ip 192.168.1.12 \
    --ssh-password MyPass123
```

**前提条件**：
- 三台服务器都已安装 `opentenbase` 软件包（用 `--skip-install` 跳过本机安装，其他机器需手动装）
- 三台服务器的 `opentenbase` 用户密码一致
- 执行机已安装 `sshpass`
- 三台服务器都创建了路径符号链接（见下方"已知问题"）
- 防火墙开放端口：6666（GTM）、11003（CN）、15432（DN）

### 反馈用户

部署完成后告知用户：

> OpenTenBase 部署成功！
> - 部署方式：一键自动化部署
> - 集群状态：GTM / Coordinator / Datanode 全部 running
>
> 连接命令：
> ```
> export LD_LIBRARY_PATH=/var/lib/opentenbase/install/opentenbase/5.0/lib
> psql -h <CN_IP> -p 11003 -U opentenbase -d postgres
> ```
>
> 常用管理命令（所有命令都需要 `-c` 参数）：
> - `opentenbase_ctl status -c config.ini` — 查看状态
> - `opentenbase_ctl stop -c config.ini` — 停止
> - `opentenbase_ctl start -c config.ini` — 启动
> - `opentenbase_ctl delete -c config.ini` — 删除集群

---

## 方式二：手动安装（APT/RPM + opentenbase_ctl）

适合需要精细控制配置的用户。

### Step 1：安装软件包

**APT 系**（Ubuntu/Debian）：

```bash
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/setup-apt.sh | sudo bash
sudo apt update && sudo apt install -y opentenbase
sudo apt install -y sshpass
```

**RPM 系**（RHEL/Rocky/Alma/Fedora/openEuler）：

```bash
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/setup-rpm.sh | sudo bash
sudo dnf install -y opentenbase
sudo dnf install -y sshpass
```

> GPG 校验失败时：APT 加 `--allow-unauthenticated`，DNF 加 `--nogpgcheck`。

### Step 2：系统准备

```bash
# 创建 opentenbase 用户
sudo useradd -m -s /bin/bash opentenbase 2>/dev/null || true
sudo passwd opentenbase  # 设置密码

# sudo 免密（安装过程中需要）
echo "opentenbase ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/opentenbase

# 启动 SSH 服务
sudo systemctl start sshd 2>/dev/null || sudo systemctl start ssh 2>/dev/null || true

# 创建路径符号链接（解决 OSS_INSTALL_DIR 硬编码问题）
sudo mkdir -p /usr/local/install
sudo ln -sf /usr/lib/opentenbase/5.0 /usr/local/install/opentenbase
```

### Step 2.5：创建部署 tar.gz 包

`opentenbase_ctl` 的 `pre_process_pkg()` 要求 `package=` 是 tar.gz 文件而非目录（`excute_cp_file()` 对本地 IP 使用 `cp` 不支持目录）。手动安装时需先打包：

```bash
cd /usr/lib/opentenbase/5.0
sudo tar -zcf /tmp/opentenbase-5.0.tar.gz *
# 验证 opentenbase_ctl 在包中
tar -tzf /tmp/opentenbase-5.0.tar.gz | grep "bin/opentenbase_ctl"
```

### Step 3：创建 INI 配置文件

```bash
sudo cp /etc/opentenbase/5.0/opentenbase_config.ini.example /tmp/otb_config.ini
sudo vi /tmp/otb_config.ini
```

#### INI 配置格式

```ini
[instance]
name=opentenbase01          # 集群名称
type=distributed             # distributed（分布式）
package=/tmp/opentenbase-5.0.tar.gz  # 必须是 tar.gz 文件，不能是目录！

[gtm]
master=127.0.0.1            # GTM 主节点 IP

[coordinators]
master=127.0.0.1            # CN 节点 IP（多个用逗号分隔）
nodes-per-server=1          # 每台服务器上部署几个 CN

[datanodes]
master=127.0.0.1            # DN 节点 IP（多个用逗号分隔）
nodes-per-server=1

[server]
ssh-user=opentenbase        # SSH 用户（所有节点必须一致）
ssh-password=your_password  # SSH 密码
ssh-port=22

[log]
level=INFO
```

#### 单节点配置（GTM + CN 同机）

```ini
[gtm]
master=127.0.0.1

[coordinators]
master=127.0.0.1
nodes-per-server=1

[datanodes]
master=127.0.0.1
nodes-per-server=1
```

#### 多机多节点配置（3 台服务器）

场景：GTM 在 .10，CN 在 .11，DN 在 .12

```ini
[gtm]
master=192.168.1.10

[coordinators]
master=192.168.1.11
nodes-per-server=1

[datanodes]
master=192.168.1.12
nodes-per-server=1
```

#### 多机多 DN 配置（1 GTM + 1 CN + 3 DN）

```ini
[gtm]
master=192.168.1.10

[coordinators]
master=192.168.1.11
nodes-per-server=1

[datanodes]
master=192.168.1.12,192.168.1.13,192.168.1.14
nodes-per-server=1
```

#### 多机多 CN + 多 DN 配置

```ini
[gtm]
master=192.168.1.10

[coordinators]
master=192.168.1.11,192.168.1.12
nodes-per-server=1

[datanodes]
master=192.168.1.13,192.168.1.14,192.168.1.15
nodes-per-server=1
```

> **多机部署前提**：每台服务器都要装好 `opentenbase` 软件包 + 创建相同的 SSH 用户 + 创建路径符号链接。

### Step 4：安装集群

```bash
# 以 opentenbase 用户执行
sudo -u opentenbase opentenbase_ctl install -c /tmp/otb_config.ini
```

`opentenbase_ctl install` 自动完成：
1. 处理安装包（SCP 传输到各节点并解压）
2. 安装 GTM 主节点（initdb → 配置 → 启动 → 注册）
3. 安装 CN/DN 主节点（initdb → 配置 → 启动 → 节点互注册）
4. 创建默认节点组和分片映射

### Step 5：验证

```bash
# 查看集群状态（所有命令都需要 -c）
opentenbase_ctl status -c /tmp/otb_config.ini

# 连接测试（注意 CN 端口是 11003，不是 5432）
export LD_LIBRARY_PATH=/var/lib/opentenbase/install/opentenbase/5.0/lib
psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres -c "SELECT version();"
```

成功标准：
- `status` 显示所有节点 running
- `psql` 能连上并返回版本号

### 后续参数调整

如果后续需要修改配置（换 IP、加节点等）：

```bash
# 1. 修改 INI 配置文件
sudo vi /tmp/otb_config.ini

# 2. 重新安装（会先 delete 旧集群）
sudo -u opentenbase opentenbase_ctl delete -c /tmp/otb_config.ini
sudo -u opentenbase opentenbase_ctl install -c /tmp/otb_config.ini

# 或使用扩容命令（不删除现有数据，也需要 -c）
opentenbase_ctl expand -c /tmp/otb_config.ini
```

---

## 方式三：Docker Compose 部署

适合开发/测试，每个节点一个容器，独立 IP，无端口冲突。

### 前提条件

- Docker 和 Docker Compose 已安装
- 至少 4GB 可用内存
- 中国大陆服务器需配置 Docker 镜像加速：

```bash
sudo mkdir -p /etc/docker
echo '{"registry-mirrors":["https://docker.m.daocloud.io"]}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

### 一键启动

```bash
# 下载并运行部署脚本（自动检测架构，下载 RPM，创建 docker-compose.yml）
curl -sLO https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/docker/test-docker.sh
bash test-docker.sh

# 启动集群（4 个容器：GTM + Coordinator + Datanode1 + Datanode2）
cd /tmp/otb-docker/compose
docker compose up -d --build
```

### 架构

```
Docker Network (172.20.0.0/24)
┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐
│  GTM     │  │  CN       │  │  DN01    │  │  DN02    │
│  172.20  │  │  172.20   │  │  172.20  │  │  172.20  │
│  .0.2    │  │  .0.3     │  │  .0.4    │  │  .0.5    │
│  :6666   │  │  :5432    │  │  :15432  │  │  :15433  │
└──────────┘  └───────────┘  └──────────┘  └──────────┘
              ↑ 对外端口 5432
```

每个容器独立 IP，`forward_port`（6670）和 `pooler_port`（6669）互不冲突。

### 验证连接

```bash
# 从宿主机连接（CN 端口映射到 5432）
psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c "SELECT version();"

# 查看节点拓扑
psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres \
  -c "SELECT node_name, node_type, node_host FROM pgxc_node;"
```

### 集群管理

```bash
cd /tmp/otb-docker/compose

docker compose ps              # 查看容器状态
docker compose logs coordinator # 查看 CN 日志
docker compose down             # 停止并删除容器
docker compose up -d            # 重新启动
docker compose down -v          # 停止并删除数据卷（完全重置）
```

### 自定义节点数量

编辑 `/tmp/otb-docker/compose/docker-compose.yml`，增加 datanode3 服务：

```yaml
  datanode3:
    build:
      context: ../runtime
      dockerfile: Dockerfile.runtime
    image: opentenbase-runtime:latest
    container_name: opentenbase-datanode3
    hostname: datanode3
    security_opt:
      - apparmor:unconfined
    depends_on:
      gtm:
        condition: service_healthy
    environment:
      - NODE_TYPE=datanode
      - NODE_NAME=datanode3
      - GTM_HOST=gtm
      - GTM_PORT=6666
      - COORD_HOST=coordinator
      - COORD_PORT=5432
      - DN_PORT=15434
    ports:
      - "15434:15434"
    volumes:
      - dn3_data:/var/lib/opentenbase/data/datanode3
    networks:
      - opentenbase
```

然后在 `volumes:` 下添加 `dn3_data:`，重新 `docker compose up -d --build`。

### 反馈用户

> OpenTenBase Docker 部署成功！
> - 容器：GTM + Coordinator + 2 Datanode，全部 Up
> - 对外端口：5432（宿主机直接连接）
> - 部署目录：`/tmp/otb-docker/compose`

---

## 安装后目录结构

| 路径 | 用途 |
|------|------|
| `/usr/lib/opentenbase/5.0/bin/opentenbase_ctl` | 官方 C++ 集群管理二进制 |
| `/usr/lib/opentenbase/5.0/bin/` | 其他二进制（postgres, gtm_ctl, initdb, psql 等） |
| `/usr/lib/opentenbase/5.0/lib/` | 运行时库（libpq.so, libpqxx.so 等） |
| `/var/lib/opentenbase/install/opentenbase/5.0/` | **运行时部署目录**（opentenbase_ctl install 后使用） |
| `/etc/opentenbase/5.0/` | 配置文件（含 opentenbase_config.ini.example） |
| `/usr/local/install/opentenbase` | 符号链接 → `/usr/lib/opentenbase/5.0` |
| `/usr/lib/opentenbase/noaffinity.so` | GTM 2核修复 stub（≤2 核自动创建） |
| `/etc/ld.so.preload` | 全局预加载配置（≤2 核自动写入 noaffinity.so） |

---

## 卸载

```bash
# 方式一/二：使用 opentenbase_ctl（所有命令需要 -c）
opentenbase_ctl delete -c /tmp/otb_config.ini

# 然后卸载软件包
sudo apt remove --purge opentenbase   # APT
sudo dnf remove opentenbase            # RPM

# 方式三：Docker
cd /tmp/otb-docker/compose && docker compose down -v
```

卸载前先告知用户会删什么，全量卸载会清数据，让用户确认。

---

## 分布式表操作指南

OpenTenBase 是分布式 HTAP 数据库，建表时必须指定**分发策略**。

| 策略 | 语法 | 适用场景 |
|------|------|---------|
| **SHARD** | `DISTRIBUTE BY SHARD(col)` | 大表、高写入（数据按哈希分布到各 DN） |
| **REPLICATION** | `DISTRIBUTE BY REPLICATION` | 小表、字典表（每 DN 存全量副本） |

```sql
-- 分片表（最常用）
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount DECIMAL(10,2)
) DISTRIBUTE BY SHARD(id) TO GROUP default_group;

-- 复制表
CREATE TABLE regions (
    id INT PRIMARY KEY,
    name VARCHAR(50)
) DISTRIBUTE BY REPLICATION TO GROUP default_group;
```

---

## 已知问题与解决方案

### 1. OSS_INSTALL_DIR 路径不匹配

`opentenbase_ctl` 的 `cluster.h` 硬编码了 `#define OSS_INSTALL_DIR "/usr/local/install/opentenbase"`，但 RPM/DEB 包安装到 `/usr/lib/opentenbase/5.0/`。

**解决**：创建符号链接（一键脚本已自动处理）：

```bash
sudo mkdir -p /usr/local/install
sudo ln -sf /usr/lib/opentenbase/5.0 /usr/local/install/opentenbase
```

### 2. 低核心数（≤2 核）GTM 启动崩溃

GTM 的 `bind_service_threads()` 在 ≤2 核机器上生成空 cpuset，导致 `pthread_setaffinity_np` 返回 EINVAL（`FATAL: binding threads failed`）。

> **重要**：`LD_PRELOAD` 方案无效！`opentenbase_ctl` 通过 SSH 启动 GTM 为独立进程，`LD_PRELOAD` 不会传播到 SSH 子进程。必须使用 `/etc/ld.so.preload` 全局注入。

**解决**：

```bash
# 1. 编译 noaffinity.so（让 pthread_setaffinity_np 变为 no-op）
cat > /tmp/noaffinity.c << 'EOF'
#define _GNU_SOURCE
#include <pthread.h>
int pthread_setaffinity_np(pthread_t t, size_t s, const cpu_set_t *c) { return 0; }
EOF
gcc -shared -fPIC -o /usr/lib/opentenbase/noaffinity.so /tmp/noaffinity.c -lpthread

# 2. 写入 /etc/ld.so.preload（全局注入，所有进程生效，含 SSH 子进程）
echo "/usr/lib/opentenbase/noaffinity.so" > /etc/ld.so.preload
chmod 644 /etc/ld.so.preload
```

一键部署脚本在检测到 CPU ≤2 核时会自动完成上述操作。

### 3. libpqxx.so 运行时缺失

从 v5.0-p30 起已自动捆绑。如仍遇到 `error while loading shared libraries: libpqxx-6.4.so`：

```bash
sudo cp /usr/lib/x86_64-linux-gnu/libpqxx* /usr/lib/opentenbase/5.0/lib/ 2>/dev/null || true
sudo cp /usr/lib64/libpqxx* /usr/lib/opentenbase/5.0/lib/ 2>/dev/null || true
sudo ldconfig
```

---

## 端口参考

| 服务 | 默认端口 | 说明 |
|------|---------|------|
| GTM | 6666 | 全局事务管理器 |
| Coordinator (CN) | **11003** | 客户端连接入口（注意：非 5432！） |
| Datanode (DN) | 15432 | 数据节点 |
| Pooler | 6669 | 连接池（各节点需不同 IP） |
| Forward Manager | 6670 | 查询转发器（各节点需不同 IP） |

> **端口说明**：`opentenbase_ctl` 部署的单节点集群 CN 监听 **11003**。
> Docker Compose 部署的 CN 映射到宿主机 **5432**。
> 连接前请用 `opentenbase_ctl status -c config.ini` 确认端口。

---

## 程序辅助

```bash
python3 {baseDir}/scripts/opentenbase_deploy.py --action check    # 部署前环境检查
python3 {baseDir}/scripts/opentenbase_deploy.py --action status   # 部署后状态验证
```

脚本只做检查与验证，不执行实际安装。

---

## 红线

- **不跳过环境检查直接部署**（尤其内存 < 4GB 必须拦截）
- **不使用 root 作为数据库运行用户**
- **不在未验证（status 全 running + psql 可连）的情况下声明部署成功**
- **部署失败如实告知，不谎报成功**
- **不自动覆盖已有数据目录**，检测到已安装时先询问用户
- **不在 `start/stop/status/delete` 后面漏掉 `-c` 参数**（所有命令都需要）

---

## 必读参考

- 仓库 README：`https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages`
- 上游 opentenbase_ctl 源码：`https://github.com/OpenTenBase/OpenTenBase/tree/v5.0/contrib/opentenbase_ctl`
- 快速开始：仓库 `docs/QUICKSTART.md`
- 部署指南：仓库 `docs/07-deployment.md`
- 故障排除：仓库 `docs/05-troubleshoot.md`
