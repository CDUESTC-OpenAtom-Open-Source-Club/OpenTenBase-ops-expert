# OpenTenBase 部署与运维专家

一个面向 **QClaw 工作区** 的 OpenTenBase 专家 Agent 项目，目标是让用户通过自然语言完成 OpenTenBase 的部署、连接、集群操作、备份恢复、权限管理、SQL 调优、插件治理、监控接入与日常巡检。

项目采用"长期记忆 + 任务路由 + 独立 Skill"的结构：顶层文件负责专家身份、行为规则和长期知识，`skills/` 中的每个 Skill 负责一类可执行任务。

> 当前项目仍在持续迭代。涉及生产环境、数据修改、恢复、权限变更和集群状态变更时，请先核对实际版本、拓扑和命令，再执行操作。

## 项目目标

- 降低 OpenTenBase 的学习和运维门槛。
- 为小白用户提供分步骤、可验证的操作引导。
- 为开发者和 DBA 提供面向分布式场景的诊断与运维流程。
- 避免把 OpenTenBase 简单当作单机 PostgreSQL 使用。
- 将常见操作沉淀为可复用的 Skill，而不是依赖模型临时猜测命令。

## 当前能力

| Skill | 主要功能 |
|---|---|
| `linux-ssh-access` | 连接 Linux 服务器、执行远程命令、配置免密登录 |
| `opentenbase-deploy` | OpenTenBase 部署、环境检查、拓扑选择和部署后验证 |
| `opentenbase-cluster-ops` | 查看状态，启动、停止和验证 OpenTenBase 集群或节点 |
| `opentenbase-backup-restore` | 逻辑备份、恢复计划、备份校验和恢复验证 |
| `opentenbase-user-permissions` | 用户、角色、Schema、对象权限和默认权限管理 |
| `opentenbase-sql-tuning` | 慢 SQL、执行计划、分布键、跨 DN Join、索引和统计信息分析 |
| `opentenbase-plugin-governance` | 插件发现、构建、分发、注册、检查和回滚 |
| `opentenbase-monitoring-integration` | Prometheus、Grafana、postgres_exporter 监控接入 |
| `opentenbase-log-error-analysis` | 日志定位、错误提取、启动与连接问题分析 |
| `opentenbase-routine-maintenance` | 日常巡检、周期任务设计、资源检查和巡检报告 |

其中，`opentenbase-monitoring-integration` 当前为第一版，主要覆盖二进制部署、CN 指标采集、Prometheus 抓取和 Grafana 基础展示。

## 工作方式

用户提出请求后，Agent 按以下流程工作：

```text
用户请求
   ↓
AGENTS.md 判断任务类型
   ↓
加载对应 skills/<skill-name>/SKILL.md
   ↓
按需读取 references/ 中的详细说明
   ↓
必要时调用 scripts/ 中的确定性脚本
   ↓
执行前检查 → 展示计划 → 执行 → 验证 → 输出结果
```

示例：

```text
"帮我启动 OpenTenBase 的 CN 节点"
→ opentenbase-cluster-ops

"备份 postgres 数据库并验证备份文件"
→ opentenbase-backup-restore

"为什么这个用户能连接数据库却查不了表？"
→ opentenbase-user-permissions

"帮我分析这条 SQL 为什么访问了全部 DN"
→ opentenbase-sql-tuning
```

## 目录结构

```text
workspace/
├── README.md                   # 项目说明
├── SKILL.md                    # 专家入口 Skill（路由表 + 执行原则）
├── AGENTS.md                   # 三条铁律 + 任务路由速查
├── SOUL.md                     # 专家性格、表达方式和行为边界（静态）
├── USER.md                     # 用户信息（静态）
├── IDENTITY.md                 # 专家名称、定位和 Vibe（静态）
├── TOOLS.md                    # Skill、工具及使用边界（静态）
├── MEMORY.md                   # OpenTenBase 核心知识库（静态参考）
├── LICENSE                     # MIT-0 许可证
├── _meta.json                  # 专家包元数据
├── CHANGELOG.md                # 版本变更记录
└── skills/
    ├── linux-ssh-access/
    ├── opentenbase-deploy/
    ├── opentenbase-cluster-ops/
    ├── opentenbase-backup-restore/
    ├── opentenbase-user-permissions/
    ├── opentenbase-sql-tuning/
    ├── opentenbase-plugin-governance/
    ├── opentenbase-monitoring-integration/
    ├── opentenbase-log-error-analysis/
    └── opentenbase-routine-maintenance/
```

## 顶层文件说明

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 专家入口，路由表 + 执行原则 + 使用示例 |
| `AGENTS.md` | 三条铁律 + 任务路由速查 |
| `SOUL.md` | 规定语气、个性、教学方式和安全边界（静态，运行时不读取） |
| `USER.md` | 用户身份、称呼、环境和表达偏好（静态，运行时不读取） |
| `IDENTITY.md` | 专家的身份卡片（静态，运行时不读取） |
| `TOOLS.md` | 记录已有 Skill、命令行工具和使用限制（静态，运行时不读取） |
| `MEMORY.md` | OpenTenBase 核心知识库（静态参考，按需查阅） |

## Skill 标准结构

```text
skills/<skill-name>/
├── SKILL.md       # 触发场景、处理流程、验证方式和红线
├── references/    # 详细知识、命令说明和操作手册
├── scripts/       # Python、Shell 等确定性脚本
└── assets/        # 配置模板、Dashboard、示例文件等资源
```

