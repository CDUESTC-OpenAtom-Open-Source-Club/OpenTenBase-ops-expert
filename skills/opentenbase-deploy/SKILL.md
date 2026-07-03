---
name: opentenbase-deploy
description: 当用户表达"部署 OpenTenBase""装一下 OTB""搭建分布式数据库"等意图时使用。引导用户选择部署方式（一键自动化部署 / 手动安装 / Docker Compose），支持单节点和多机多节点拓扑，覆盖 2.5 / 2.6 / 5.0 三版本与低内存 DN 扩展，完成部署并验证，最后给出连接信息。基于开源仓库 OpenTenBase-Packages（官方最新 v5.0-p32+），直接引用官方脚本（opentenbase.sh 统一入口，CDN 加速），不维护本地副本。
version: 3.8.0
author: CDUESTC OpenAtom Open Source Club
tools: [shell, filesystem]
user-invocable: true
---

# OpenTenBase 部署（引导式）

目标：在目标 Linux 服务器上完成 OpenTenBase 分布式数据库部署，验证可用，并返回连接信息。

把用户当作第一次部署的小白：每一步说清楚在做什么、为什么这么做，关键决策点要主动咨询用户，不要替用户拍板。

---

## 核心输出规则（部署任务的致命问题）

部署任务评测中最常见的问题是"形式大于内容"——回复很友好但没有可执行方案。

**铁律一：首次回复必须包含可执行的部署命令。**

不管用户是"帮我规划一个 3 节点方案"还是"我这有 3 台机器帮我装"，你的第一次回复必须包含：
- 部署命令（可直接复制粘贴执行）
- 端口号（GTM=6666、CN=11003、DN=15432）
- 数据目录路径
- 验证步骤（如何确认部署成功）

不要回复成"好的，我先帮你分析一下..."然后等用户再追问。直接给方案。

**铁律二：用户已提供的信息不重复追问。**

如果用户说"3 台服务器，IP 是 .10 .11 .12，密码 Admin123"，你不需要再问 IP、密码、服务器数量。直接输出部署命令。

**铁律三：复杂场景首次回复必须给完整拓扑。**

多机多节点部署时，首次回复必须包含：
- 每个节点的角色（GTM/CN/DN）+ IP + 端口 + 数据目录
- 节点间通信端口（pooler=6669，forward=6670）
- GTM Standby 建议（生产环境至少 1 个 GTM 备节点）
- 防火墙开放端口清单

缺少这些就是"拓扑规划严重不足"。

---

## 这个技能能做什么

**一句话**：把一台（或多台）白板 Linux 服务器，变成一个跑起来的 OpenTenBase 分布式数据库集群，并告诉你怎么连、怎么用。

> 【部署完成后】日常运维（启停/状态/监控）→ 见 `opentenbase-cluster-ops` | SQL 调优/慢查询 → `opentenbase-sql-tuning` | 用户权限 → `opentenbase-user-permissions` | 备份恢复 → `opentenbase-backup-restore` | 插件管理 → `opentenbase-plugin-governance`

OpenTenBase 是国产开源**分布式 HTAP 数据库**（基于 PostgreSQL 内核增强）。这个技能帮你完成从 0 到 1 的部署：

| 能力 | 说明 |
|------|------|
| **三种部署方式** | 一键自动化（推荐）/ 手动安装 / Docker Compose，按场景选 |
| **单节点 & 多机多节点** | 学习用单节点（GTM+CN+DN 同机）；生产用多机分布式 |
| **三版本支持** | 2.5 / 2.6（`pgxc_ctl` 链路）/ 5.0（`opentenbase_ctl` 链路，默认推荐） |
| **低内存出路** | 1–2GB 小机器也能当 Datanode 加入现有集群 |
| **环境自检** | 部署前检查内存/磁盘/端口/发行版，主动给推荐而非反问 |
| **分布式表** | 建表时指定 SHARD（分片）/ REPLICATION（复制）分发策略 |
| **部署后验证** | status 全 running + psql 连通 + 分布式表 CRUD，才算成功 |

> **不做什么**：不跳过环境检查、不用 root 跑数据库、不在未验证时谎报成功。详见文末「红线」。

---

## ⚡ 30 秒极速部署（单节点，最常见场景）

> 适用：一台 ≥4GB 内存的 Linux 服务器，想最快跑起来一个单节点集群学习/测试。
> 这是最简单的路径——白板机器，一条命令，全部默认值。

```bash
# 交互式（推荐新手，会问你几个问题，直接回车用默认值）
# CDN 加速路径（推荐，全球加速）
curl -sSL https://repo.blackevil217.com/scripts/opentenbase.sh | sudo bash

# 或 GitHub 直连（备用）
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/opentenbase.sh | sudo bash

# 或非交互式（单节点 127.0.0.1，全自动，CI 用）
curl -sSL https://repo.blackevil217.com/scripts/opentenbase.sh | sudo bash -s -- --yes
```

脚本自动完成：装包 → 建用户 → 配 SSH → 生成 INI → `opentenbase_ctl install` → 启动验证（含 GTM 2核自动修复、主目录权限修复、版本号显式锁定）。

> **CDN 加速**：官方脚本已部署到 Cloudflare CDN（`repo.blackevil217.com/scripts/`），全球加速，国内速度提升约 150-200 倍。脚本自动 CDN 优先，GitHub 回退。
>
> **兼容性提示**：旧脚本 `deploy-opentenbase.sh` 在 2026-06-30 已重命名为 `opentenbase.sh`（单一入口脚本，含 `install`/`uninstall`/`switch`/`status`/`test` 子命令）。`deploy-opentenbase.sh` 作为软链接保留，向下兼容。

部署成功后连接（**5.0 的 CN 端口是 11003，不是 5432**）：

```bash
export LD_LIBRARY_PATH=/var/lib/opentenbase/install/opentenbase/5.0/lib
psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres -c "SELECT version();"
```

> 以下章节是这条命令的展开：多机部署、手动控制、Docker、低内存扩展、版本切换、故障排查。小白照上面三条命令跑通即可；需要定制再往下看。

---

## 部署源仓库

