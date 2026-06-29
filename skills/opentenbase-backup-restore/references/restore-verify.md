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

如果源库仍可读，比较源库和恢复库的关键表行数。

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

