---
name: opentenbase-deploy
description: 当用户表达"部署 OpenTenBase""装一下 OTB""搭建分布式数据库"等意图时使用。会先检查目标服务器环境，引导用户选择部署方式（AI 定制化包安装 / Docker Compose），完成部署并验证，最后给出连接信息。基于开源仓库 OpenTenBase-Packages。
version: 1.0.0
user-invocable: true
---

# OpenTenBase 部署（引导式）

目标：在目标 Linux 服务器上完成 OpenTenBase 分布式数据库部署，验证可用，并返回连接信息。

把用户当作第一次部署的小白：每一步说清楚在做什么、为什么这么做，关键决策点要主动咨询用户，不要替用户拍板。

---

## 部署源仓库

- 仓库：`https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages.git`
- 维护：CDUESTC 开源社团（blackEvil217 / muzimu217）
- 许可证：Apache 2.0
- 最新版本：`v5.0-p13`（截至 2026-06）
- 支持 15+ 发行版（Ubuntu/Debian/Rocky/AlmaLinux/CentOS Stream/Fedora/openEuler），x86_64 与 aarch64

仓库共提供 **6 种部署方式**，本技能按用户意图聚焦两种主流方式，其余标注定位：

| # | 方式 | 脚本/文件 | 定位 |
|---|------|-----------|------|
| 1 | APT 仓库安装（Ubuntu/Debian） | `scripts/setup-apt.sh` | **AI 定制化安装基础**（推荐） |
| 2 | YUM/DNF 仓库安装（RHEL系） | `scripts/setup-rpm.sh` | **AI 定制化安装基础**（推荐） |
| 3 | 手动下载 DEB/RPM 包安装 | Releases 页 | 备选（离线/特定版本） |
| 4 | 一键交互式部署 | `scripts/setup-cluster.sh` | **不推荐**——由 AI 接管定制化安装，不用黑盒脚本 |
| 5 | Docker Compose 部署 | `docker/test-docker.sh` | **第二种主推方式**（隔离/快速体验） |
| 6 | 源码编译部署 | `docs/source-build-guide.md` | 高级/开发者，可选 |

**默认策略**：不调用仓库的一键脚本 `setup-cluster.sh`。由 AI 检测服务器环境后，选择对应包管理器（APT 或 YUM/DNF）做定制化一体化安装，针对实际环境配置端口、数据目录、内存参数等。

---

## 前置条件

- 目标主机已通过 `linux-ssh-access` 技能完成 SSH 连接（免密已配置）
- 拥有 `sudo` 或 `root` 权限（安装系统包需要）
- 内存 **≥ 4GB**（硬性要求，Coordinator 约需 4GB 共享内存；2GB 服务器无法运行）
- 磁盘 ≥ 10GB（二进制约 500MB + 数据目录）
- 受支持发行版（见上表）

---

## 处理流程

### 阶段一：环境检查（部署前必做）

连接服务器后，**先收集环境信息再决定怎么装**，不要上来就装。逐项检查：

```bash
# 1. 操作系统与版本
cat /etc/os-release | grep -E "^(NAME|VERSION_ID|ID)="

# 2. CPU 架构
uname -m

# 3. 内存（必须 ≥ 4GB）
free -h

# 4. 磁盘可用空间
df -h /

# 5. 当前用户与 sudo 权限
whoami; sudo -n true 2>/dev/null && echo "sudo OK" || echo "sudo 需密码"

# 6. 端口占用（OpenTenBase 默认用 5432 等）
ss -tlnp | grep -E ":(5432|5433|5434|5435)" || echo "端口空闲"

# 7. 是否已安装 opentenbase
which opentenbase-ctl 2>/dev/null && echo "已安装" || echo "未安装"

# 8. Docker 是否可用（影响是否可选 Docker 方式）
which docker 2>/dev/null && docker --version || echo "无 Docker"
```

把检查结果整理给用户，重点说明：

> 📋 服务器环境检查结果：
> - 系统：`Ubuntu 22.04 x86_64`
> - 内存：`8GB`（✅ 满足 ≥4GB 要求）
> - 磁盘：剩余 `40GB`（✅）
> - 端口 5432：空闲（✅）
> - Docker：已安装（✅ 可选 Docker 方式）
> - OpenTenBase：未安装
>
> 这台服务器满足部署条件。

**任何硬性条件不满足时停止**，如实告知用户缺什么，不要强行部署：
- 内存 < 4GB：报告"内存不足，OpenTenBase 至少需要 4GB，无法部署"
- 发行版不在支持矩阵：报告"当前系统不在官方支持列表，可能不兼容"，询问是否仍要尝试
- 端口被占用：报告哪个端口被占，询问是否更换端口或先处理占用进程

### 阶段二：咨询用户选择部署方式

环境检查通过后，主动向用户说明有哪些方式，并给出推荐，让用户拍板：