- 仓库：`https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages`
- 维护：CDUESTC 开源社团（blackEvil217 / muzimu217）
- 许可证：Apache 2.0
- **最新版本：`v5.0-p32`**（2026-06-29 release）
  - 核心变更：GTM ≤2核崩溃修复 + `opentenbase_ctl` 全命令 `-c` 规则 + CN 端口定 11003 + 一键脚本端到端验证 + 自动打包 libpqxx/CLI11
  - 参见 commit `70166917`（"GTM 2-core crash + opentenbase_ctl -c param + port 11003 + deploy e2e"）
- **后续更新（2026-07-01）**：
  - 脚本下载改为 CDN 优先（`repo.blackevil217.com/scripts/`），`setup-apt.sh`/`setup-rpm.sh` 同样走 CDN（commit `922ad4a` #46）
  - 安装版本显式锁定：`dnf install opentenbase-<ver>` / `apt install opentenbase=<ver>`（commit `d0a41eb` #52）
  - RPM 回退链：`dnf install` → `dnf --nobest` → `dnf download + rpm -ivh --nodeps`（解决 RHPG 符号依赖问题，commit `3978b4a` #51）
  - 仓库源检测改为 repo 文件存在性检查，规避 OpenCloudOS 等发行版包名大小写干扰（commit `a74e6e8` #50）
  - `pgxc_ctl` 2.5/2.6 修复：`chown -R` 工作目录 + 显式 `--home` 参数（commit `3c4c53a` #53）
  - 版本检测重构：`detect_installed_version()` 通过 rpm -q 或目录扫描，不再依赖 `opentenbase-switch-version`（commit `cc2bbf7` #55）
  - `uninstall`/`switch` 子命令通过 `resolve_script()` 从 CDN 下载 helper 脚本（commit `bb838c9` #56）
  - 验证测试修复：移除 timestamp/now() 列规避 datanode bug，加入 `pgxc_pool_reload` + sleep 2s（commit `6a2e667`/`f754bec`/`a5bd0a7` #41/#42/#43）
- **后续更新（2026-07-01 晚）**：
  - **sshpass 静态二进制**：仓库新增预编译 sshpass 静态二进制（x86_64 + aarch64），Alpine + musl 编译，无动态依赖，跨发行版通用。适合 EulerOS/openEuler、精简容器等包管理器缺 sshpass 的环境（commit `197f2a9`/`0f86e19`/`fd116f8`）
  - **Cloudflare R2 CDN**：sshpass 静态二进制托管至 Cloudflare R2（`pub-eed8815c064447e293145382db9f6b98.r2.dev`），下载速度比 GitHub Raw 快 4 倍（commit `85c219d`）
  - **CI 自动编译**：GitHub Actions workflow 自动编译 sshpass 静态二进制并提交（commit `441192c`/`79b86fe`）
- 双镜像：Cloudflare `repo.blackevil217.com`（主）+ GitHub Pages（备），GPG 指纹 `D8B2E316E1FF88EE178703549D8FA46F3A55D5F0`

### 支持的发行版与架构

**架构**：x86_64 + aarch64（ARM64）。

**官方打包发行版**（p32 release 覆盖）：

| 系 | 发行版 |
|----|--------|
| DEB（amd64+arm64） | Ubuntu 18.04 / 20.04 / 22.04 / 24.04 / 25.04；Debian 10 / 11 / 12 / 13 |
| RPM（x86_64+aarch64） | CentOS Stream 8/9、Rocky 8/9、AlmaLinux 8/9、Fedora 40、openEuler 22.03 |

**setup 脚本额外兜底支持**（通过 `ID_LIKE` 识别）：OpenCloudOS 8/9、Anolis 8/9、TencentOS 2/3 等 RHEL 兼容发行版。

> 共 30 个构建目标，覆盖 15+ 发行版。完整矩阵见仓库 `README_zh.md` 平台表。

## 版本与集群管理工具

当前支持三个版本，分两套控制链路：

| 版本 | 集群管理工具 | 底层工具（内部） | CN 端口 | 说明 |
|------|------------|----------------|---------|------|
| **2.5** | `pgxc_ctl` | `pg_ctl` | 5432 | 旧版 Postgres-XL 链路 |
| **2.6** | `pgxc_ctl` | `pg_ctl` | 5432 | 同上，含功能增强 |
| **5.0** | `opentenbase_ctl` | `pg_ctl` | **11003** | 新版链路，`install`/`delete`/`expand`/`shrink` 需 `-c`，`start`/`stop`/`status` 不需（默认推荐） |

> **核心原则**：用户和自动化脚本 **只与集群管理工具交互**，不直接调用 `pg_ctl`/`initdb`。`pgxc_ctl` 和 `opentenbase_ctl` 各自封装了底层操作（节点注册、GTM 配置、initdb 调用）。

### pgxc_ctl（2.5 / 2.6）

```bash
# 部署集群
pgxc_ctl deploy -c pgxc_ctl.conf

# 初始化节点
pgxc_ctl init -c pgxc_ctl.conf

# 启停/监控
pgxc_ctl start -c pgxc_ctl.conf
pgxc_ctl stop -c pgxc_ctl.conf
pgxc_ctl monitor -c pgxc_ctl.conf

# 查看状态
pgxc_ctl show cluster -c pgxc_ctl.conf
```

配置文件模板：`pgxc_ctl.conf`（含 `GTM_HOST`、`GTM_PORT`、节点拓扑定义）。

> **⚠️ 已知问题**：2.5/2.6 的 `initdb` 在 bootstrap 阶段会执行 `create gtm node` 注册 GTM，但它自身没有 `--gtmhost`/`--gtmport` 参数。**必须通过 `pgxc_ctl deploy` 或 `pgxc_ctl init` 间接调用 initdb**，由 `pgxc_ctl` 通过环境变量传入 GTM 连接信息。直接调用 `initdb` 会导致 `create gtm node (null)` 语法错误，initdb 失败。

### opentenbase_ctl（5.0）

```bash
# install/delete/expand/shrink 带 -c；start/stop/status 不带（install 后集群状态已持久化）
opentenbase_ctl install -c config.ini   # 安装集群（需 -c）
opentenbase_ctl start                   # 启动
opentenbase_ctl stop                    # 停止
opentenbase_ctl status                  # 查看状态
opentenbase_ctl delete -c config.ini    # 删除集群（需 -c）
opentenbase_ctl expand -c config.ini    # 扩容（需 -c）
opentenbase_ctl shrink -c config.ini    # 缩容（需 -c）
```

