# 物理备份、PITR 和高风险边界

本文件用于风险判断，不作为自动执行手册。

## 为什么要谨慎

OpenTenBase 是分布式数据库。物理备份和 PITR 不只是复制一个 PostgreSQL 数据目录，还涉及：

- CN、DN、GTM 多角色；
- 多节点时间点一致性；
- WAL 和事务状态；
- 节点拓扑和元数据；
- 主备关系；
- 恢复后路由一致性。

因此，Agent 不应自行设计生产物理恢复流程。

## 可以做的只读检查

```bash
ps -ef | grep -E '[p]ostgres|[g]tm'
ss -lntp 2>/dev/null || ss -lnt 2>/dev/null
```

```sql
SELECT version();
SELECT node_name,node_type,node_host,node_port
FROM pgxc_node
ORDER BY node_name;
```

可以查看配置和目录，但不要修改：

```bash
ls -ld <data_dir>
ls -l <data_dir>/postgresql.conf <data_dir>/PG_VERSION 2>/dev/null || true
```

## 高风险操作

以下操作不得自动执行：

```text
停止集群
复制或覆盖数据目录
删除 pg_wal / pg_xlog
删除 postmaster.pid / gtm.pid
修改 recovery 配置
执行 PITR
替换 CN/DN/GTM 数据目录
清理或重建节点
```

## 什么时候建议人工方案

遇到以下场景，停止并建议人工制定恢复方案：

- 生产库恢复；
- 需要恢复到指定时间点；
- 多 DN 数据不一致；
- GTM 或全局事务状态异常；
- 需要替换物理数据目录；
- 需要跨版本恢复；
- 需要恢复插件 `.so`、control 文件或外部依赖。

## 最低要求

物理恢复方案至少应明确：

```text
备份类型：
备份时间点：
覆盖范围：
CN/DN/GTM 节点清单：
每个节点的数据目录：
WAL 范围：
恢复顺序：
验证步骤：
回退方案：
```

