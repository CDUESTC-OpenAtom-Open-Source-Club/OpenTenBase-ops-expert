# 集群管理配置文件

本文件用于识别和审计 OpenTenBase 集群管理配置。默认只读，不自动修改。

## 常见配置

`opentenbase_ctl`：

```text
/data/opentenbase/opentenbase_ctl_current/config.ini
```

`pgxc_ctl`：

```text
/data/opentenbase/pgxc_ctl/pgxc_ctl.conf
```

实际路径必须从当前运行用户环境、管理工具帮助、工作目录或用户说明中确认，不要硬编码。

## 什么时候读取

- `opentenbase_ctl status` 或 `pgxc_ctl monitor all` 输出与预期不一致；
- VM、主机名、IP、端口、数据目录发生变化；
- 用户要求解释或调整 CN/DN/GTM 拓扑；
- 启停失败怀疑是配置文件与真实环境不一致。

## 只读审计命令

```bash
su - <opentenbase_user>
ls -l <config_file>
sed -n '1,220p' <config_file>
```

同时对比：

```bash
ps -ef | grep -E '[p]ostgres|[g]tm'
ss -lntp 2>/dev/null || ss -lnt 2>/dev/null
psql -h <cn_host> -p <cn_port> -U <db_user> -d <database> \
  -Atqc 'SELECT node_name,node_type,node_host,node_port FROM pgxc_node ORDER BY node_name;'
```

只报告差异，不自动修复。

## 修改前必须确认

修改配置前必须展示：

```text
配置文件路径
当前备份路径
将修改的节点/IP/端口/目录
修改前后 diff
是否需要重启或 reload
失败回滚方式
影响哪些 CN/DN/GTM
```

建议备份：

```bash
cp -a <config_file> <config_file>.bak.$(date +%Y%m%d%H%M%S)
```

## 禁止自动执行

未经用户确认，不执行：

```text
修改 config.ini 或 pgxc_ctl.conf
init all
clean all
kill all
failover
节点增删
删除数据目录
删除 pid/lock 文件
```

## 修改后验证

用户确认并完成修改后，至少验证：

```text
管理工具状态
GTM/CN/DN 进程
监听端口
至少一个 CN 的 SELECT 1
pgxc_node 拓扑
```

如果任一项不一致，停止继续变更，报告证据。
