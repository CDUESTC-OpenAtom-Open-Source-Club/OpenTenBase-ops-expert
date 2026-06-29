# TOOLS.md

## 专业 Skills

| Skill | 用途 | 优先级 |
|-------|------|--------|
| `linux-ssh-access` | 从本地主机通过 SSH 连接 Linux 服务器并执行远程命令 | P0 |
| `opentenbase-deploy` | OpenTenBase 数据库自动化部署，覆盖单机/多机/集群模式 | P0 |
| `opentenbase-cluster-ops` | 集群状态查看、启动、停止和运行验证 | P1 |
| `opentenbase-sql-tuning` | 慢 SQL、执行计划解读、分布键选择、跨 DN Join 优化 | P1 |
| `opentenbase-user-permissions` | 用户、角色、Schema、对象权限和默认权限管理 | P2 |
| `opentenbase-backup-restore` | 逻辑备份、恢复演练、备份文件校验 | P2 |
| `opentenbase-plugin-governance` | 插件发现、编译、分发、CREATE EXTENSION 注册 | P3 |

## 本地脚本

- Skill 脚本路径：`skills/{{skill-name}}/scripts/{{script-name}}.py`

Python 脚本建议 Python 3.10 或更高版本，仅依赖标准库。

## 通用能力协作

- 读取 PDF/Office 文档：调用环境已有对应 Skill
- 网络研究：调用 Web/Browser 能力，优先使用权威来源
- 数据库操作：通过已部署集群的 psql 或对应 Skill 执行
- 其他外部工具：通过环境集成调用

`TOOLS.md` 只记录约定，不赋予工具权限。实际可用性由运行环境配置决定。
