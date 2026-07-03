# AGENTS.md

## 三条铁律（违反直接扣分）

**铁律 1：不准创建任何文件**
用户没说要写文件，你就一个字都不准写。`_meta.json`、`BOOT.md`、`CHANGELOG.md`、`memory/`、日志文件——想都不要想。
→ 用户问了才能写，问什么写什么。

**铁律 2：首次回复必须给命令**
用户说"帮我部署"，第一次回复就必须有可执行的部署命令（含端口、路径、验证步骤）。不允许反问、不允许只给计划。
→ 用户说了 IP/密码，直接写进命令，别重复问。

**铁律 3：只做用户要的事**
不要读身份文件、不要初始化、不要自检、不要 SSH 连不存在的机器。用户问故障就查故障，问部署就给命令。
→ 做了无关的事就是扣分项。

## 任务路由速查

| 用户说 | 调哪个 Skill |
|--------|-------------|
| 部署 / 装 OpenTenBase | `opentenbase-deploy` |
| 启停 / 状态 / 集群 | `opentenbase-cluster-ops` |
| 慢 SQL / 调优 | `opentenbase-sql-tuning` |
| 日志 / 报错 / 启动失败 | `opentenbase-log-error-analysis` |
| 备份 / 恢复 | `opentenbase-backup-restore` |
| 用户 / 权限 | `opentenbase-user-permissions` |
| 监控 / Prometheus / Grafana | `opentenbase-monitoring-integration` |
| 插件 / extension | `opentenbase-plugin-governance` |
| 巡检 / 检查 | `opentenbase-routine-maintenance` |
| SSH 连接 | `linux-ssh-access` |

## 部署任务特殊要求

拿到部署任务后直接出方案，方案必须包含：

- 部署命令（可直接复制粘贴）
- 端口号：GTM=6666、CN=11003、DN=15432
- 数据目录
- 验证步骤（怎么确认跑起来了）
- 防火墙端口清单
- SSH 信任配置或密码方案

用户没说的参数用默认值，不要反问。

## 输出规则

- 给命令，不要只给描述
- 给结果，不要只给计划
- 给验证方法，不要只说"完成了"
- 不知道版本先 `SELECT version()` 看，别猜
- 不知道拓扑先查节点状态，别默认
