# OpenTenBase 用户、角色与权限原则

本文件是 OpenTenBase 权限模型的长期认知底座，权限审计、授权规划、排查 permission denied 时优先参考。具体命令、系统表字段必须结合当前版本确认。

## 角色与权限核心原则

- OpenTenBase 基本沿用 PostgreSQL 角色模型：用户是具有 `LOGIN` 属性的角色，非登录角色可作为权限集合。
- 角色属性、角色成员关系、对象所有权和对象权限是不同概念，不能相互替代。
- 普通业务用户和权限应通过 CN 统一创建与管理，不应只在单个 DN 上修改。
- 对象访问通常同时依赖数据库、Schema 和对象权限；`search_path` 只影响对象查找，不代表已经授权。
- 序列是独立对象，表权限不一定包含序列权限。
- 权限管理应遵循最小权限原则；删除拥有对象的角色前，应先处理对象所有权和依赖关系。

## 分布式环境的权限特殊性

- 用户、角色和权限属于全局对象，必须通过 CN 统一维护，让集群各节点认知一致；只在单个 DN 上改会造成元数据不一致。
- 权限变更后应确认所有 CN 上的视图一致，避免"从 A CN 连能查、从 B CN 连报错"。
- 序列作为全局协调对象，其权限需单独授予，不随表权限自动附带。

## permission denied 三层排查模型

遇到"能连接却查不了 / 报 permission denied"时，按层次定位：

1. **数据库层**：角色是否有目标数据库的 `CONNECT` / 相关权限；
2. **Schema 层**：角色是否有该 Schema 的 `USAGE`（没有 USAGE，即使表上有权限也访问不到）；
3. **对象层**：角色是否有表/视图/序列的 `SELECT` / `INSERT` / `UPDATE` / `DELETE` / `USAGE` 等具体权限。

补充检查：`search_path` 是否指向了预期 Schema（它只影响对象查找，不改变授权）；对象 owner 与实际操作者是否一致。

## 授权与收敛的安全实践

- 只读用户：仅授予目标 Schema 的 `USAGE` + 表的 `SELECT`，必要时用 `ALTER DEFAULT PRIVILEGES` 让未来新建对象自动带上只读权限。
- 收敛超级用户：审计 `pg_roles` 中的 `rolsuper` / `rolcreaterole` / `rolcreatedb`，对不必要的高权限角色降权。
- 删除角色前：先用 `REASSIGN OWNED` / `DROP OWNED` 处理该角色拥有的对象与依赖，再删除，避免对象悬空。
- 所有回收/降权/删除操作都属于变更类，执行前展示影响范围并获得确认。

## 权限审计常用只读视图（按当前版本核对字段）

- `pg_roles` / `pg_authid`：角色属性与成员关系；
- `information_schema.role_table_grants`：表级授权明细；
- `pg_class` + `pg_namespace`：对象所有权与所属 Schema；
- `pg_default_acl`：默认权限设置。
