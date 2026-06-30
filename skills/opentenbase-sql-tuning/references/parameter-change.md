# 数据库参数变更

本文件用于 SQL 调优过程中涉及 OpenTenBase/PostgreSQL 参数时。默认只读分析，不自动改配置。

## 常见文件

每个 CN/DN 数据目录通常包含：

```text
postgresql.conf
postgresql.auto.conf
pg_hba.conf
pg_ident.conf
```

具体路径从进程参数或管理配置确认：

```bash
ps -ef | grep -E '[p]ostgres'
```

## 优先只读查询

先连接 CN 查看当前值：

```sql
SHOW shared_buffers;
SHOW max_connections;
SHOW work_mem;
SHOW maintenance_work_mem;
SHOW max_pool_size;
SELECT name, setting, unit, context, source
FROM pg_settings
WHERE name IN ('shared_buffers','max_connections','work_mem','maintenance_work_mem','max_pool_size');
```

`context` 可帮助判断是否需要 reload 或 restart。不要只凭参数名猜生效方式。

## 变更原则

- 优先给建议，不直接执行；
- 优先使用当前 OpenTenBase 版本支持的官方方式；
- 修改文件前必须备份；
- 展示修改前后 diff；
- 说明是否需要 reload 或 restart；
- 多 CN/DN 环境要说明影响哪些节点，不能只改一个节点后声称全局生效。

## 高风险参数

以下参数可能影响内存、连接或启动，必须单独说明风险：

```text
shared_buffers
max_connections
max_pool_size
work_mem
maintenance_work_mem
listen_addresses
port
```

## 禁止自动执行

未经用户确认，不执行：

```text
ALTER SYSTEM
直接编辑 postgresql.conf
直接编辑 postgresql.auto.conf
reload/restart
VACUUM FULL
REINDEX
```

## 修改后验证

如果用户确认并完成变更，验证：

```sql
SHOW <parameter>;
SELECT name, setting, source FROM pg_settings WHERE name='<parameter>';
SELECT 1;
```

必要时再检查进程、端口和 `pgxc_node`。
