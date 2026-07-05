# 执行计划分析

## 首选只读计划

```sql
EXPLAIN (VERBOSE, COSTS)
<SQL>;
```

`EXPLAIN` 不执行 SQL，适合默认使用。

## 谨慎使用 EXPLAIN ANALYZE

`EXPLAIN ANALYZE` 会真实执行 SQL：

```sql
EXPLAIN (ANALYZE, VERBOSE, BUFFERS)
<SELECT SQL>;
```

只在用户确认后用于只读 `SELECT`。不要对写 SQL 自动执行。

## 需要关注的计划信号

普通 PostgreSQL 视角：

- Seq Scan / Index Scan / Bitmap Scan
- Nested Loop / Hash Join / Merge Join
- Sort / Aggregate / Materialize
- 估算行数和实际行数差异

OpenTenBase 分布式视角：

- SQL 是否下推到 DN；
- 是否访问全部 DN；
- 是否出现远程执行节点；
- 是否广播小表；
- 是否发生数据重分布；
- Join 是否能在 DN 本地完成；
- CN 是否承担大量排序、聚合或结果汇总。

## 分析步骤

1. 确认 SQL 是 OLTP 点查、范围查、Join、聚合还是批量写。
2. 找出主表和过滤条件。
3. 判断过滤条件是否包含分布键等值条件。
4. 判断 Join 两边是否按相同分布键关联。
5. 判断估算行数是否明显偏离直觉。
6. 再考虑索引、统计信息和 SQL 改写。

## 输出不要过度承诺

没有 `EXPLAIN ANALYZE`、表数据量、索引和统计信息时，只能给“初步判断”，不能断言真实瓶颈。