> **5.0 `-c` 规则**：`install` / `delete` / `expand` / `shrink` 必须带 `-c config.ini`；`start` / `stop` / `status` **不带** `-c`（install 后集群状态已持久化，直接 start/status 即可）。只有 `install` 缺 `-c` 会报 `Failed to extract version from package name`。
> SSH 方式通过 `sshpass` + 密码远程执行（无需密钥互信），在 INI 的 `[server]` 段配置 `ssh-user`/`ssh-password`/`ssh-port`。

---

## 三种部署方式总览

| # | 方式 | 定位 | 适用场景 | 交互 |
|---|------|------|---------|------|
| **1** | **一键自动化部署** | 白板机器→集群运行，一条命令 | **推荐**，生产/学习/快速体验 | 交互式 + 非交互式 |
| **2** | **手动安装** | APT/RPM 装包 + 集群管理工具配置 | 需要精细控制配置的高级用户 | 手动编辑配置 |
| **3** | **Docker Compose** | 容器隔离，每节点独立 IP | 开发/测试/CI/CD | 一键 `docker compose up` |

**默认推荐方式一**。除非用户明确说"我要手动配置"或"用 Docker"，否则直接走一键部署。

> **版本选择**：当前支持 2.5 / 2.6 / 5.0 三个版本。用户可通过 `--version` 参数指定（默认 5.0）。
> 各版本的底层集群管理工具不同：2.5/2.6 用 `pgxc_ctl`，5.0 用 `opentenbase_ctl`。

---

## 部署拓扑说明

OpenTenBase 是分布式数据库，包含三种节点角色：**GTM**（全局事务管理器）、**Coordinator/CN**（协调节点，客户端入口）、**Datanode/DN**（数据节点，存储数据）。

| 拓扑 | 架构 | 适用场景 | 支持状态 |
|------|------|---------|---------|
| **单节点** | GTM + CN + DN 在同一台机器 | 开发测试、学习 | ✅ 支持（`127.0.0.1`） |
| **多机多节点** | GTM / CN / DN 分布在不同服务器 | 生产环境 | ✅ 支持 |
| **Docker 多节点** | 每个节点一个容器，独立 IP | 开发测试 | ✅ 支持 |
| ~~单机多节点~~ | GTM + CN + DN 在同一台物理机 | — | ❌ **不支持** |

> 以上拓扑约束对 **所有版本（2.5 / 2.6 / 5.0）通用**。

### 为什么单机多节点不支持？

CN 和 DN 都有 **forward manager**（查询转发器），默认绑定 `127.0.0.1:6670`。单机部署时 CN 和 DN 共享 IP，第二个节点启动会报 `Address already in use`。

> **替代方案**：想在一台机器上跑多节点，用 **Docker Compose**（方式三），每个容器有独立 IP。

---

## 前置条件

- 拥有 `sudo` 或 `root` 权限
- **内存 ≥ 4GB**（硬性要求，所有部署方式通用）
  - 完整集群（GTM+CN+DN）Coordinator 共享内存需求约 4GB，**无法通过调优降低**；2GB 机器跑完整集群会反复 OOM
  - 1–2GB 的瘦机器**不要硬上完整集群**，可改用「进阶场景 → 低内存 DN 部署」把它作为 Datanode 加入远程集群
- **磁盘：最低 2GB，推荐 10GB+**
- 受支持发行版（见上方「支持的发行版与架构」）
- 多机部署时：各服务器间网络互通，所有节点使用相同的 SSH 用户名和密码
- **OS 内核调优与时间同步**（生产/多机强烈建议）：透明大页(THP)、`kernel.shmmax/shmall`、`ulimit -n/-u`、**NTP 时间同步**等。分布式部署未做这些会踩雷——尤其 **NTP 不同步会导致 GTM 全局时间戳错乱、分布式事务异常**。详见 `references/os-prerequisites.md`（含一键只读体检脚本 + 建议值 + 逐台检查清单）。

---

## 处理流程

### 阶段一：环境检查

连接服务器后，先收集环境信息：

```bash
# 操作系统
cat /etc/os-release | grep -E "^(NAME|VERSION_ID|ID)=" 

# CPU 架构
uname -m

# 内存（完整集群要求 ≥4GB）
free -h

# 磁盘
df -h /

# 端口占用
ss -tlnp | grep -E ":(11003|6666|15432|6669|6670)" || echo "端口空闲"

# Docker
which docker 2>/dev/null && docker --version || echo "无 Docker"
```

也可参考官方仓库的 `scripts/opentenbase.sh` 内置环境检查（一键脚本 Step 1 自动完成）。

**生产/多机部署补充体检**：上面只查内存/磁盘/端口。生产或多机拓扑还需过一遍 OS 内核与时间同步体检——读取 `references/os-prerequisites.md`，跑其中的只读体检脚本，重点确认 **THP 已关闭、`shmmax` 足够、`ulimit` 够高、NTP 已同步**。THP 未关或 NTP 不同步是分布式部署最常见的隐性雷。

**硬性拦截**：
- 内存 < 4GB → 停止部署完整集群，告知"内存不足，建议扩容到 4GB+；若只想加节点可走低内存 DN 方案"
- 端口被占用 → 报告哪个端口被占，询问处理方式

#### 环境评估 → 部署方式推荐

环境检查不是只为了"卡人"，而是要**主动给出推荐**。把收集到的内存 / CPU 核数 / 磁盘 / 是否有 Docker / 服务器数量综合判断，**先给用户一个明确结论**，再让用户确认，而不是上来就问"你想用哪种方式"。

判断逻辑（按优先级，命中即停）：

| 检测结果 | 推荐方式 | 推荐拓扑 | 理由 |
|---------|---------|---------|------|
| 内存 < 4GB | ❌ **不建议部署完整集群** | — | Coordinator 需 ~4GB，硬性要求；引导到低内存 DN 方案或扩容 |
| 内存 ≥ 4GB，**无 Docker** | **方式一 一键部署（推荐）** | 单节点或多机 | 裸机资源利用最充分，生产可用 |
| 内存 ≥ 4GB，**有 Docker**，且用户要测分布式 | **方式三 Docker Compose** | Docker 多节点 | 4 容器模拟真实分片拓扑，互不冲突 |
| 多台服务器（≥3），网络互通 | **方式一 多机多节点** | GTM/CN/DN 分机 | 生产分布式，GTM 单点需独立 |
| 用户明确要精细控制配置 | **方式二 手动安装** | 同上 | 需要逐项调参、定制 INI |

