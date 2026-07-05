# 恢复演练与验证

恢复验证比“备份命令成功”更重要。

## 恢复前确认

```text
目标库是否存在：
目标库是否为空：
是否允许写入：
是否会覆盖对象：
是否需要角色和权限：
是否需要 extension 文件：
是否需要 plugin_ctl 分发插件：
```

若目标库不是空库，停止并让用户确认。

## 基础验证

```sql
SELECT 1;
SELECT version();

SELECT node_name,node_type,node_host,node_port
FROM pgxc_node
ORDER BY node_name;
```

## 对象验证

```sql
SELECT nspname
FROM pg_namespace
WHERE nspname NOT LIKE 'pg_%'
  AND nspname <> 'information_schema'
ORDER BY nspname;

SELECT extname, extversion
FROM pg_extension
ORDER BY extname;

SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog','information_schema')
ORDER BY schemaname, tablename;
```

## 行数抽查

对关键表执行：

```sql
SELECT count(*) FROM <schema>.<table>;
```

如果源库仍可读，用一次查询比较所有表行数：

```sql
SELECT 'table1' AS tbl, count(*) FROM <schema>.table1
UNION ALL SELECT 'table2', count(*) FROM <schema>.table2
UNION ALL SELECT 'table3', count(*) FROM <schema>.table3
ORDER BY tbl;
```

源库和恢复库分别执行后逐行核对。这是最可靠的验证方法。

## 已知可忽略的恢复告警

`pg_restore` 恢复时出现以下告警通常可安全忽略：

```text
WARNING:  schema "opentenbase_ora" already exists, skipping
WARNING:  extension "opentenbase_plpgsql" already exists, skipping
WARNING:  function ... already exists, skipping
WARNING:  type ... already exists, skipping
```

这些是 OpenTenBase 内建的 `opentenbase_ora` 兼容 schema 和 `opentenbase_plpgsql` 扩展对象。恢复时目标库已存在它们，`pg_restore` 跳过不覆盖，不影响业务数据。

⚠️ 如果涉及自定义 extension（如 `pgcrypto`、`postgis` 等），需要在恢复前先 `CREATE EXTENSION` 安装依赖对象，否则恢复会报错。

## 权限验证

用目标业务用户连接测试：

```sql
SELECT current_user, current_database();
SELECT has_schema_privilege(current_user, '<schema>', 'USAGE');
SELECT has_table_privilege(current_user, '<schema>.<table>', 'SELECT');
```

## 业务验证

至少执行一条只读业务 SQL。不要用“对象存在”代替业务可用性。

## 结果分类

```text
恢复已验证：基础连接、对象、关键行数和业务 SQL 均通过。
恢复部分验证：只验证了对象或连接，缺少业务校验。
恢复失败：恢复命令失败或关键对象缺失。
恢复未验证：只完成备份，没有恢复演练。
```

