---
name: opentenbase-user-permissions
description: 管理 OpenTenBase 的用户、角色、Schema、对象权限和默认权限。适用于只读权限审计、解释权限问题、生成授权或回收计划，以及在用户明确确认后执行 GRANT、REVOKE、CREATE ROLE、ALTER ROLE 等权限操作。
version: 1.0.0
author: CDUESTC OpenAtom Open Source Club
tools: [shell, filesystem]
user-invocable: true
---

# OpenTenBase 用户与权限运维

若数据库位于远程 Linux，先使用 `linux-ssh-access`。若需要确认集群是否可用，可先使用 `opentenbase-cluster-ops` 做只读状态检查。

本 Skill 只处理数据库用户、角色、权限、Schema 和对象授权，不负责集群启停、安装、备份恢复或 SQL 性能调优。

## 运行用户

执行 `psql` 前，先确认 OpenTenBase 运行用户。不要在 root 下直接判断 `psql` 是否可用。

若用户只提供 root 账号，先询问 OpenTenBase 运行用户，并请求允许：

```bash
su - <opentenbase_user>
```

若用户提供的是普通 Linux 用户，也要确认它是否具备连接目标 CN 的环境和权限。

## 基本原则

- 默认先做只读审计，不修改数据库。
- 普通业务用户和权限应通过 CN 统一管理，不直接在 DN 上修改。
- 不能只看 `\du` 判断权限；同时检查角色属性、成员关系、数据库权限、Schema 权限、对象权限、默认权限和 `search_path`。
- `superuser`、`CREATEROLE`、`CREATEDB`、`REPLICATION`、`BYPASSRLS` 属于高风险属性，不能随手授予。
- 执行任何写操作前，先展示 SQL 计划、影响对象、回滚方式和风险，并获得用户确认。

## 选择 reference

- 只读审计、排查“能否登录/能否访问对象”：读取 `references/audit.md`。
- 需要创建用户、角色、授权或回收权限：读取 `references/grant-revoke.md`。
- 需要解释 PostgreSQL/OpenTenBase 角色模型：读取 `references/role-model.md`。
- 涉及登录来源、认证方式、`pg_hba.conf` 或 `pg_ident.conf`：读取 `references/auth-config.md`。

## 标准流程

### 1. 确认连接入口

连接 CN，不连接 DN 作为普通权限管理入口：

```bash
PGCONNECT_TIMEOUT=5 psql -X -w -h <cn_host> -p <cn_port> \
  -U <admin_user> -d <database>
```

先确认版本和拓扑：

```sql
SELECT version();
SELECT node_name,node_type,node_host,node_port
FROM pgxc_node
ORDER BY node_name;
```

### 2. 只读审计

先读取 `references/audit.md`，检查：

- 角色属性
- 角色成员关系
- 数据库 owner 和 ACL
- Schema owner 和 ACL
- 表、视图、序列、函数权限
- 默认权限
- `search_path`

### 3. 形成结论

结论必须区分：

```text
能登录 / 不能登录
能连接数据库 / 不能连接数据库
能进入 schema / 不能进入 schema
能访问对象 / 不能访问对象
权限缺失位置：角色属性 / 数据库 / Schema / 对象 / 默认权限 / search_path
```

### 4. 写操作计划

需要写操作时，先给计划，不直接执行：

```text
目标用户：
目标数据库：
目标 Schema：
目标对象：
将执行的 SQL：
影响范围：
回滚 SQL：
风险：
```

用户确认后才执行。

## 使用示例

**示例 1：审计用户权限**

> 用户：app_user 查不了 orders 表，帮我看看为什么
>
> Agent：（执行只读审计）审计发现：`app_user` 角色有 `public` schema 的 USAGE 权限，但 `orders` 表在 `app` schema 下，该角色缺少 `app` schema 的 USAGE 权限。建议：`GRANT USAGE ON SCHEMA app TO app_user;`。需要我执行吗？

**示例 2：创建只读用户**

> 用户：创建一个只读用户 readonly，只能查 current schema 的表
>
> Agent：将执行以下计划：
> 1. `CREATE ROLE readonly WITH LOGIN PASSWORD '<设定密码>';`
> 2. `GRANT USAGE ON SCHEMA current TO readonly;`
> 3. `GRANT SELECT ON ALL TABLES IN SCHEMA current TO readonly;`
> 请提供密码，然后我确认后执行。
>
> 用户：密码 ReadOnly123
>
> Agent：（执行计划）✅ 只读用户创建完成。

---

## 禁止自动执行

未经用户明确确认，不执行：

```text
CREATE ROLE
ALTER ROLE
DROP ROLE
GRANT
REVOKE
ALTER DEFAULT PRIVILEGES
ALTER SCHEMA OWNER
ALTER DATABASE OWNER
DROP OWNED
REASSIGN OWNED
```

默认禁止授予：

```text
SUPERUSER
CREATEROLE
CREATEDB
REPLICATION
BYPASSRLS
```

确实需要时，必须单独说明风险并再次确认。

## 回复格式

```text
权限结论：正常 / 缺权限 / 高风险 / 未验证
连接入口：<CN host:port/database>
目标角色：<role>
缺失位置：<无 / database / schema / object / default privileges / role attribute>
建议动作：<只读建议或待确认 SQL>
风险：<无 / 高权限 / 影响现有业务 / 需要回滚>
```
