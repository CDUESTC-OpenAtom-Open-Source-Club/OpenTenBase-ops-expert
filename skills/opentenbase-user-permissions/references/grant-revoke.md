# 授权、回收和用户变更

本文件包含写操作模板。执行前必须先向用户展示计划并获得确认。

## 创建登录用户

优先创建普通登录用户，不授予高风险属性：

```sql
CREATE ROLE <user_name> LOGIN PASSWORD '<temporary_password>';
```

如需要密码过期或限制，请按当前版本能力确认后再加。

## 创建权限组

推荐用“用户 + 权限组”分离：

```sql
CREATE ROLE <app_readonly_role>;
GRANT <app_readonly_role> TO <user_name>;
```

业务权限授给权限组，用户只加入权限组。

## 数据库连接权限

```sql
GRANT CONNECT ON DATABASE <database> TO <role>;
```

回滚：

```sql
REVOKE CONNECT ON DATABASE <database> FROM <role>;
```

## Schema 权限

使用已有对象前通常需要：

```sql
GRANT USAGE ON SCHEMA <schema> TO <role>;
```

允许创建对象时才授予：

```sql
GRANT CREATE ON SCHEMA <schema> TO <role>;
```

回滚：

```sql
REVOKE CREATE ON SCHEMA <schema> FROM <role>;
REVOKE USAGE ON SCHEMA <schema> FROM <role>;
```

## 表权限

只读：

```sql
GRANT SELECT ON ALL TABLES IN SCHEMA <schema> TO <role>;
```

读写：

```sql
GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA <schema>
TO <role>;
```

回滚：

```sql
REVOKE SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA <schema>
FROM <role>;
```

## 序列权限

插入自增列常需要：

```sql
GRANT USAGE, SELECT
ON ALL SEQUENCES IN SCHEMA <schema>
TO <role>;
```

回滚：

```sql
REVOKE USAGE, SELECT
ON ALL SEQUENCES IN SCHEMA <schema>
FROM <role>;
```

## 函数执行权限

```sql
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA <schema> TO <role>;
```

回滚：

```sql
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA <schema> FROM <role>;
```

## 默认权限

默认权限影响未来对象。必须以“未来对象的创建者”身份执行，或明确指定 `FOR ROLE`：

```sql
ALTER DEFAULT PRIVILEGES FOR ROLE <object_owner> IN SCHEMA <schema>
GRANT SELECT ON TABLES TO <role>;
```

读写示例：

```sql
ALTER DEFAULT PRIVILEGES FOR ROLE <object_owner> IN SCHEMA <schema>
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO <role>;

ALTER DEFAULT PRIVILEGES FOR ROLE <object_owner> IN SCHEMA <schema>
GRANT USAGE, SELECT ON SEQUENCES TO <role>;

ALTER DEFAULT PRIVILEGES FOR ROLE <object_owner> IN SCHEMA <schema>
GRANT EXECUTE ON FUNCTIONS TO <role>;
```

默认权限不影响已有对象。已有对象仍需单独 `GRANT ON ALL ...`。

## 高风险操作

以下操作默认不执行，除非用户明确要求并二次确认：

```sql
ALTER ROLE <role> SUPERUSER;
ALTER ROLE <role> CREATEROLE;
ALTER ROLE <role> CREATEDB;
ALTER ROLE <role> REPLICATION;
DROP ROLE <role>;
DROP OWNED BY <role>;
REASSIGN OWNED BY <old_role> TO <new_role>;
```

删除用户前必须检查：

```sql
SELECT nspname AS schema_name
FROM pg_namespace
WHERE nspowner = '<role>'::regrole;

SELECT relnamespace::regnamespace::text AS schema_name,
       relname,
       relkind
FROM pg_class
WHERE relowner = '<role>'::regrole
ORDER BY schema_name, relname;
```

有对象归属时，先让用户选择 `REASSIGN OWNED` 或迁移方案，不自动删除。

