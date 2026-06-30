---
name: opentenbase-sql-tuning
description: 分析和优化 OpenTenBase SQL 性能。适用于慢 SQL、执行计划解读、分布键选择、跨 DN Join、广播/重分布、数据倾斜、索引和统计信息排查。默认只读分析，避免把 OpenTenBase 当单机 PostgreSQL 调优。
---

# OpenTenBase SQL 调优

若目标数据库在远程 Linux，先使用 `linux-ssh-access`。若集群状态不确定，先使用 `opentenbase-cluster-ops` 只读确认 CN/DN/GTM 可用。

本 Skill 负责 SQL 性能分析和调优建议，不负责集群启停、用户授权、备份恢复或插件治理。

## 运行用户

执行 `psql`、查看工具或读取 OpenTenBase 环境前，先确认 OpenTenBase 运行用户。不要在 root 下直接判断工具是否存在。

若用户只提供 root 账号，先询问 OpenTenBase 运行用户，并请求允许：

```bash
su - <opentenbase_user>
```

## 基本原则

- 默认只读分析，不直接改 SQL、索引、统计信息或参数。
- 应用通常连接 CN；分析计划时必须关注 SQL 是否被下推到 DN、是否广播、是否重分布、是否集中到 CN。
- 不要只按单机 PostgreSQL 思路看索引和扫描方式；同时检查分布方式、分布键、Join 键、数据倾斜和跨节点事务。
- `EXPLAIN` 可默认使用；`EXPLAIN ANALYZE` 会真实执行 SQL，必须先确认 SQL 类型和影响。
- 对 `INSERT/UPDATE/DELETE/MERGE/DDL` 不自动执行 `EXPLAIN ANALYZE`。

## 选择 reference

- 看执行计划：读取 `references/explain-plan.md`。
- 判断分布键、广播、重分布、数据倾斜：读取 `references/distribution-diagnosis.md`。
- 检查索引、统计信息、VACUUM/ANALYZE：读取 `references/statistics-indexes.md`。
- 涉及 `postgresql.conf`、`postgresql.auto.conf` 或数据库参数变更建议：读取 `references/parameter-change.md`。
- 给用户输出完整调优结论：读取 `references/tuning-report.md`。

## 标准流程

### 1. 收集上下文

先问清或读取：

```text
慢 SQL
数据库名
连接 CN
表结构
表分布方式
数据量级
是否允许执行 EXPLAIN ANALYZE
是否允许建索引或 ANALYZE
```

### 2. 确认环境

```sql
SELECT version();
SELECT node_name,node_type,node_host,node_port
FROM pgxc_node
ORDER BY node_name;
```

### 3. 只读执行计划

```sql
EXPLAIN (VERBOSE, COSTS)
<SQL>;
```

不要先跑 `EXPLAIN ANALYZE`。

### 4. 分布式判断

重点判断：

```text
是否能按分布键路由到少量 DN
是否访问全部 DN
是否有广播
是否有数据重分布
Join 是否本地化
CN 是否承担大量汇总或排序
是否存在数据倾斜
```

### 5. 给出建议

建议按优先级输出：

```text
1. SQL 改写
2. 分布键或表类型调整
3. 索引建议
4. 统计信息建议
5. 参数或资源建议
6. 需要进一步验证的证据
```

涉及写操作时，只给计划，等待用户确认。

## 禁止自动执行

未经确认，不执行：

```text
CREATE INDEX
DROP INDEX
ANALYZE
VACUUM
ALTER TABLE
ALTER SYSTEM
SET GLOBAL
EXPLAIN ANALYZE 写 SQL
任何 INSERT/UPDATE/DELETE/MERGE/DDL
```

## 回复格式

```text
SQL 调优结论：可优化 / 证据不足 / 风险较高
连接入口：<CN host:port/database>
主要瓶颈：<分布键 / 广播 / 重分布 / 索引 / 统计信息 / CN 汇总 / 数据倾斜 / 其他>
证据：<执行计划或只读查询摘要>
建议：<按优先级列出>
需要确认：<是否允许 EXPLAIN ANALYZE / ANALYZE / 建索引 / 改表>
```
