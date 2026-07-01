# TOOLS.md

## 专业 Skills

| Skill | 用途 | 优先级 |
|-------|------|--------|
| `linux-ssh-access` | 从本地主机通过 SSH 连接 Linux 服务器并执行远程命令 | P0 |
| `opentenbase-deploy` | OpenTenBase 数据库自动化部署，覆盖单机/多机/集群模式 | P0 |
| `opentenbase-cluster-ops` | 集群状态查看、启动、停止和运行验证 | P1 |
| `opentenbase-log-error-analysis` | 日志定位、错误分析、启动和连接故障排查 | P1 |
| `opentenbase-routine-maintenance` | 日常巡检、定期维护、容量和健康检查 | P1 |
| `opentenbase-monitoring-integration` | Prometheus、Grafana、postgres_exporter 监控接入 | P2 |
| `opentenbase-sql-tuning` | 慢 SQL、执行计划解读、分布键选择、跨 DN Join 优化 | P1 |
| `opentenbase-user-permissions` | 用户、角色、Schema、对象权限和默认权限管理 | P2 |
| `opentenbase-backup-restore` | 逻辑备份、恢复演练、备份文件校验 | P2 |
| `opentenbase-plugin-governance` | 插件发现、编译、分发、CREATE EXTENSION 注册 | P3 |

## 本地脚本

- Skill 脚本如存在，位于对应技能的 `scripts/` 目录。
- Skill 参考文档位于对应技能的 `references/` 目录。

Python 脚本建议 Python 3.10 或更高版本，仅依赖标准库。

## 常用工具边界

- 远程连接：`ssh`、`scp`、`sftp`。
- 集群生命周期：`opentenbase_ctl`、`pgxc_ctl`。
- SQL 和元数据检查：OpenTenBase 安装目录下的 `psql`。
- 备份恢复：OpenTenBase 安装目录下的 `pg_dump`、`pg_restore`、`createdb`。
- 插件编译和验证：`plugin_ctl`、`pg_config`、`make`、PGXS。
- 监控接入：`postgres_exporter`、Prometheus、Grafana、`curl`、`systemctl` 或 `nohup`。
- 读取 PDF/Office 文档、网络研究等，调用运行环境已有对应能力。

## 不应使用的方式

- 不直接编辑 OpenTenBase 数据目录。
- 不手工删除 WAL、base、global、pg_xact 等数据库内部目录。
- 不用系统自带 PostgreSQL 工具替代 OpenTenBase 自带工具，除非已经确认版本兼容。
- 不把 `pg_ctl` 当作 OpenTenBase 集群管理入口。

`TOOLS.md` 只记录约定，不赋予工具权限。实际可用性由运行环境配置决定。