> 部署 OpenTenBase 有以下几种方式，我按你的服务器环境给出建议：
>
> **方式一：AI 定制化包安装（推荐）**
> 我根据你的系统（Ubuntu 22.04）用 APT 仓库安装，全程由我针对你的环境配置端口、数据目录、内存参数。装完用 `opentenbase-ctl` 管理，最贴合生产/学习用途。
> 适合：长期使用、想直接管理数据库服务。
>
> **方式二：Docker Compose 部署**
> 用容器跑，环境隔离，一键起停，不污染宿主机。你的服务器已装 Docker，可以直接用。
> 适合：快速体验、测试、不想动宿主系统。
>
> **方式三：源码编译部署**
> 从源码编译，最灵活但最耗时，适合开发者定制。
>
> 请问选哪种方式？（回复"1""2"或"3"，推荐"1"）

**注意**：不向用户推荐仓库自带的"一键交互式脚本 `setup-cluster.sh`"。如果用户主动提到要用它，解释："那个脚本是黑盒交互式的，我更建议由我针对你的环境做定制化安装，出了问题我能直接定位。"

根据用户选择进入对应阶段：

---

### 方式一：AI 定制化包安装（推荐路径）

#### 1. 配置软件源

**强制规则：必须使用仓库官方脚本 `setup-apt.sh` / `setup-rpm.sh` 配置源，不要手动写 repo 文件。** 脚本会自动检测发行版、选择最快镜像、导入 GPG key、配置 repo 文件，这是唯一正确的源配置方式。

`setup-rpm.sh` 已支持所有 RHEL 兼容发行版（含 OpenCloudOS、Anolis OS、TencentOS），并带 `ID_LIKE` 兜底机制，无需手动绕过。

根据阶段一检测的发行版类型选择脚本：

**APT 系**（Ubuntu/Debian/Mint/Pop!_OS）：

```bash
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/setup-apt.sh | sudo bash
sudo apt update
```

**RPM 系**（RHEL/Rocky/AlmaLinux/CentOS Stream/Fedora/openEuler/OpenCloudOS/Anolis/TencentOS 等所有 RHEL 兼容发行版）：

```bash
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/setup-rpm.sh | sudo bash
```

脚本执行成功后会输出 "Repository configured" 并提示安装命令。若脚本因网络问题拉取 GPG key 失败，重试一次；仍失败则检查服务器到 `repo.blackevil217.com` 的连通性。

配置源后告知用户："软件源已通过官方脚本配置好，接下来安装 OpenTenBase 服务端和客户端。"

#### 2. 安装软件包

```bash
# APT 系
sudo apt install -y opentenbase

# RPM 系
sudo dnf install -y opentenbase
```

**GPG 签名说明**：仓库的包签名是条件性的——当 CI 配置了 `GPG_PRIVATE_KEY` secret 时包会签名，否则发布的包未签名。如果 `dnf install` 报 GPG 校验失败（`Public key for opentenbase-*.rpm is not installed` 或 `signature could not be verified`），说明当前发布的包未签名，加 `--nogpgcheck` 安装：

```bash
sudo dnf install -y --nogpgcheck opentenbase
```

APT 系同理，若报 `NO_PUBKEY`，在 sources.list 用 `trusted=yes` 或执行 `sudo apt install -y --allow-unauthenticated opentenbase`。

这不是脚本配置问题（`setup-rpm.sh` 正确配置了 `gpgcheck=1` + `gpgkey`），是发布产物本身的签名状态决定的。安装后不影响使用。

`opentenbase` 是元包，会带上 `opentenbase-server` + `opentenbase-client`。

安装后核对版本与安装路径：

```bash
opentenbase-ctl --version
ls -l /usr/lib/opentenbase/ /etc/opentenbase/
```

安装后目录结构：

| 路径 | 用途 |
|------|------|
| `/usr/lib/opentenbase/<version>/` | 二进制和库 |
| `/etc/opentenbase/<version>/` | 配置文件 |
| `/var/lib/opentenbase/<version>/` | 数据目录 |
| `/var/log/opentenbase/<version>/` | 日志 |
| `/etc/opentenbase/current` | 当前版本符号链接 |
| `/usr/bin/opentenbase-ctl` | 集群管理脚本 |

#### 3. 初始化集群（AI 定制，不调用一键脚本）

**不调用 `setup-cluster.sh`**。由 AI 根据环境参数引导初始化。初始化前先确认关键参数，若用户无偏好则用合理默认值并告知用户：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| Coordinator 端口 | `5432` | 对外服务端口 |
| Datanode 端口 | `5433`/`5434` | 数据节点 |
| GTM 端口 | `5435` | 全局事务管理 |
| 数据目录 | `/var/lib/opentenbase/<version>/data` | 可自定义 |
| 运行用户 | `opentenbase`（非 root） | 安装包默认创建 |

向用户确认参数后执行初始化：

```bash
sudo opentenbase-ctl init
```

初始化过程向用户实时说明在做什么（GTM → Coordinator → Datanode 依次拉起）。

