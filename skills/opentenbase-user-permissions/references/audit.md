# 权限只读审计

本文件只包含只读查询。不要在审计阶段执行写 SQL。

## 连接和基础信息

```sql
SELECT version();
SELECT current_user, current_database();
SELECT node_name,node_type,node_host,node_port
FROM pgxc_node
ORDER BY node_name;
```

## 角色属性

```sql
SELECT rolname,
       rolcanlogin,
       rolsuper,
       rolcreatedb,
       rolcreaterole,
       rolreplication,
       rolbypassrls
FROM pg_roles
ORDER BY rolname;
```

判断：

- `rolcanlogin = true` 才能直接登录。
- `rolsuper = true` 是最高风险权限。
- `rolcreaterole = true` 可继续授予或管理角色，通常不应给普通业务账号。

## 角色成员关系

```sql
SELECT member.rolname AS member,
       parent.rolname AS inherited_role,
       m.admin_option
FROM pg_auth_members m
JOIN pg_roles member ON member.oid = m.member
JOIN pg_roles parent ON parent.oid = m.roleid
ORDER BY member.rolname, parent.rolname;
```

权限可能来自成员关系，不一定直接出现在目标用户上。

## 数据库权限

```sql
SELECT datname,
       pg_get_userbyid(datdba) AS owner,
       datacl
FROM pg_database
ORDER BY datname;
```

检查目标用户是否能连接目标数据库：

```sql
SELECT has_database_privilege('<role>', '<database>', 'CONNECT') AS can_connect;
```

## Schema 权限

```sql
SELECT nspname,
       pg_get_userbyid(nspowner) AS owner,
       nspacl
FROM pg_namespace
WHERE nspname NOT LIKE 'pg_%'
  AND nspname <> 'information_schema'
ORDER BY nspname;
```

检查目标用户是否能使用 Schema：

```sql
SELECT has_schema_privilege('<role>', '<schema>', 'USAGE') AS can_use_schema,
       has_schema_privilege('<role>', '<schema>', 'CREATE') AS can_create_in_schema;
```

常见误区：有表权限但没有 Schema `USAGE`，仍然可能访问失败。

## 表和视图权限

```sql
SELECT table_schema,
       table_name,
       privilege_type
FROM information_schema.role_table_grants
WHERE grantee = '<role>'
  AND table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name, privilege_type;
```

如果排查系统视图权限，再去掉 `table_schema` 过滤；普通业务权限审计默认过滤系统 schema，避免噪声。

检查单个对象：

```sql
SELECT has_table_privilege('<role>', '<schema>.<table>', 'SELECT') AS can_select,
       has_table_privilege('<role>', '<schema>.<table>', 'INSERT') AS can_insert,
       has_table_privilege('<role>', '<schema>.<table>', 'UPDATE') AS can_update,
       has_table_privilege('<role>', '<schema>.<table>', 'DELETE') AS can_delete;
```

## 序列权限

```sql
SELECT sequence_schema,
       sequence_name
FROM information_schema.sequences
ORDER BY sequence_schema, sequence_name;
```

检查：

```sql
SELECT has_sequence_privilege('<role>', '<schema>.<sequence>', 'USAGE') AS can_use,
       has_sequence_privilege('<role>', '<schema>.<sequence>', 'SELECT') AS can_select,
       has_sequence_privilege('<role>', '<schema>.<sequence>', 'UPDATE') AS can_update;
```

常见误区：表有 `INSERT`，但自增序列没有 `USAGE`，插入仍可能失败。

## 函数权限

```sql
SELECT routine_schema,
       routine_name,
       routine_type
FROM information_schema.routines
WHERE routine_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY routine_schema, routine_name;
```

检查：

```sql
SELECT has_function_privilege('<role>', '<schema>.<function_signature>', 'EXECUTE') AS can_execute;
```

函数签名需要包含参数类型，例如 `public.f(integer,text)`。

## 默认权限

```sql
SELECT defaclrole::regrole::text AS owner_role,
       defaclnamespace::regnamespace::text AS schema_name,
       defaclobjtype,
       defaclacl
FROM pg_default_acl
ORDER BY owner_role, schema_name, defaclobjtype;
```

默认权限只影响未来创建的对象，不会自动修复已有对象权限。

## search_path

```sql
SHOW search_path;
SELECT rolname, rolconfig
FROM pg_roles
WHERE rolconfig IS NOT NULL
ORDER BY rolname;
```

`search_path` 只影响对象查找，不等于授权。