并非每个 Skill 都必须包含全部子目录。

### `SKILL.md`

负责描述：

- 什么情况下应调用这个 Skill；
- 执行前需要确认哪些信息；
- 具体处理步骤；
- 哪些操作需要用户确认；
- 如何判断成功或失败；
- 哪些行为禁止自动执行。

### `references/`

存放较长的操作手册和知识细节。只有任务需要时才读取，避免把所有内容都塞进主 Skill。

### `scripts/`

存放适合程序化的步骤，例如 SSH 连接、环境检查和结果解析。脚本用于降低模型临时拼接命令造成的错误。

### `assets/`

存放配置模板、监控面板、示例文件等不适合写入 Markdown 的资源。

## 快速开始

### 1. 准备工作区

下载或克隆本项目，将项目目录作为 QClaw 的 Agent 工作区使用。

```bash
git clone https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-ops-expert.git
cd OpenTenBase-ops-expert
```

也可以直接解压项目压缩包后导入工作区。

### 2. 完善用户与环境信息

首次使用前可根据实际情况检查：

```text
USER.md      用户称呼、身份和偏好
TOOLS.md     本地工具、主机别名和环境说明
MEMORY.md    长期有效的 OpenTenBase 知识
```

每日记忆文件由运行过程按需要生成或更新，不必提前为每一天手工创建。

### 3. 检查依赖

不同 Skill 使用的依赖不同，常见依赖包括：

```text
ssh / scp / sftp
Python 3
OpenTenBase 自带的 psql、pg_dump、pg_restore、createdb
opentenbase_ctl 或 pgxc_ctl
curl、wget、tar、systemctl 等 Linux 工具
```

部分运行环境可能需要额外 Python 包或系统工具；具体以对应 Skill 的说明为准。监控、插件和部署 Skill 会使用各自声明的外部工具。

### 4. 开始使用

可以直接用自然语言提出任务：

```text
连接 192.168.1.20 这台 Linux 虚拟机。

查看 OpenTenBase 集群状态，并启动停止的节点。

备份 testdb 数据库，只备份结构，并验证备份文件。

创建一个只能查询 app schema 的只读用户。

分析这条 SQL 的执行计划，重点看是否访问了全部 DN。

查看当前集群已经安装了哪些 extension。

为现有 OpenTenBase CN 接入 Prometheus 和 Grafana。
```

## Memory 与 Skill 的分工

`MEMORY.md` 保存长期有效的认知，例如：

- CN、DN、GTM 的职责；
- 分布键、分片、分区和 Group 的区别；
- SQL 路由和跨节点执行的基本原则；
- 权限、备份和分布式事务的判断原则；
- 已确认的用户环境和关键决策。

Skill 不重复编写完整知识百科，而应重点描述：

- 用户何时会需要这项能力；
- 需要收集哪些参数；
- 应执行哪些操作；
- 执行前后如何验证；
- 哪些操作需要确认或禁止自动执行。

## 安全与执行原则

- 先识别 OpenTenBase 的实际版本、部署方式和拓扑，不默认所有环境相同。
- 集群生命周期操作优先使用 `opentenbase_ctl` 或 `pgxc_ctl`。
- SQL、备份、权限和插件操作优先使用 OpenTenBase 安装目录中的配套工具。
- 数据库相关命令应以实际运行 OpenTenBase 的系统用户执行。
- 修改配置、停止集群、恢复数据、回收权限等操作必须先说明影响并获得确认。
- 不直接编辑 OpenTenBase 数据目录，不手工删除 WAL、`base`、`global`、`pg_xact` 等内部文件。
- 命令执行成功不等于任务完成，必须进行进程、端口、SQL、对象或文件级验证。
- 未经实际验证的场景要明确说明，不伪造执行结果。

## 扩展新的 Skill

项目保留了 `skills/example-skill/` 作为模板。

新增 Skill 时建议：

1. 复制 `example-skill` 并重命名目录；
2. 修改 `SKILL.md` 中的名称、描述、触发条件和流程；
3. 将长篇说明拆到 `references/`；
4. 将可重复、可解析的操作写入 `scripts/`；
5. 在 `AGENTS.md` 中增加任务路由；
6. 在 `TOOLS.md` 中登记 Skill 和依赖；
7. 使用真实环境验证成功路径和失败路径。

一个好的 Skill 应具备明确的输入、稳定的执行步骤、可判断的结果和清晰的安全边界。

## 当前限制

- 不同 OpenTenBase 版本的工具、参数和系统表可能存在差异，必须以目标环境为准。
- 部分 Skill 仍以流程和参考文档为主，尚未完全脚本化。
- 监控接入当前主要覆盖 CN 级 PostgreSQL 兼容指标，并不等同于完整的 OpenTenBase 分布式监控平台。
- SQL 调优结论依赖真实 SQL、表结构、分布方式、执行计划和数据规模，缺少证据时不应下确定结论。
- 主备故障切换、在线扩缩容、物理恢复和跨版本迁移属于高风险能力，需要单独验证和授权。

## 项目状态

该项目处于持续开发阶段。当前重点是提高 Skill 的可执行性、验证能力和 OpenTenBase 分布式场景适配度。

欢迎基于真实部署、运维和教学案例继续补充 Skill、脚本、参考资料与测试记录。
