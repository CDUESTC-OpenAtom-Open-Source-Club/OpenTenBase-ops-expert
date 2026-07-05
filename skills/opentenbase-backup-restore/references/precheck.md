# 备份前只读检查

本文件只包含只读检查。

## 运行用户

先进入 OpenTenBase 运行用户环境：

```bash
su - <opentenbase_user>
```

## 工具版本

优先使用 OpenTenBase 自带工具：

```bash
command -v pg_dump pg_restore psql createdb
pg_dump --version
pg_restore --version
psql --version
createdb --version
```

如果工具版本和服务器版本明显不一致，先报告风险，不继续执行备份。

## 集群和连接

通过 CN 检查：

```sql
SELECT version();

SELECT node_name,node_type,node_host,node_port
FROM pgxc_node
ORDER BY node_name;

SELECT current_user, current_database();
```

不要把 DN 当作普通逻辑备份入口。

## 数据库大小

```sql
SELECT datname,
       pg_size_pretty(pg_database_size(datname)) AS size
FROM pg_database
ORDER BY datname;
```

备份位置可用空间：

```bash
df -h <backup_dir>
```

备份目录权限：

```bash
ls -ld <backup_dir>
```

## 对象概况

```sql
SELECT nspname,
       pg_get_userbyid(nspowner) AS owner
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

## 角色和权限概况

```sql
SELECT rolname,
       rolcanlogin,
       rolsuper,
       rolcreatedb,
       rolcreaterole
FROM pg_roles
ORDER BY rolname;
```

逻辑恢复时，角色和权限可能需要单独处理。不要假设备份文件一定能在目标环境完整恢复权限。

## 备份元信息记录

备份前记录：

```text
时间：
服务器版本：
CN：
数据库：
备份范围：
备份命令：
备份文件：
执行用户：
```
