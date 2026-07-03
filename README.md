# OpenTenBase 运维专家

面向 **QClaw 平台** 的 OpenTenBase 分布式数据库运维专家。目标是让用户通过自然语言完成 OpenTenBase 的部署、连接、集群操作、备份恢复、权限管理、SQL 调优、插件治理、监控接入与日常巡检。

专家采用"总入口路由 + 独立 Skill"的结构：根 `SKILL.md` 负责触发判断、执行铁律和子 Skill 路由；`skills/` 中每个 Skill 负责一类可执行任务，并在各自的 `references/` 中沉淀分布式专业知识。

> 涉及生产环境、数据修改、恢复、权限变更和集群状态变更时，请先核对实际版本、拓扑和命令，再执行操作。

## 项目目标

- 降低 OpenTenBase 的学习和运维门槛。
- 为小白用户提供分步骤、可验证的操作引导。
- 为开发者和 DBA 提供面向分布式场景的诊断与运维流程。
- 避免把 OpenTenBase 简单当作单机 PostgreSQL 使用。
- 将常见操作沉淀为可复用的 Skill，而不是依赖模型临时猜测命令。

## 能力总览

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

其中，`opentenbase-monitoring-integration` 当前主要覆盖二进制部署、CN 指标采集、Prometheus 抓取和 Grafana 基础展示。

## 工作方式

用户提出请求后，专家按以下流程工作：

```text
用户请求
   ↓
根 SKILL.md 判断意图（执行铁律 + 子 Skill 路由表）
   ↓
加载对应 skills/<skill-name>/SKILL.md
   ↓
按需读取 references/ 中的详细知识与操作手册
   ↓
执行前检查 → 展示计划 → 确认后执行 → 验证 → 输出结果
```

示例：

```text
"帮我启动 OpenTenBase 的 CN 节点"        → opentenbase-cluster-ops
"备份 postgres 数据库并验证备份文件"      → opentenbase-backup-restore
"为什么这个用户能连接却查不了表？"        → opentenbase-user-permissions
"帮我分析这条 SQL 为什么访问了全部 DN"    → opentenbase-sql-tuning
```

## 目录结构

```text
OpenTenBase-ops-expert/
├── SKILL.md          # 专家总入口：触发判断、执行铁律、子 Skill 路由
├── README.md         # 项目说明
├── LICENSE           # 开源协议（MIT-0）
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

## Skill 标准结构

```text
skills/<skill-name>/
├── SKILL.md       # 触发场景、处理流程、验证方式和红线
├── references/    # 详细知识、命令说明和操作手册（按需加载）
├── scripts/       # 确定性脚本（可选）
└── assets/        # 配置模板、Dashboard、示例文件等资源（可选）
```

并非每个 Skill 都必须包含全部子目录。

### `SKILL.md`

描述：什么情况下调用、执行前需确认哪些信息、具体处理步骤、哪些操作需用户确认、如何判断成功/失败、哪些行为禁止自动执行。

### `references/`

存放较长的操作手册和分布式知识细节，只有任务需要时才读取，避免把所有内容塞进主 Skill。核心分布式知识分布在：

- `opentenbase-sql-tuning/references/distributed-fundamentals.md` — 架构、分布键、SQL 路由、表类型、执行计划、常见误区
- `opentenbase-backup-restore/references/distributed-backup-principles.md` — 分布式备份恢复原则、备份方式对照、恢复验证清单
- `opentenbase-user-permissions/references/role-permission-principles.md` — 角色权限模型、permission denied 三层排查
- `opentenbase-log-error-analysis/references/distributed-diagnosis-model.md` — 事务/2PC 残留、集群健康分层判断、诊断模型

## 安全与执行原则

- 先识别 OpenTenBase 的实际版本、部署方式和拓扑，不默认所有环境相同。
- 集群生命周期操作优先使用 `opentenbase_ctl` 或 `pgxc_ctl`。
- SQL、备份、权限和插件操作优先使用 OpenTenBase 安装目录中的配套工具。
- 数据库相关命令应以实际运行 OpenTenBase 的系统用户执行，不用 root 跑数据库进程。
- 修改配置、停止集群、恢复数据、回收权限等操作必须先说明影响并获得确认。
- 不直接编辑 OpenTenBase 数据目录，不手工删除 WAL、`base`、`global`、`pg_xact` 等内部文件。
- 命令执行成功不等于任务完成，必须进行进程、端口、SQL、对象或文件级验证。
- 未经实际验证的场景要明确说明，不伪造执行结果。

## 当前限制

- 不同 OpenTenBase 版本的工具、参数和系统表可能存在差异，必须以目标环境为准。
- 部分 Skill 仍以流程和参考文档为主，尚未完全脚本化。
- 监控接入当前主要覆盖 CN 级 PostgreSQL 兼容指标，并不等同于完整的 OpenTenBase 分布式监控平台。
- SQL 调优结论依赖真实 SQL、表结构、分布方式、执行计划和数据规模，缺少证据时不应下确定结论。
- 主备故障切换、在线扩缩容、物理恢复和跨版本迁移属于高风险能力，需要单独验证和授权。
