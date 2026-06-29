# 每日只读巡检清单

本清单只做检查和报告，不自动修复。

## 1. 运行用户和时间

```bash
hostname
whoami
date '+%F %T %Z'
```

确认已进入 OpenTenBase 运行用户：

```bash
su - <opentenbase_user>
```

## 2. 集群状态

优先在已验证的管理主机或控制节点上使用：

```bash
opentenbase_ctl status
```

如果 `opentenbase_ctl` 存在但因环境变量、动态库或配置问题失败，不要自动修复环境，也不要启停集群；记录错误输出，继续做进程、端口和 CN 连接检查。

如果当前环境只支持 `pgxc_ctl`，再按 `opentenbase-cluster-ops` 的规则使用 `monitor all`。

## 3. 进程和端口

```bash
ps -ef | grep -E '[p]ostgres|[g]tm'
ss -lntp 2>/dev/null || ss -lnt 2>/dev/null
```

只报告异常，不自动 kill 或 restart。

## 4. CN 连接

从 `opentenbase_ctl status` 或配置中取得 CN 地址：

```bash
PGCONNECT_TIMEOUT=5 psql -X -w -h <cn_host> -p <cn_port> \
  -U <db_user> -d <database> -Atqc 'SELECT 1;'
```

至少检查一个可用 CN；多 CN 环境建议逐个检查。

## 5. 拓扑

```sql
SELECT node_name,node_type,node_host,node_port
FROM pgxc_node
ORDER BY node_name;
```

对比结果和预期 CN/DN/GTM 数量。

## 6. 系统资源

```bash
free -h
df -h / /data 2>/dev/null || df -h
```

关注：

- 可用内存；
- swap 是否大量使用；
- `/data` 或数据目录所在磁盘是否接近满。

## 7. 数据库概况

```sql
SELECT datname, pg_size_pretty(pg_database_size(datname))
FROM pg_database
ORDER BY datname;

SELECT extname, extversion
FROM pg_extension
ORDER BY extname;
```

## 8. 日志快速检查

先找最近日志：

```bash
find /data/opentenbase -maxdepth 5 -type f -name "*.log" \
  -printf "%TY-%Tm-%Td %TH:%TM %p\n" 2>/dev/null | sort | tail -30
```

再检查最近错误：

```bash
grep -Ei "ERROR|FATAL|PANIC|could not|failed" <recent_log> | tail -50
```

日志路径必须按当前环境确认，不要硬编码。

## 9. 备份文件检查

如果用户已有备份目录：

```bash
ls -lh <backup_dir> | tail
find <backup_dir> -type f -mtime -2 -ls 2>/dev/null
```

只检查是否存在和大小，不自动删除旧备份。
