# 统计信息与索引

## 索引不是分布键替代品

索引解决单节点访问效率，分布键解决数据路由和跨节点代价。慢 SQL 可能同时需要索引和分布方式调整。

## 查看索引

```sql
SELECT schemaname,
       tablename,
       indexname,
       indexdef
FROM pg_indexes
WHERE schemaname = '<schema>'
  AND tablename = '<table>'
ORDER BY indexname;
```

## 查看表大小

```sql
SELECT relnamespace::regnamespace::text AS schema_name,
       relname,
       pg_size_pretty(pg_total_relation_size(oid)) AS total_size
FROM pg_class
WHERE relname = '<table>'
ORDER BY pg_total_relation_size(oid) DESC;
```

## 查看统计信息

```sql
SELECT schemaname,
       tablename,
       attname,
       n_distinct,
       most_common_vals,
       most_common_freqs
FROM pg_stats
WHERE schemaname = '<schema>'
  AND tablename = '<table>'
ORDER BY attname;
```

判断：

- `n_distinct` 很小的列通常不适合作大表分布键；
- `most_common_freqs` 中某个值占比很高，可能倾斜；
- 估算行数偏差大时，统计信息可能过旧或不足。

## ANALYZE 边界

`ANALYZE` 会更新统计信息，是写元数据操作。不要自动执行。

需要执行时先展示：

```sql
ANALYZE <schema>.<table>;
```

并说明：

- 影响统计信息；
- 可能消耗资源；
- 高峰期谨慎执行；
- 执行后应重新 `EXPLAIN`。

## 建索引边界

创建索引是写操作，可能消耗大量 IO、锁和空间。不要自动执行。

给建议时使用计划形式：

```sql
CREATE INDEX CONCURRENTLY <index_name>
ON <schema>.<table> (<columns>);
```

如果当前版本不支持或不适合 `CONCURRENTLY`，按实际版本调整。

索引建议必须说明：

- 支持哪个查询条件或 Join；
- 是否包含分布键；
- 是否会增加写入成本；
- 是否可能与已有索引重复。