#### 4. 启动并验证

```bash
# 启动集群
sudo opentenbase-ctl start

# 查看状态
sudo opentenbase-ctl status
```

连接验证：

```bash
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c "SELECT version();"
```

成功标准：
- `opentenbase-ctl status` 显示 GTM/Coordinator/Datanode 全部 running
- `psql` 能连上并返回版本号

#### 5. 反馈用户

> ✅ OpenTenBase 部署成功！
> - 版本：`v5.0-p13`
> - 部署方式：AI 定制化包安装（APT）
> - 节点状态：GTM / Coordinator / Datanode 全部 running
> - 数据目录：`/var/lib/opentenbase/.../data`
>
> 连接命令（可直接复制使用）：
> ```
> opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres
> ```
>
> 常用管理命令：
> - 启动：`sudo opentenbase-ctl start`
> - 停止：`sudo opentenbase-ctl stop`
> - 状态：`sudo opentenbase-ctl status`
>
> 如果你想让我帮忙建库、建表或做性能调优，随时说。

---

### 方式二：Docker Compose 部署

#### 1. 前置确认

确认 Docker 与 docker compose 可用。中国大陆服务器需先配置 Docker 镜像加速，否则拉镜像会失败：

```bash
docker --version
docker compose version

# 检查是否已配置镜像加速
cat /etc/docker/daemon.json 2>/dev/null || echo "未配置镜像加速"
```

若未配置且服务器在中国大陆，先配置镜像加速并重启 Docker：

```bash
sudo mkdir -p /etc/docker
echo '{"registry-mirrors":["https://docker.m.daocloud.io"]}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

配置前先告知用户："检测到你的服务器在国内，Docker Hub 直接访问会失败，我先帮你配一下镜像加速。"

#### 2. 拉取部署脚本并启动

```bash
# 下载部署脚本
curl -sLO https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/docker/test-docker.sh
bash test-docker.sh

# 启动集群
cd /tmp/otb-docker/compose
docker compose up -d --build
```

#### 3. 验证连接

```bash
cd /tmp/otb-docker/compose
docker compose exec coordinator psql -h 127.0.0.1 -U opentenbase -d postgres -c "SELECT version();"
```

成功标准：容器全部 Up，`psql` 返回版本号。

#### 4. 反馈用户

> ✅ OpenTenBase Docker 部署成功！
> - 版本：`v5.0-p13`
> - 部署方式：Docker Compose
> - 容器状态：全部 Up
> - 部署目录：`/tmp/otb-docker/compose`
>
> 连接命令（可直接复制使用）：
> ```
> cd /tmp/otb-docker/compose && docker compose exec coordinator psql -h 127.0.0.1 -U opentenbase -d postgres
> ```
>
> 常用管理命令：
> - 启动：`cd /tmp/otb-docker/compose && docker compose up -d`
> - 停止：`cd /tmp/otb-docker/compose && docker compose down`
> - 查看日志：`cd /tmp/otb-docker/compose && docker compose logs -f`

---

### 方式三：源码编译部署（高级）

面向开发者。参考仓库 `docs/source-build-guide.md`。此方式耗时长、依赖多，仅当用户明确要求时执行。执行前先向用户说明耗时与依赖风险，并引导查阅源码编译指南。

---

## 卸载

部署失败或用户要求卸载时：

```bash
# 交互式卸载（删除前提示）
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/uninstall.sh | sudo bash

# 全量卸载（含数据和日志，无提示）
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/uninstall.sh | sudo bash -s -- --purge --yes
```

Docker 方式卸载：`cd /tmp/otb-docker/compose && docker compose down -v`

卸载前先告知用户会删什么，全量卸载会清数据，让用户确认。

---

## 程序辅助

当任务可程序化时，使用脚本辅助执行环境检查与状态验证：

```bash
python3 {baseDir}/scripts/opentenbase_deploy.py --action check    # 环境检查
python3 {baseDir}/scripts/opentenbase_deploy.py --action status   # 部署后状态验证
```

不得把脚本报错隐藏成确定结论。脚本不覆盖的场景必须进行人工复核。

---

## 红线

- **不跳过环境检查直接部署**（尤其内存 < 4GB 必须拦截）。
- **不调用仓库一键脚本 `setup-cluster.sh` 做部署**（由 AI 定制化安装替代）。
- 不使用 `root` 作为数据库运行用户。
- 不在未验证（status 全 running + psql 可连）的情况下声明部署成功。
- 部署失败如实告知，不谎报成功。
- 不自动覆盖已有数据目录，检测到已安装时先询问用户是升级还是卸载重装。

---

## 必读参考

- 仓库 README：`https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages`
- 快速开始：`docs/QUICKSTART.md`
- 部署指南：`docs/07-deployment.md`
- 源码编译：`docs/source-build-guide.md`
- 故障排除：`docs/05-troubleshoot.md`
- `{baseDir}/references/README.md`（本地补充资料）
