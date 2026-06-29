---
name: opentenbase-cluster-ops
description: 管理已经安装和初始化完成的 OpenTenBase 集群，完成状态查看、启动、停止和运行验证。
---

# OpenTenBase 集群运维

若集群位于远程 Linux，先使用 `linux-ssh-access`。

本 Skill 适用于已经安装、初始化并配置完成的集群，不负责安装、初始化、扩缩容、故障切换、备份恢复或配置修改。

## 运行用户

不要在 root 环境下直接判断 `opentenbase_ctl`、`pgxc_ctl`、`psql` 是否可用。OpenTenBase 工具通常依赖运行用户的 `PATH`、`LD_LIBRARY_PATH`、工作目录和文件权限。

若用户只提供 root 账号和密码，先询问：

```text
OpenTenBase 是由哪个系统用户运行的？例如 opentenbase。
是否允许我执行 su - <运行用户> 进入该用户环境？
```

若用户提供的是其他 Linux 用户，也先确认它是否就是 OpenTenBase 运行用户；如果不是，询问正确运行用户、切换方式和是否需要密码。

确认后优先进入运行用户环境：

```bash
su - <opentenbase_user>
```

后续查找工具、查看状态、启动、停止和执行 `psql`，都应在该用户环境中进行。只有在需要检查系统级网络、进程或文件权限时，才回到 root 或当前 SSH 用户。

## 管理方式

默认读取并使用：

```text
references/opentenbase_ctl.md
```

若在执行状态变更前确认 `opentenbase_ctl` 无法使用，可读取：

```text
references/pgxc_ctl.md
```

切换前说明原因、工具、配置和计划命令，并获得用户确认。

用户明确要求手动启动时，读取：

```text
references/manual_start.md
```

手动启动时先展示完整节点计划，再按计划执行；不作为自动补救步骤。

## 执行流程

### 1. 确认目标环境

```bash
hostname
whoami
uname -s
```

必须确认当前是目标 Linux 主机。

### 2. 查看当前状态

按照已选方式：

- 查找程序和配置
- 查看本机帮助
- 执行状态命令
- 检查进程和端口

通用检查：

```bash
ps -ef | grep -E '[p]ostgres|[g]tm'
ss -lntp 2>/dev/null || ss -lnt 2>/dev/null
```

集群已处于目标状态时，不重复执行状态变更。

### 3. 执行计划

执行启动或停止前，展示：

- 目标主机
- 系统用户
- OpenTenBase 运行用户
- 管理方式
- 程序绝对路径
- 配置或数据目录
- 精确命令
- 执行顺序
- 影响范围

用户提出启动请求后，按计划直接执行。

停止操作先展示计划，等待用户确认后执行。

### 4. 执行并验证

状态变更后等待数秒，最多验证 3 次：

- 管理工具或节点状态
- GTM、CN、DN 进程
- 预期监听端口
- CN SQL 连接

从状态输出、配置或用户信息中取得 CN 地址和端口，不猜默认值：

```bash
PGCONNECT_TIMEOUT=5 psql -X -w -h <cn_host> -p <cn_port> \
  -U <db_user> -d <database> -Atqc 'SELECT 1;'
```

必要时查看节点拓扑：

```bash
PGCONNECT_TIMEOUT=5 psql -X -w -h <cn_host> -p <cn_port> \
  -U <db_user> -d <database> -F '|' -Atqc \
  'SELECT node_name,node_type,node_host,node_port FROM pgxc_node ORDER BY node_name;'
```

## 验证未通过

若状态、进程、端口或 SQL 与预期不一致：

1. 标记为“启动未验证”或“停止未验证”。
2. 收集状态、进程、端口和明确日志。
3. 停止后续状态变更，向用户报告现象和证据。

其他处理方案由用户重新选择并确认。

## 安全边界

不执行：

```text
install、delete、init、clean、kill、failover、expand、shrink、
节点增删、数据目录删除、配置修改、破坏性 SQL
```

不得删除 `postmaster.pid`、`gtm.pid` 或其他锁文件。发现疑似残留文件时，只报告。

## 成功标准

启动成功：

- 状态符合预期
- 预期 GTM、CN、DN 进程存在
- 预期端口监听
- 至少一个 CN 的 `SELECT 1` 成功

停止成功：

- 状态显示停止
- 相关进程消失
- 相关端口不再监听

命令退出码或 `Success` 文字不能单独证明成功。

## 回复格式

```text
OpenTenBase：正常 / 已停止 / 启动未验证 / 停止未验证 / 异常
目标：<host>
方式：<opentenbase_ctl / pgxc_ctl / 手动启动>
GTM：<running/total>
CN：<running/total>
DN：<running/total>
CN 连接：成功 / 失败 / 未验证
问题：<仅异常时填写>
```

除非用户要求，不粘贴完整日志。