**输出格式**（检查后必须这样汇报给用户）：

```
✅ 环境评估完成
- 操作系统：Ubuntu 22.04 (x86_64)
- 内存：8.0 GB   CPU：4 核   磁盘：50 GB（剩余 38 GB）
- Docker：已安装（24.0）
- 端口：11003/6666/15432/6669/6670 全部空闲

👉 推荐部署方式：方式三 Docker Compose
   理由：内存 ≥4GB 且已装 Docker，4 容器可模拟真实分布式拓扑
   预计内存占用：约 3–4 GB
```

> **铁律**：先报告评估结论 + 推荐，**再**咨询用户是否采用。不要跳过推荐直接问"你选哪种"。用户可选择接受推荐或切换其他方式。

### 阶段二：咨询用户选择版本、部署方式和拓扑

> OpenTenBase 支持三个版本，分两套控制链路：
>
> | 版本 | 控制工具 | 适用场景 |
> |------|---------|---------|
> | **2.5 / 2.6** | `pgxc_ctl` | 旧版兼容、已有 2.x 集群维护 |
> | **5.0**（默认）| `opentenbase_ctl` | 新部署、生产环境推荐 |
>
> 三种部署方式：
>
> **方式一：一键自动化部署（推荐）**
> 白板机器上一条命令搞定，自动装包、配置、安装集群、验证。支持交互式（问你几个问题）和非交互式（全自动）。
>
> **方式二：手动安装**
> 先装软件包，再编辑集群配置文件，最后执行控制命令。适合需要精细控制配置的用户。
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

## 核心脚本：`opentenbase.sh`（统一入口，原 `deploy-opentenbase.sh`）

官方仓库在 2026-06-30 将 19 个脚本整合为单一入口 `opentenbase.sh`，支持子命令：

```bash
# 子命令结构
sudo bash opentenbase.sh install [--yes]        # 安装部署（默认命令）
sudo bash opentenbase.sh uninstall [--purge]    # 卸载
sudo bash opentenbase.sh switch [VERSION]        # 切换版本
sudo bash opentenbase.sh status                  # 查看集群状态
sudo bash opentenbase.sh test [--quick|--full]   # 验证测试

# 向下兼容：旧用法（无子命令）等同于 install
curl -sSL https://repo.blackevil217.com/scripts/opentenbase.sh | sudo bash
curl -sSL https://repo.blackevil217.com/scripts/opentenbase.sh | sudo bash -s -- --yes
```

> **2026-07-01 新增功能**：
> - **CDN 优先**：脚本改为从 `repo.blackevil217.com/scripts/` 下载，CDN 不可用时自动回退 GitHub raw
> - **版本显式锁定**：安装时 pin 版本号（`apt install opentenbase=5.0` / `dnf install opentenbase-5.0`），确保 `--version` 参数生效
> - **RPM 回退链**：`dnf install` → `--nobest` → `dnf download + rpm -ivh --nodeps`，解决非 RHEL 发行版缺少 RHPG 符号依赖的问题
> - **resolve_script()**：`uninstall`/`switch` 子命令在 curl|bash 模式下自动从 CDN 下载 helper 脚本到 `/tmp`
> - **日常运维分离**：安装后提示明确区分日常用 `opentenbase_ctl`/`pgxc_ctl`（随包安装，本地命令无需 curl）和一键脚本

白板机器上一条命令完成全部步骤：安装包 → 创建用户 → 配置 sshpass → 路径符号链接 → 生成 INI → `opentenbase_ctl install -c <config.ini>` → 启动验证。

### 三种使用模式

**模式 A：交互式（推荐新手）**

```bash
# CDN 加速（推荐）
curl -sSL https://repo.blackevil217.com/scripts/opentenbase.sh | sudo bash

# 或 GitHub 直连
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/opentenbase.sh | sudo bash
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
curl -sSL https://repo.blackevil217.com/scripts/opentenbase.sh | sudo bash -s -- --yes
```

零交互，全部使用默认值（单节点 `127.0.0.1`，密码 `opentenbase`）。

**模式 C：非交互式 + 自定义参数（多机多节点）**

```bash
sudo bash opentenbase.sh install --yes \
    --cluster-name prod01 \
    --gtm-ip 192.168.1.10 \
    --cn-ip 192.168.1.11 \
    --dn-ip 192.168.1.12 \
    --ssh-user opentenbase \
    --ssh-password MyPass123 \
    --ssh-port 22
```

### 命令行参数（`install` 子命令）

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
| `--version VER` | OpenTenBase 版本（5.0 / 2.6.0 / 2.5.0） | `5.0` |
| `--skip-install` | 跳过包安装（已装时用） | false |
| `--clean` | 部署前清理旧数据目录 | false |
| `--start` | 安装后自动启动集群（默认启用） | true |
| `--no-start` | 安装后**不**启动集群（只装不启） | false |
| `--help` / `-h` | 显示帮助 | — |

> **版本锁定注意**：安装时会显式锁定版本号（`apt install opentenbase=5.0` / `dnf install opentenbase-5.0`），确保 `--version` 参数正确生效。RPM 安装如遇 `libpq.so.5(RHPG_10)` 符号依赖错误（非 RHEL 发行版），自动降级 `dnf download + rpm -ivh --nodeps`。
>
> **其他子命令参数**：`uninstall` 支持 `--purge`（删除数据和日志）和 `--yes`；`test` 支持 `--quick`（仅连接验证）和 `--full`（完整 CRUD 测试）；`switch` 直接跟版本号如 `5.0`。

### 脚本自动完成的 6 步

