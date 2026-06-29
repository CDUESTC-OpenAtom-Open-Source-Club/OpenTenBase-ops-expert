# 分布式诊断

## 查看节点拓扑

```sql
SELECT node_name,node_type,node_host,node_port
FROM pgxc_node
ORDER BY node_name;
```

一个 CN 可连接不代表所有 DN 都健康。调优时至少知道有几个 CN、几个 DN。

## 查看表分布元数据

优先从建表 SQL、业务文档或 `\d+ <table>` 获取分布方式。

不同 OpenTenBase 版本的 `pgxc_class` 字段可能不同。先查看当前字段：

```sql
SELECT attnum, attname, format_type(atttypid, atttypmod)
FROM pg_attribute
WHERE attrelid = 'pgxc_class'::regclass
  AND attnum > 0
  AND NOT attisdropped
ORDER BY attnum;
```

在已验证的 OpenTenBase_v5.21.8.11 环境中，可用字段包括 `pclocatortype`、`discolnums`、`nodeoids`。可尝试：

```sql
SELECT c.relname,
       xc.pclocatortype,
       xc.discolnums,
       xc.nodeoids
FROM pg_class c
JOIN pgxc_class xc ON xc.pcrelid = c.oid
WHERE c.relname = '<table_name>';
```

如果查询结果为空，通常表示当前数据库没有该表的分布元数据、表名/schema 不匹配，或当前库没有用户分布表；这不是 SQL 执行失败。

无法确认字段含义时，不要编造分布键；回到建表 SQL、`\d+` 输出或用户提供的设计说明。

## 常见表类型

```text
分布表：数据按分布键或分布规则放到不同 DN。
复制表：各相关 DN 保存完整副本，适合小字典表。
分区分布表：同时存在分区和分布，需要分别分析。
```

## 分布键判断

好的分布键通常满足：

- 经常出现在过滤条件；
- 经常作为大表 Join 键；
- 值分布足够均匀；
- 能减少跨 DN 访问；
- 与事务边界接近。

主键不一定是最佳分布键。

## Join 判断

优先级：

```text
同分布键本地 Join > 小表复制/广播 Join > 数据重分布 Join > CN 集中 Join
```

两个大表 Join 如果分布键不同，可能出现跨 DN 数据重分布，成本很高。

## 数据倾斜排查

只读思路：

```text
1. 看分布键是否低基数或热点明显。
2. 看各 DN 表大小、行数或执行时间是否差异很大。
3. 看计划中是否某个节点耗时异常。
```

不要直接改分布键。改变分布方式通常是高风险表结构变更，需要迁移方案。

## 常见建议

- 点查 SQL 尽量带分布键等值条件。
- 大表 Join 尽量使用相同分布键。
- 小维表可考虑复制表，但高频更新大表不适合复制。
- 跨 DN 大聚合应关注 CN 汇总压力。
- 分布键倾斜时，优先验证数据分布，不直接改表。
