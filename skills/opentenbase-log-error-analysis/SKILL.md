---
name: opentenbase-log-error-analysis
description: 分析 OpenTenBase 日志、启动失败、连接失败、节点异常、管理工具报错和插件/SQL 执行错误。用于用户要求排查报错、查看日志、解释 ERROR/FATAL/WARNING、判断 CN/DN/GTM 或 opentenbase_ctl/pgxc_ctl 问题时。
version: 1.0.0
user-invocable: true
---

# OpenTenBase 日志与错误分析

若目标在远程 Linux，先使用 `linux-ssh-access`。默认只读分析，不启停集群、不修改配置、不清理日志。

## 运行用户

优先进入 OpenTenBase 运行用户环境：

```bash
su - <opentenbase_user>
```

不要在 root 环境下直接断定 `opentenbase_ctl`、`pgxc_ctl`、`psql` 或日志目录不存在。若用户只提供 root，先询问 OpenTenBase 运行用户，并确认是否允许 `su - <运行用户>`。

## 标准流程

1. 确认目标和时间范围：

```bash
hostname
whoami
date
```

询问或推断用户关心的是：启动失败、停止异常、连接失败、SQL 报错、节点间通信异常、插件部署异常，还是管理工具报错。

2. 获取状态证据：

```bash
opentenbase_ctl status -c <config.ini>
printf 'monitor all\nquit\n' | pgxc_ctl --home <pgxc_home> -c <pgxc_ctl.conf>
ps -ef | grep -E '[p]ostgres|[g]tm'
ss -lntp 2>/dev/null || ss -lnt 2>/dev/null
```

本机命令不可用时，只报告原因，不自动切换工具做状态变更。

3. 定位日志：

读取 `references/log-locations.md`。先从管理工具日志和相关节点日志开始，不无边界 `find /`。

4. 提取关键错误：

```bash
grep -Ein 'ERROR|FATAL|PANIC|WARNING|could not|failed|invalid|permission denied|No such file|already in use|Connection refused|not found' <log_file> | tail -n 50
tail -n 100 <log_file>
```

5. 关联判断：

读取 `references/error-patterns.md`。把日志时间、节点名、节点角色、端口、进程和连接结果对齐后再下结论。

## 安全边界

禁止自动执行：

```text
start、stop、restart、init、clean、kill、failover、expand、shrink
删除/截断/压缩/移动日志
修改配置
删除 postmaster.pid / gtm.pid
执行写数据库 SQL
```

需要查看系统日志时，先说明原因；若需要 root、sudo 或敏感日志，先请求用户确认。

## 结果格式

```text
问题类型：启动失败 / 连接失败 / 节点通信异常 / 管理工具异常 / SQL 错误 / 未确定
影响节点：<CN/DN/GTM/管理工具>
关键证据：<日志路径:行号 或 命令输出摘要>
初步判断：<一两句话>
风险等级：低 / 中 / 高
建议下一步：<只读补充检查 或 需用户确认的修复动作>
未验证项：<仍缺少的证据>
```

不要只凭单条 `ERROR` 下结论。`FATAL: terminating connection due to administrator command` 在正常停止期间可能是预期现象。
