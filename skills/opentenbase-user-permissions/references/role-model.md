# OpenTenBase 角色模型要点

OpenTenBase 基本沿用 PostgreSQL 角色模型。用户本质上是带 `LOGIN` 属性的角色。

## 核心概念

- 角色：权限主体，可以拥有对象，也可以被授予权限。
- 用户：具有 `LOGIN` 的角色。
- 权限组：不带 `LOGIN` 的角色，适合承载业务权限。
- 成员关系：`GRANT role_a TO user_b` 让用户继承或使用权限组能力。
- 对象 owner：对象所有者天然拥有对象管理能力，不等同于普通授权。

## 权限层次

访问一个表通常至少涉及：

```text
数据库 CONNECT
Schema USAGE
表 SELECT/INSERT/UPDATE/DELETE
序列 USAGE/SELECT（如果用自增）
函数 EXECUTE（如果调用函数）
```

任一层缺失都可能导致访问失败。

## 分布式环境注意点

- 普通权限管理应连接 CN 执行。
- 不应只在某个 DN 上创建用户或授权。
- 多 CN 环境中，变更后应至少在另一个 CN 做只读验证。
- 一个 CN 可连接不代表所有 CN 都可用；权限问题排查时仍应说明所连接的 CN。

## 常见误区

- `search_path` 能找到对象，不代表有权限。
- 表有 `INSERT`，不代表序列有 `USAGE`。
- 默认权限只影响未来对象，不影响已有对象。
- `GRANT ALL` 不等于可以登录数据库。
- `SUPERUSER` 不是普通授权手段，而是绕过大多数权限检查的高风险属性。

