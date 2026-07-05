# 手动启动集群

仅在用户明确选择手动启动后使用。本流程只启动现有节点，不创建节点、不修改配置。

先确认并切换到 OpenTenBase 运行用户：

```bash
su - <opentenbase_user>
```

不要用 root 直接启动 CN/DN/GTM，除非当前安装明确要求且用户确认。

## 1. 收集节点清单

优先从现有 `pgxc_ctl` 配置、`pgxc_ctl.conf`、状态输出或用户提供的信息中取得：

```text
节点名称
节点角色
主机
主备关系
程序目录
数据目录
端口
日志路径
运行用户
```

不能确认节点角色、数据目录或主备关系时停止，不按目录名猜测。

查找本机工具：

```bash
command -v gtm_ctl pg_ctl psql 2>/dev/null || true
type -a gtm_ctl pg_ctl psql 2>/dev/null || true
```

查看实际语法：

```bash
<gtm_ctl> --help
<pg_ctl> --help
```

各节点使用同一套 OpenTenBase 安装目录中的程序。

## 2. 启动前检查

对每个节点检查：

```bash
ls -ld <data_dir>
ls -l <data_dir>/gtm.conf <data_dir>/postgresql.conf \
  <data_dir>/PG_VERSION <data_dir>/gtm.pid \
  <data_dir>/postmaster.pid 2>/dev/null || true
```

并检查：

```bash
ps -ef | grep -E '[p]ostgres|[g]tm'
ss -lntp 2>/dev/null || ss -lnt 2>/dev/null
```

规则：

- 已运行的节点不重复启动。
- 数据目录必须属于预期运行用户。
- 发现 PID 文件时先核对对应进程。
- PID 文件存在但进程不存在时停止并报告，不删除文件。
- 使用绝对路径和独立日志文件。

## 3. 生成启动计划

按以下顺序排列：

```text
GTM 主节点
GTM 备节点或代理（如有）
DN 节点
CN 节点
```

展示每个节点的主机、角色、数据目录、端口、日志和精确命令，然后按计划执行。

## 4. 启动 GTM

GTM 主节点：

```bash
<gtm_ctl> start -Z gtm -w -t 60 \
  -D <gtm_data> -l <gtm_log>
```

GTM 备节点：

```bash
<gtm_ctl> start -Z gtm_standby -w -t 60 \
  -D <gtm_standby_data> -l <gtm_standby_log>
```

GTM Proxy：

```bash
<gtm_ctl> start -Z gtm_proxy -w -t 60 \
  -D <gtm_proxy_data> -l <gtm_proxy_log> -i <proxy_name>
```

仅执行实际拓扑中存在的角色。每一步验证成功后再继续。

## 5. 启动 DN

在对应主机以数据目录所有者执行：

```bash
<pg_ctl> start -Z datanode -w -t 60 \
  -D <dn_data> -l <dn_log>
```

逐个确认进程和监听端口。某个 DN 失败时停止，不继续启动 CN。

## 6. 启动 CN

在对应主机以数据目录所有者执行：

```bash
<pg_ctl> start -Z coordinator -w -t 60 \
  -D <cn_data> -l <cn_log>
```

逐个确认进程和监听端口。

## 7. 集群验证

```bash
ps -ef | grep -E '[p]ostgres|[g]tm'
ss -lntp 2>/dev/null || ss -lnt 2>/dev/null
```

连接一个 CN：

```bash
PGCONNECT_TIMEOUT=5 psql -X -w -h <cn_host> -p <cn_port> \
  -U <db_user> -d <database> -Atqc 'SELECT 1;'
```

查看拓扑：

```bash
PGCONNECT_TIMEOUT=5 psql -X -w -h <cn_host> -p <cn_port> \
  -U <db_user> -d <database> -F '|' -Atqc \
  'SELECT node_name,node_type,node_host,node_port FROM pgxc_node ORDER BY node_name;'
```

手动启动成功必须满足：

- GTM 正常运行
- 预期 DN 和 CN 进程存在
- 预期端口监听
- CN 可执行 `SELECT 1`
- 查询到的拓扑与计划一致

任一步失败时停止并报告对应日志，不继续猜测或修改配置。