1. **环境检查** — root/内存/磁盘/CPU/OS 检测
2. **安装软件包** — 自动检测 APT/RPM，安装 `opentenbase` + `sshpass`
3. **系统准备** — 创建用户 → 设密码 → sudo 免密 → 启动 sshd → 路径符号链接
4. **集群配置** — 交互式收集参数或使用默认值 → 生成 INI 配置（`chmod 600` 保护密码）
5. **安装集群** — `opentenbase_ctl install -c /tmp/opentenbase_config.ini`（含 GTM 2核自动修复）
6. **启动验证** — `opentenbase_ctl status` + psql 连接测试（端口 11003）+ 分布式表 CRUD 测试

> **关于两套部署脚本**：仓库还有另一套 `setup-cluster.sh`（内部下载并执行 `setup-cluster-impl.sh`），用 `opentenbase-ctl`（连字符，仓库自带 shell 包装）+ `opentenbase.conf`，默认 CN 端口 **5432**，内存分级更细（4 级）、有单节点 single 模式。
> **本技能以 `opentenbase.sh` 为主**——它经 p32+ 端到端验证、用上游官方 `opentenbase_ctl` 二进制。若主脚本在特殊环境（极低内存、broken APT 源）受阻，可尝试 `setup-cluster.sh` 作为备用，但注意其 CN 端口是 5432，连接前务必用 `status` 确认。

### 多机多节点部署示例

场景：3 台服务器，GTM 在 .10，CN 在 .11，DN 在 .12。

在任意一台服务器（推荐 GTM 所在机器）执行：

```bash
sudo bash opentenbase.sh install --yes \
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
> **日常运维**（以下工具已随包安装到本机，本地命令无需 curl）：
> - **v5.0**: `opentenbase_ctl status`（状态）/ `start` / `stop` / `expand` / `shrink` / `delete`
> - **v2.5/v2.6**: `pgxc_ctl monitor all` / `start all` / `stop all`（需先 `export PATH`）
> - 一键脚本 `opentenbase.sh` 仅在装/卸/自检时使用
>
> 连接命令：
> ```
> export LD_LIBRARY_PATH=/var/lib/opentenbase/install/opentenbase/5.0/lib
> psql -h <CN_IP> -p 11003 -U opentenbase -d postgres
> ```
>
> 版本差异（`start`/`stop`/`status` 不带 `-c`；`delete`/`expand`/`shrink` 带 `-c`）：
> - `opentenbase_ctl status` — 查看状态
> - `opentenbase_ctl stop` — 停止
> - `opentenbase_ctl start` — 启动
> - `opentenbase_ctl delete -c config.ini` — 删除集群

---

## 方式二：手动安装

适合需要精细控制配置的用户。

> **版本分流**：
> - **2.5 / 2.6**：使用 `pgxc_ctl` 链路。安装包后编辑 `pgxc_ctl.conf`，执行 `pgxc_ctl deploy` 部署集群。
> - **5.0**：使用 `opentenbase_ctl` 链路。安装包后编辑 INI 配置文件，执行 `opentenbase_ctl install -c config.ini`。
>
> 以下以 **5.0** 为例（最常用）。

### Step 1：安装软件包

有三种装包途径，按需选择：

**途径 A：配置官方仓库后用包管理器装**（推荐，自动处理依赖与更新）

> **CDN 加速**：`setup-apt.sh`/`setup-rpm.sh` 现已部署到 CDN，`opentenbase.sh` 安装时自动 CDN 优先、GitHub 回退，并向 setup 脚本传递 `--version` 参数实现多版本仓库选择。

APT 系（Ubuntu/Debian）：

```bash
# CDN 加速（推荐）
curl -sSL https://repo.blackevil217.com/scripts/setup-apt.sh | sudo bash -s -- --version 5.0

# GitHub 直连
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/setup-apt.sh | sudo bash
sudo apt update && sudo apt install -y opentenbase
sudo apt install -y sshpass
```

RPM 系（RHEL/Rocky/Alma/Fedora/openEuler）：

```bash
# CDN 加速（推荐）
curl -sSL https://repo.blackevil217.com/scripts/setup-rpm.sh | sudo bash -s -- --version 5.0

# GitHub 直连
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/setup-rpm.sh | sudo bash
sudo dnf install -y opentenbase
sudo dnf install -y sshpass
```

> `setup-apt.sh` 支持 `--version 5.0|2.6.0|2.5.0` 指定版本（对应仓库 component：main/v2.6/v2.5）；`setup-rpm.sh` 不带版本参数。
> GPG 校验失败时：APT 加 `--allow-unauthenticated`，DNF 加 `--nogpgcheck`。
> **版本锁定注意**：`opentenbase.sh install` 已自动执行版本 pinning（`apt install opentenbase=5.0` / `dnf install opentenbase-5.0`），确保多版本环境下安装指定版本。

**途径 B：用通用安装器 `install.sh`（已合并入 `opentenbase.sh`）**

> **2026-06-30 变更**：官方仓库已将 `install.sh` 删除，功能合并到 `opentenbase.sh`。以下用法供参考，新用户直接使用 `opentenbase.sh install`。

```bash
# 通过 opentenbase.sh 统一入口安装（推荐）
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/opentenbase.sh | sudo bash

# 指定版本
sudo bash opentenbase.sh install --yes --version 5.0   # 或 2.6.0 / 2.5.0

# 旧版 install.sh 用法（仅仓库已有副本可用）：
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/install.sh | sudo bash
sudo bash install.sh --version 2.6.0        # 或 5.0 / 2.5.0 / master / latest
sudo bash install.sh --build-from-source
sudo bash install.sh /path/to/packages/
sudo bash install.sh --force
```

> `install.sh`（旧版）支持多版本 side-by-side 安装，`opentenbase.sh install` 已继承此能力。

**途径 C：手动下载 release 包安装**

```bash
# DEB
wget https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/releases/download/v5.0-p32/opentenbase_5.0-p32_amd64.deb
sudo dpkg -i opentenbase_*.deb && sudo apt-get install -f -y

# RPM
wget https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/releases/download/v5.0-p32/opentenbase-5.0-p32.x86_64.rpm
sudo rpm -ivh opentenbase-*.rpm
```

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
ssh-password=your_password  # SSH 密码（单节点本地部署可省略，多机必填）
ssh-port=22

[log]
level=INFO
```

