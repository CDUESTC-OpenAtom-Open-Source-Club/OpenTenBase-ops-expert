---
name: opentenbase-routine-maintenance
description: 设计和执行 OpenTenBase 日常定时运维巡检。适用于每日/每周/月度健康检查、Linux cron 或 systemd timer 方案、巡检脚本规划、备份文件检查、日志检查、资源检查和巡检报告。默认只读，不自动修改 crontab、systemd、数据库或集群状态。
version: 1.1.0
author: CDUESTC OpenAtom Open Source Club
tools: [shell, filesystem]
user-invocable: true
---

# OpenTenBase 日常定时运维

若目标数据库在远程 Linux，先使用 `linux-ssh-access`。若用户只给 root 账号，先确认 OpenTenBase 运行用户，并请求允许：

```bash
su - <opentenbase_user>
```

本 Skill 负责日常巡检和定时运维设计，不负责安装、启停、故障切换、备份恢复执行、权限变更、SQL 调优或插件部署。

## 核心原则

- 默认只读巡检，不修改数据库、不修改配置、不启停集群。
- 先人工跑通巡检命令，再考虑放入 cron 或 systemd timer。
- 定时任务应使用 OpenTenBase 运行用户环境，不要默认 root 执行。
- 不假设每台机器都能直接运行管理工具；`opentenbase_ctl`/`pgxc_ctl` 失败时记录错误，改用进程、端口和 CN 连接做只读补充检查。
- 日常任务以发现问题和报告为主，不自动修复。
- 自动任务写入 `crontab` 或 systemd 前必须展示计划并获得用户确认。

## 选择 reference

- 每日巡检项：读取 `references/daily-checklist.md`。
- 深度健康巡检（XID age/autovacuum/长事务/2PC 残留/复制延迟/膨胀等 P0 隐患，只读）：读取 `references/deep-health-check.md`。
- 每周/月度运维项：读取 `references/weekly-monthly.md`。
- Linux 定时任务设计：读取 `references/linux-scheduling.md`。
- 巡检报告格式：读取 `references/report-template.md`。
- 告警阈值和禁止项：读取 `references/thresholds-and-boundaries.md`。

## 标准流程

### 1. 确认环境

```bash
hostname
whoami
date '+%F %T %Z'
```

进入 OpenTenBase 运行用户后确认工具：

```bash
command -v opentenbase_ctl psql pg_dump pg_restore createdb
```

### 2. 先做一次人工巡检

读取 `references/daily-checklist.md`，执行只读检查：

```text
集群状态
进程和端口
CN SELECT 1
pgxc_node 拓扑
磁盘和内存
数据库大小
扩展列表
近期 ERROR/FATAL 日志
备份文件存在性
```

人工巡检通过后，再讨论定时化。

### 3. 选择定时方式

向用户说明并选择：

```text
1. cron：简单、常见，适合每日巡检脚本。
2. systemd timer：可追踪状态和日志，适合更规范的 Linux 运维。
3. 不设置定时任务，只保留手动巡检清单。
```

不要替用户直接写入定时任务。

### 4. 生成计划

写入 cron/systemd 前必须展示：

```text
执行用户：
执行频率：
脚本路径：
日志路径：
输出报告路径：
命令内容：
失败处理：
回滚方式：
```

用户确认后才执行。

## 使用示例

**示例 1：每日巡检**

> 用户：帮我做一次日常巡检
>
> Agent：（检查集群状态、资源、备份、日志）
> ```
> 每日巡检报告 — 2026-07-02
> 主机：192.168.1.10
> 集群状态：✅ running
> CN：1/1 | DN：1/1 | GTM：1/1
> 磁盘：/data 67% (30GB/45GB)
> 内存：5.2GB / 8.0GB
> 备份：✅ 最近备份 2026-07-01 02:00
> 日志：无 ERROR/FATAL
> 结论：正常，无风险项
> ```

**示例 2：设计定时巡检 cron**

> 用户：帮我设置每天凌晨 2 点自动巡检
>
> Agent：建议添加以下 crontab（以 opentenbase 用户执行）：
> ```
> 0 2 * * * /usr/local/bin/otb-daily-check.sh
> ```
> 巡检脚本内容参考 `references/daily-checklist.md`。需要我帮你生成并部署这个脚本吗？

---

## 禁止自动执行

未经确认，不执行：

```text
crontab -e
crontab <file>
systemctl enable/start timer
写入 /etc/cron*
写入 /etc/systemd/system
opentenbase_ctl start/stop
pgxc_ctl start/stop/init/clean/kill/failover
VACUUM FULL
REINDEX
ANALYZE
DELETE/TRUNCATE/DROP/ALTER
自动清理 WAL、日志、备份文件或数据目录
```

## 回复格式

```text
日常运维结论：正常 / 有风险 / 未验证 / 需要用户确认
主机：<host>
运行用户：<opentenbase_user>
集群状态：<running/stopped/unknown>
CN 连接：<ok/fail/not checked>
资源：<disk/memory summary>
备份：<ok/missing/not checked>
日志：<clean/warnings/errors/not checked>
建议：<下一步>
```
