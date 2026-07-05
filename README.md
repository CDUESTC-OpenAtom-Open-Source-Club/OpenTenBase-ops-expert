# OpenTenBase 部署与运维专家

OpenTenBase 分布式数据库的高可用部署、运维诊断与调优知识库。

## 能力矩阵

| 场景 | 对应内容 |
|------|----------|
| **部署** | 单节点/多节点/Docker Compose 部署、环境检查、配置参考、版本切换 |
| **集群运维** | pgxc_ctl 管理、启停控制、配置修改、扩缩容规划 |
| **备份恢复** | 逻辑备份、物理备份、PITR、备份校验、恢复验证 |
| **SQL 调优** | 执行计划分析、分布键优化、跨 DN Join 诊断、统计信息与索引 |
| **权限管理** | 用户/角色管理、Schema 权限、默认权限、审计配置 |
| **监控接入** | Prometheus + Grafana + postgres_exporter 集成 |
| **日志分析** | 错误定位、分布式故障诊断模型、数据损坏与 XID 处理 |
| **插件治理** | C/SQL 插件全生命周期管理 |
| **日常巡检** | 健康检查清单、阈值告警、巡检报告模板 |
| **SSH 连接** | 远程服务器连接与命令执行 |

## 目录结构

```
skills/
├── opentenbase-deploy/               # 部署（核心）
│   ├── SKILL.md
│   └── references/
│       ├── deploy-multi-node.md      # 多节点部署
│       ├── install-and-deploy-single-node.md  # 单节点部署
│       ├── deploy-docker-compose.md  # Docker Compose 部署
│       ├── one-click-install.md      # 一键安装
│       ├── config-reference.md       # 配置参考
│       ├── cluster-management.md     # 集群管理
│       ├── troubleshooting.md        # 部署排障
│       ├── version-switch.md         # 版本切换
│       └── memory-tuning.md          # 内存调优
├── opentenbase-cluster-ops/          # 集群运维
├── opentenbase-backup-restore/       # 备份恢复
├── opentenbase-sql-tuning/           # SQL 调优
├── opentenbase-user-permissions/     # 权限管理
├── opentenbase-monitoring-integration/ # 监控接入
├── opentenbase-log-error-analysis/   # 日志分析
├── opentenbase-plugin-governance/    # 插件治理
├── opentenbase-routine-maintenance/  # 日常巡检
└── linux-ssh-access/                 # SSH 连接（辅助）
    ├── SKILL.md
    └── scripts/ssh_connect.py
```

## 使用方式

每个 skill 下：
- **SKILL.md** — 场景触发条件 + 执行流程 + 可执行命令 + 验证方法
- **references/** — 详细操作手册与配置参考

执行原则：
1. 先确认环境（版本、拓扑、部署方式），不默认所有环境相同
2. 每条命令附带验证方法（进程、端口、SQL 查询、文件校验）
3. 修改配置、停集群、恢复数据等操作必须先说明影响并确认
4. 不自发创建与当前任务无关的文件