> **关于 `ssh-password`**：官方单节点模板（`opentenbase_config.ini.example`）**省略**了此字段——因为本地 IP（127.0.0.1）走 `cp` 拷贝不走 SSH。**多机部署必填**，否则远程节点连不上。一键脚本通过 `--ssh-password` 参数自动写入。

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
# 查看集群状态（status 不需要 -c）
opentenbase_ctl status

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
# CDN 加速路径（推荐，GitHub 不可用时自动回退 CDN）
curl -sLO https://repo.blackevil217.com/scripts/test-docker.sh
# GitHub 直连（备用）
# curl -sLO https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/docker/test-docker.sh
bash test-docker.sh

# 启动集群（4 个容器：GTM + Coordinator + Datanode1 + Datanode2）
cd /tmp/otb-docker/compose
docker compose up -d --build
```

> **关于镜像 tag**：`test-docker.sh` 下载的是 multi-arch 的 RPM（来自 `v5.0-multi13` tag），与裸机部署用的 `v5.0-p32` 是**两套 tag 体系**（前者按 CPU 架构打包，后者按 release 迭代）。这是正常的，不影响使用。

### 架构

```
Docker Network (172.20.0.0/24，IP 由 Docker 动态分配)
┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐
│  GTM     │  │  CN       │  │  DN01    │  │  DN02    │
│  :6666   │  │  :5432    │  │  :15432  │  │  :15433  │
└──────────┘  └───────────┘  └──────────┘  └──────────┘
              ↑ 对外端口 5432
```

每个容器独立 IP，`forward_port`（6670）和 `pooler_port`（6669）互不冲突。

> **端口提醒**：Docker 部署下 CN 通过环境变量 `COORD_PORT=5432` 配置并映射到宿主机 **5432**；这与裸机 5.0 的 **11003** 不同。即同一 5.0 版本，**裸机用 11003、Docker 用 5432**——连接前请确认部署方式。

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

> **源码编译 Docker（进阶）**：仓库另有 `docker/cluster/quick-start-source.sh`，在容器内 clone 上游源码并编译运行，端口拓扑不同（CN=15432、库名=`opentenbase`），仅供二次开发使用，日常部署不用。

### 反馈用户

> OpenTenBase Docker 部署成功！
> - 容器：GTM + Coordinator + 2 Datanode，全部 Up
> - 对外端口：5432（宿主机直接连接）
> - 部署目录：`/tmp/otb-docker/compose`

---

## 进阶场景

### 低内存 DN 部署（1–2GB 服务器当数据节点）

场景：手里有一台 1–2GB 内存的小机器（常见国产云低配机），跑不了完整集群，但想把它作为 **Datanode** 加入一个已有的远程集群。

仓库提供专用脚本 `deploy-lowmem-datanode.sh`（位于 `scripts/extras/`）：自动建 1GB swap、只起 DN 进程、直连远程 GTM，内存占用约 **400–600MB**。

```bash
# 在低内存机器上执行（--gtm-ip 必填，指向已有集群的 GTM）
# CDN 加速（推荐）
curl -sSL https://repo.blackevil217.com/scripts/extras/deploy-lowmem-datanode.sh | sudo bash -s -- --gtm-ip 192.168.1.10
# GitHub 直连（备用）
# curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/extras/deploy-lowmem-datanode.sh | sudo bash -s -- --gtm-ip 192.168.1.10

# 完整参数
sudo bash extras/deploy-lowmem-datanode.sh \
    --gtm-ip 192.168.1.10 \
    --gtm-port 6666 \
    --dn-name dn2 \
    --dn-port 15432 \
    --version 5.0
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--gtm-ip IP` | 远程 GTM 的 IP | **必填** |
| `--gtm-port PORT` | GTM 端口 | `6666` |
| `--dn-name NAME` | 本 Datanode 名称 | `dn1` |
| `--dn-port PORT` | 本 Datanode 端口 | `15432` |
| `--version VER` | OpenTenBase 版本 | `5.0` |

> 该脚本直接用 `initdb` + `pg_ctl` 启动 DN（不走 opentenbase_ctl），适合 5.0；加入后需在 CN 侧用 `CREATE NODE` / `ALTER NODE` 注册该 DN 并重分布数据。

### 多版本切换（side-by-side）

场景：同一台机器上用 `install.sh` 装了多个版本（如 5.0 和 2.6.0），想在它们之间切换。

`install.sh` 安装时会部署 `opentenbase-switch-version` 命令，操作 `/etc/opentenbase/current` 符号链接：

```bash
# 列出已安装版本并显示当前激活版本
opentenbase-switch-version

# 切换到指定版本（需 root）
sudo opentenbase-switch-version 5.0       # 或 2.6.0 / 2.5.0
```

> 切换的是默认版本符号链接（`/usr/bin/*`、`/etc/opentenbase/current`），不影响已运行的集群进程；切换后新起的会话/命令使用新版本。

---

## 安装后目录结构

| 路径 | 用途 |
|------|------|
| `/usr/lib/opentenbase/5.0/bin/opentenbase_ctl` | 官方 C++ 集群管理二进制 |
| `/usr/lib/opentenbase/5.0/bin/` | 其他二进制（postgres, gtm_ctl, initdb, psql 等） |
| `/usr/lib/opentenbase/5.0/lib/` | 运行时库（libpq.so, libpqxx.so 等，当前版本已捆绑） |
| `/var/lib/opentenbase/install/opentenbase/5.0/` | **运行时部署目录**（opentenbase_ctl install 后使用） |
| `/etc/opentenbase/5.0/` | 配置文件（含 opentenbase_config.ini.example） |
| `/usr/local/install/opentenbase` | 符号链接 → `/usr/lib/opentenbase/5.0` |
| `/usr/lib/opentenbase/noaffinity.so` | GTM 2核修复 stub（≤2 核自动创建） |
| `/etc/ld.so.preload` | 全局预加载配置（≤2 核自动写入 noaffinity.so） |

---

## 卸载

```bash
# 方式一/二：使用 opentenbase_ctl（delete 需要 -c）
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

### 0. 当前多版本自动化结论

- **2.5 / 2.6 正式链路**：必须固定为 `pgxc_ctl deploy` / `pgxc_ctl init`，不能把后台启动后强杀控制器的临时办法当成成功交付。
- **5.0 正式链路**：必须固定为 `opentenbase_ctl ... -c config.ini`（p32 已端到端验证）。
- **Docker 正式链路**：必须采用多容器、独立 IP 的 Compose 架构；单容器伪多节点仅适合临时排障，不作为交付方案。
- 参考文档见 `{baseDir}/references/README.md`（索引）及各专题文档。

### 1. OSS_INSTALL_DIR 路径不匹配

`opentenbase_ctl` 的 `cluster.h` 硬编码了 `#define OSS_INSTALL_DIR "/usr/local/install/opentenbase"`，但 RPM/DEB 包安装到 `/usr/lib/opentenbase/5.0/`。

**解决**：创建符号链接（一键脚本已自动处理）：

```bash
sudo mkdir -p /usr/local/install
sudo ln -sf /usr/lib/opentenbase/5.0 /usr/local/install/opentenbase
```

### 1.5. 用户主目录归属错误（opentenbase.sh #39 修复）

软件包安装后 `opentenbase` 用户主目录可能归属 `root`，导致 `ssh-keygen` 失败、SSH 连接异常。

**解决**（`opentenbase.sh install` 已自动修复）：

```bash
SSH_USER_HOME=$(getent passwd opentenbase | cut -d: -f6)
chown -R opentenbase:opentenbase "$SSH_USER_HOME"
chmod 750 "$SSH_USER_HOME"
chmod 700 "$SSH_USER_HOME/.ssh"
```

### 2. 低核心数（≤2 核）GTM 启动崩溃

GTM 的 `bind_service_threads()` 在 ≤2 核机器上生成空 cpuset，导致 `pthread_setaffinity_np` 返回 EINVAL（`FATAL: binding threads failed`）。

> **为什么必须用全局注入**：`opentenbase_ctl` 通过 SSH 启动 GTM 为独立进程，`LD_PRELOAD` **不会传播到 SSH 子进程**（p32 commit `70166917` 实测确认）。因此**必须**用 `/etc/ld.so.preload` 全局注入；同时建议叠加 `LD_PRELOAD` 双保险（脚本两者都做）。

**解决**（一键脚本在 CPU ≤2 核时自动完成）：

```bash
# 1. 编译 noaffinity.so（让 pthread_setaffinity_np 变为 no-op）
cat > /tmp/noaffinity.c << 'EOF'
#define _GNU_SOURCE
#include <pthread.h>
int pthread_setaffinity_np(pthread_t t, size_t s, const cpu_set_t *c) { return 0; }
EOF
gcc -shared -fPIC -o /usr/lib/opentenbase/noaffinity.so /tmp/noaffinity.c -lpthread

# 2. 写入 /etc/ld.so.preload（全局注入，所有进程生效，含 SSH 子进程——这一步是关键）
echo "/usr/lib/opentenbase/noaffinity.so" > /etc/ld.so.preload
chmod 644 /etc/ld.so.preload
```

### 3. libpqxx.so 运行时缺失

**当前版本（p31/p32）已将 libpqxx/CLI11 打包进 `/usr/lib/opentenbase/5.0/lib/`**，正常无需手动处理。如遇旧包仍报 `error while loading shared libraries: libpqxx-6.4.so`：

```bash
sudo cp /usr/lib/x86_64-linux-gnu/libpqxx* /usr/lib/opentenbase/5.0/lib/ 2>/dev/null || true
sudo cp /usr/lib64/libpqxx* /usr/lib/opentenbase/5.0/lib/ 2>/dev/null || true
sudo ldconfig
```

### 4. 2.5/2.6 initdb create gtm node (null) 语法错误（版本缺陷）

**仅 2.5 / 2.6 受影响**。5.0 无此问题（5.0 的 initdb 可直接调用并支持 `--master_gtm_nodename/ip/port`）。

**现象**：直接调用 `initdb` 初始化 coordinator 或 datanode 时，bootstrap 阶段报错退出：

```
FATAL:  syntax error at or near "(" at character 17
STATEMENT:  create gtm node (null) with (type='gtm', host='(null)',port=(null), primary=1);
```

**根因**：2.5/2.6 的 `initdb` 在 bootstrap SQL 中强制注册 GTM 节点，但它自身没有 `--gtmhost`/`--gtmport` 参数。当环境变量 `master_gtm_ip`、`master_gtm_port`、`master_gtm_nodename` 未设置时，值默认为 `(null)`，生成非法 SQL。

**解决**：**必须通过 `pgxc_ctl deploy` 或 `pgxc_ctl init` 调用 initdb**，由 `pgxc_ctl` 负责传入 GTM 连接信息。禁止直接调用 `initdb`。

```bash
# ✅ 正确
pgxc_ctl deploy -c pgxc_ctl.conf

# ❌ 错误 — 会触发 (null) bug
initdb --nodename=coord1 --nodetype=coordinator -D /data/coord
```

### 5. 2.5/2.6 pgxc_ctl 权限和 --home 参数问题（#53 修复）

**仅 2.5 / 2.6 受影响**。`pgxc_ctl init all` 可能因两个问题失败：

1. **工作目录权限**：`/var/lib/opentenbase/pgxc_ctl` 由 root 创建，但 `pgxc_ctl` 以 `opentenbase` 用户运行，首次运行时在其中安装驱动脚本和日志目录时报 `Permission denied`。
2. **缺少 --home 参数**：`pgxc_ctl` 未指定 `--home` 时从 `~/pgxc_ctl` 寻找配置和驱动脚本，而非生成的工作目录。

**解决**（`opentenbase.sh install` 在 2026-07-01 已修复）：

```bash
# 工作目录归属修复
sudo chown -R opentenbase:opentenbase /var/lib/opentenbase/pgxc_ctl

# 正确调用方式
su - opentenbase -c "pgxc_ctl --home /var/lib/opentenbase/pgxc_ctl --configuration /var/lib/opentenbase/pgxc_ctl/pgxc_ctl.conf init all"
```

---

## 端口参考

| 服务 | 2.5 / 2.6 | 5.0（裸机） | 5.0（Docker） | 说明 |
|------|-----------|-----|-----|------|
| GTM | 6666 | 6666 | 6666 | 全局事务管理器 |
| Coordinator (CN) | **5432** | **11003** | **5432** | 客户端连接入口（版本/部署方式不同，端口不同！） |
| Datanode (DN) | 15432 | 15432 | 15432/15433 | 数据节点（Docker 下多 DN 递增） |
| Pooler | 6669 | 6669 | 6669 | 连接池（各节点需不同 IP） |
| Forward Manager | 6670 | 6670 | 6670 | 查询转发器（各节点需不同 IP） |

> **端口速记**：
> - 2.5/2.6 单节点 CN = **5432**
> - 5.0 裸机（opentenbase_ctl 部署）CN = **11003**
> - 5.0 Docker Compose CN 映射宿主 = **5432**
> - 连接前请用集群管理工具确认端口：`pgxc_ctl monitor`（2.5/2.6）或 `opentenbase_ctl status`（5.0）

---

## 官方脚本索引

OpenTenBase-Packages 官方仓库提供了以下脚本，本技能直接引用，无需本地维护副本：

> **2026-06-30 重构**：原 `deploy-opentenbase.sh` 和 `install.sh` 已合并为统一入口 `opentenbase.sh`（支持 `install`/`uninstall`/`switch`/`status`/`test` 子命令）。`deploy-opentenbase.sh` 作为软链接保留，向下兼容。`install.sh` 已删除，功能由 `opentenbase.sh install` 替代。

| 脚本 | 用途 | 调用方式 |
|------|------|---------|
| `opentenbase.sh` | **统一管理脚本**（安装/卸载/切换/状态/测试） | `curl ... \| sudo bash` 或 `sudo bash opentenbase.sh [command]` |
| `setup-apt.sh` | 配置 APT 仓库 | `curl ... \| sudo bash` |
| `setup-rpm.sh` | 配置 RPM 仓库 | `curl ... \| sudo bash` |
| `uninstall.sh` | 卸载（含 `--purge` 全量清理） | `curl ... \| sudo bash`（或 `opentenbase.sh uninstall`，CDN 自动 resolve） |
| `switch-version.sh` | 版本切换 | 通常通过 `opentenbase.sh switch` 调用（CDN 自动 resolve） |
| `extras/deploy-lowmem-datanode.sh` | 低内存 DN 部署 | `curl ... \| sudo bash`（旧路径保留软链接） |
| `test-docker.sh` | Docker Compose 部署 | `curl -sLO && bash`（位置：`docker/test-docker.sh`） |

---

## 使用示例

**示例 1：白板机器快速部署**

> 用户：帮我在 192.168.1.10 上装一个 OpenTenBase
>
> Agent：先帮你检查环境。请确认我通过 SSH 连接这台服务器？
>
> （连接后）
> Agent：✅ 环境评估完成 — Ubuntu 22.04，8GB 内存，4 核，30GB 磁盘。推荐一键部署（单节点 v5.0）。现在开始部署吗？
>
> 用户：开始
>
> Agent：（执行 `curl -sSL https://repo.blackevil217.com/scripts/opentenbase.sh | sudo bash`）
> ✅ 部署成功！连接命令：`psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres`

**示例 2：多机分布式部署**

> 用户：3 台服务器，GTM 在 .10，CN 在 .11，DN 在 .12，部署 v5.0
>
> Agent：好的。确认三台服务器都已安装 opentenbase 软件包、opentenbase 用户密码一致、防火墙已开放 6666/11003/15432 端口？密码是什么？
>
> 用户：密码都是 Admin123，端口已开
>
> Agent：（执行自动化多机部署命令）✅ 部署成功！

---

## 红线

- **不跳过环境检查直接部署**（内存 < 4GB 必须拦截，引导低内存 DN 方案或扩容）
- **不使用 root 作为数据库运行用户**
- **不在未验证（status 全 running + psql 可连）的情况下声明部署成功**
- **部署失败如实告知，不谎报成功**
- **不自动覆盖已有数据目录**，检测到已安装时先询问用户
- **`install`/`delete`/`expand`/`shrink` 必须带 `-c`；`start`/`stop`/`status` 不带**（5.0：install 后集群状态已持久化，只有处理拓扑的命令才需 `-c`）
- **2.5/2.6 禁止直接调用 `initdb`**，必须通过 `pgxc_ctl deploy` 间接调用（否则 `create gtm node (null)` bug）
- **版本混淆**：2.5/2.6 用 `pgxc_ctl`，5.0 用 `opentenbase_ctl`，工具不能混用
- **端口混淆**：2.5/2.6 与 5.0-Docker 的 CN 是 **5432**，5.0 裸机的 CN 是 **11003**，连接前务必确认
- **依赖缺失不自创依赖**：服务器缺少前置依赖时（如 sshpass、libpqxx、CLI11 等），不自创依赖代码。优先下载对应发行版的二进制安装包（`.deb`/`.rpm`）；二进制包不可用时，下载该依赖的官方源码编译安装。禁止自行编写一个"替代品"来绕过缺失的依赖。例外：GTM ≤2 核崩溃修复用的 `noaffinity.so` 是系统调用拦截桩，不属于依赖替代，不受此限

---

## 必读参考

- 仓库 README：`https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages`
- 最新 release：`https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/releases/tag/v5.0-p32`
- 近期变更：
  - 2026-06-30：脚本整合为 `opentenbase.sh` 统一入口（commit `14a8bd4` #39），管道修复（commit `cfe12ec` #40），CLI 文档和版本控制路径（commit `5ba0ae2` #36/#44）
  - 2026-07-01：CDN 优先脚本下载（commit `922ad4a` #46），版本显式锁定 + 卸载元包修复（commit `d0a41eb` #52），RPM `--nodeps` 回退（commit `3978b4a` #51），repo 检测改为文件存在性检查（commit `a74e6e8` #50），pgxc_ctl `--home` 修复（commit `3c4c53a` #53），版本检测重构（commit `cc2bbf7` #55），resolve_script() CDN 回退（commit `bb838c9` #56），测试验证修复（commit `6a2e667`/`f754bec`/`a5bd0a7` #41/#42/#43）
- 上游 opentenbase_ctl 源码：`https://github.com/OpenTenBase/OpenTenBase/tree/v5.0/contrib/opentenbase_ctl`
- 快速开始：仓库 `docs/01-quickstart.md`、`docs/QUICKSTART.md`
- 部署指南：仓库 `docs/07-deployment.md`
- 故障排除：仓库 `docs/05-troubleshoot.md`
