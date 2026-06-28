---
name: otb-ops-dba
description: 当 Agent 需要对 OpenTenBase 进行日常监控巡检、故障应急（特别是集群启动时序与中间态误判）、性能调优、分布式定时任务管理时使用。覆盖 opentenbase-ctl 管理全流程，强调"先确认进程再看端口""绝不绕过 ctl 手动拉进程"等运维铁律。
version: 1.0.0
user-invocable: true
---

# OpenTenBase 运维与 DBA

目标：对已部署的 OpenTenBase 集群执行日常监控巡检、故障应急、性能调优与分布式定时任务管理，输出可执行的诊断结论与操作建议，杜绝因"中间态误判"导致的二次故障。

输出必须包含：

1. 集群/节点状态概览（进程、端口、角色）
2. 异常项与告警（区分"真正失败"与"启动中间态"）
3. 操作建议或运维结果（命令 + 判断标准）

---

## 前置条件

- 目标主机已通过 `linux-ssh-access` 技能完成 SSH 连接（免密已配置）
- OpenTenBase 已通过 `opentenbase-deploy` 技能完成部署，`opentenbase-ctl` 可用
- 拥有 `sudo` 或数据库运行用户（默认 `opentenbase`）权限
- 已知集群拓扑：GTM 端口（默认 5435）、Coordinator 端口（默认 5432）、Datanode 端口（默认 5433/5434）
- 日志路径形如 `/var/log/opentenbase/<version>/`，数据路径形如 `/var/lib/opentenbase/<version>/`

---

## 日常监控巡检场景

定期巡检，逐项检查并对照阈值。任一项异常需进入对应故障应急流程。

### 1. 集群整体状态

```bash
# 查看集群各节点状态（GTM / Coordinator / Datanode）
sudo opentenbase-ctl status
```

**判断标准**：所有节点显示 `running` 为正常。任一节点显示 `stopped` 需进入故障应急场景 A/B 排查。

**注意**：`status` 命令基于端口检测，端口不通即显示 `stopped`。若节点刚启动或正在重启，端口可能短暂不通但进程存活——此时需配合下方"进程检查"综合判断，不能仅凭 `status` 下结论。

### 2. 节点进程存活检查

```bash
# 检查 GTM 进程
pgrep -af gtm

# 检查 Coordinator / Datanode 进程（postgres 内核）
pgrep -af postgres | grep -E "coordinator|datanode"

# 或一次性查看所有 OpenTenBase 相关进程
pgrep -af "gtm|postgres" | grep opentenbase
```

**判断标准**：每个角色至少有一个进程存活。GTM 进程名含 `gtm`，Coordinator/Datanode 进程名含 `postgres` 并带角色标识。进程不存在需进入故障应急场景 B。

### 3. 端口监听检查

```bash
# 检查关键端口（5432 Coordinator / 5433-5434 Datanode / 5435 GTM）
sudo ss -tlnp | grep -E ":(5432|5433|5434|5435)"
```

**判断标准**：四个端口均在 LISTEN 状态为正常。端口不通但进程存活 = 启动中间态或绑定异常，进入故障应急场景 A；端口不通且进程不存在 = 真正宕机，进入场景 B。

### 4. 数据库连接数

```bash
# 查看当前活跃连接数与上限
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c \
  "SELECT count(*) AS active, (SELECT setting FROM pg_settings WHERE name='max_connections') AS max FROM pg_stat_activity;"
```

**判断标准**：`active / max` 比值 > 80% 需告警，> 95% 进入故障应急场景 C。

### 5. 慢查询检查

```bash
# 查看运行超过 5 秒的查询
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c \
  "SELECT pid, now() - query_start AS duration, query FROM pg_stat_activity WHERE state='active' AND now() - query_start > interval '5 seconds' ORDER BY duration DESC;"
```

**判断标准**：存在慢查询需进入性能调优场景分析执行计划。

### 6. 磁盘与内存

```bash
# 磁盘使用率（数据目录所在分区）
df -h /var/lib/opentenbase

# 内存使用
free -h

# 数据目录占用 TOP
sudo du -sh /var/lib/opentenbase/<version>/* 2>/dev/null | sort -rh | head -10
```

**判断标准**：磁盘使用率 > 80% 告警，> 90% 紧急处理（清理 WAL/日志或扩容）。可用内存 < 总内存 10% 需检查是否有内存泄漏或调整 `shared_buffers`。

---

## 故障应急场景

### 场景 A：集群启动后 GTM 显示 STOPPED（启动时序与中间态误判）

**这是部署与运维中最易误判的场景，必须首要掌握。**

#### 现象

- 执行 `opentenbase-ctl init` 后，执行 `opentenbase-ctl start`，退出码为 `1`
- `opentenbase-ctl status` 显示 GTM 为 `STOPPED`，但 Coordinator 和 Datanode 显示 `RUNNING`
- GTM 日志（`/var/log/opentenbase/<version>/gtm.log`）出现 `GTM_SHUTDOWNED` 状态
- AI/运维人员误判为"GTM 启动失败"，手动用 `nohup` 拉起 GTM，SSH 断开后 GTM 进程又死了，日志再次记录 `GTM_SHUTDOWNED`

#### 根因（三层，缺一不可）

**第一层 — `init` 设计如此，不启动进程**

`opentenbase-ctl init` 只负责初始化数据目录和配置文件，不启动任何进程。init 完成后 GTM/Coordinator/Datanode 全部处于停止状态是**正常行为**，日志会提示 `Run 'opentenbase-ctl start' to start the cluster`。init 后看到全部 stopped 不要慌。

**第二层 — `start` 的 `wait_for_port` 60s 超时过于激进**

`cmd_start` 通过 `gtm_ctl start` / `pg_ctl start` 拉起进程，这两个工具是 **daemonize** 的：fork 子进程后父进程立即返回，子进程在后台继续初始化。GTM 完整启动需要时间，若 60 秒内端口未进入 LISTEN 状态，`cmd_start` 直接 `exit 1`——但此时 GTM daemon 进程可能仍在后台启动中，并非真正失败。脚本把"启动慢"误报成"启动失败"。

**第三层 — `status` 只看端口不看进程**

`cmd_status` 用 `ss`/`netstat` 查端口，端口不通就显示 `STOPPED`。当进程已 daemonize 存活但仍在启动初始化阶段时，`status` 错误显示 `STOPPED`，加重误判。AI/运维人员看到 `STOPPED` 就去手动干预，绕过 `opentenbase-ctl` 用 `nohup` 或前台命令拉 GTM——这种手动拉起的进程绑定在当前 SSH 会话上，SSH 断开后被 `SIGHUP` 信号杀死，日志记 `GTM_SHUTDOWNED`。

#### 铁证：为什么 Coordinator 和 Datanode 活下来了

Coordinator 和 Datanode 在 SSH 断开后依然存活——它们和 GTM 使用的是**完全相同**的 `as_svc` + `gtm_ctl`/`pg_ctl start` daemonize 方式。如果 SSH 断开会杀进程，三个角色都该死。实际死掉的只是 AI 手动 `nohup` 拉起的那个 GTM，因为它没走 daemonize 路径，进程的父进程是 SSH 会话 shell，会话结束被 `SIGHUP` 清理。

#### 正确处理流程

```bash
# 步骤 1：opentenbase-ctl start 返回 exit 1 后，不要立刻查 status！
# 先等待 30-60 秒，让 daemon 进程完成后台启动初始化
sleep 60

# 步骤 2：用 pgrep 确认进程是否存活（不是看端口！）
pgrep -af gtm

# 步骤 3：再查端口是否已监听
sudo ss -tlnp | grep :5435

# 步骤 4：用 opentenbase-ctl status 综合确认
sudo opentenbase-ctl status
```

**判断分支：**

- **进程在 + 端口不通** = 正在启动中间态，继续等待，不要干预。每 15 秒复查一次 `pgrep` 和 `ss`，直到端口监听上。
- **进程在 + 端口通** = 启动成功，`status` 若仍显示 STOPPED 是检测时序问题，可忽略或重查。
- **进程不在** = 真正失败，查日志定位原因：

```bash
# 查看最近 50 行 GTM 日志
tail -50 /var/log/opentenbase/<version>/gtm.log

# 查看启动相关错误
grep -iE "error|fatal|fail" /var/log/opentenbase/<version>/gtm.log | tail -20
```

#### 红线（此场景绝对禁止）

1. **绝不绕过 `opentenbase-ctl` 手动用 `nohup`/前台命令拉进程**。`opentenbase-ctl` 的 daemonize 机制（`as_svc` + `gtm_ctl`/`pg_ctl`）才能保证进程脱离 SSH 会话存活。手动拉的进程绑在 SSH 会话上，断开即死。
2. **`start` 返回 exit 1 后不立刻判失败**。先等 30-60 秒，用 `pgrep` 确认进程状态，再下结论。
3. **判定节点状态不能只看端口**。`status` 显示 STOPPED 不等于进程不存在，必须 `pgrep` 确认进程。
4. 需要重启用 `opentenbase-ctl restart`，需要停用 `opentenbase-ctl stop`，不要手动 kill 后自行拉起。

---

### 场景 B：节点进程不存在（真正宕机）

**现象**：`pgrep -af gtm` 或 `pgrep -af postgres` 无输出，对应端口不通，`status` 显示 STOPPED。

**处理流程：**

```bash
# 1. 查看宕机节点日志，定位退出原因
tail -100 /var/log/opentenbase/<version>/gtm.log       # GTM
tail -100 /var/log/opentenbase/<version>/coordinator.log  # Coordinator
tail -100 /var/log/opentenbase/<version>/datanode.log     # Datanode

# 2. 查找致命错误
grep -iE "error|fatal|panic|corrupt" /var/log/opentenbase/<version>/*.log | tail -30

# 3. 确认数据目录完整性
ls -la /var/lib/opentenbase/<version>/data/

# 4. 用 opentenbase-ctl 重启单个节点（不重启整个集群）
sudo opentenbase-ctl restart gtm            # 仅重启 GTM
sudo opentenbase-ctl restart coordinator    # 仅重启 Coordinator
sudo opentenbase-ctl restart datanode       # 仅重启 Datanode

# 5. 重启后按场景 A 流程验证（等 30-60s 再 pgrep 确认，不要立刻判失败）
```

**判断标准**：重启后进程存活 + 端口监听 + `opentenbase-psql` 可连 = 恢复成功。若日志出现数据损坏（`corrupt`/`panic`），不要强行重启，需进入数据恢复流程并告知用户。

---

### 场景 C：连接数打满

**现象**：新连接报 `FATAL: sorry, too many clients already`，或巡检发现 `active / max > 95%`。

**处理流程：**

```bash
# 1. 查看当前所有活跃会话及其来源
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c \
  "SELECT pid, usename, client_addr, state, query_start, query FROM pg_stat_activity WHERE state='active' ORDER BY query_start;"

# 2. 查看空闲长连接（可能是连接泄漏）
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c \
  "SELECT pid, usename, client_addr, state, now()-state_change AS idle_for FROM pg_stat_activity WHERE state='idle' AND now()-state_change > interval '10 minutes' ORDER BY idle_for DESC;"

# 3. 终止特定会话（替换 <pid>）
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c \
  "SELECT pg_terminate_backend(<pid>);"

# 4. 终止所有空闲超过 10 分钟的会话
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle' AND now()-state_change > interval '10 minutes' AND pid <> pg_backend_pid();"
```

**判断标准**：终止后会话数下降，新连接可建立 = 恢复。若反复打满，需排查应用连接池配置（见性能调优场景的 `max_connections`/`max_pool_size` 部分）。

---

## 性能调优场景

### 1. 慢查询分析

```bash
# 查看累计耗时最长的查询（基于 pg_stat_statements，需插件已启用）
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c \
  "SELECT calls, total_exec_time, mean_exec_time, rows, query FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;"

# 对单条慢查询查看执行计划（替换 <sql> 为实际 SQL）
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c "EXPLAIN ANALYZE <sql>;"
```

**判断标准**：执行计划中出现 `Seq Scan`（全表扫描）且行数大 = 缺索引；`Nested Loop` 配合大表 = 关联方式不佳；`Sort` 耗时高 = 缺排序索引或 `work_mem` 不足。

### 2. 内存参数调优

关键参数与内存的关系（以 8GB 服务器为例）：

| 参数 | 说明 | 8GB 建议值 | 计算逻辑 |
|------|------|-----------|----------|
| `shared_buffers` | 共享内存缓冲池 | `2GB` | 总内存的 25% |
| `max_connections` | 最大连接数 | `200` | 每连接约 5-10MB，200 连接约需 2GB |
| `max_pool_size` | 连接池上限（CN/DN 各自） | `100` | 应小于 `max_connections`，避免池耗尽主连接 |
| `work_mem` | 单查询排序/哈希内存 | `16MB` | `(总内存 - shared_buffers) / (max_connections * 2)` |
| `maintenance_work_mem` | 维护操作内存（VACUUM/索引） | `256MB` | 可适当调大加速维护 |

```bash
# 查看当前参数值
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c \
  "SHOW shared_buffers; SHOW max_connections; SHOW max_pool_size; SHOW work_mem;"

# 修改参数（需 reload 生效，shared_buffers 等需重启）
sudo sed -i "s/^shared_buffers.*/shared_buffers = 2GB/" /etc/opentenbase/<version>/postgresql.conf
sudo opentenbase-ctl reload coordinator
```

**注意**：`max_connections` 调大需同步评估内存是否够用，公式：`max_connections × 单连接内存 + shared_buffers < 物理内存 × 0.7`。盲目调大导致 OOM。

### 3. 索引检查

```bash
# 查找未被使用的索引（可考虑删除以提升写入性能）
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c \
  "SELECT schemaname, relname, indexrelname, idx_scan FROM pg_stat_user_indexes WHERE idx_scan = 0 ORDER BY pg_relation_size(indexrelid) DESC LIMIT 20;"

# 查找缺失索引的高频查询表（seq_scan 远大于 idx_scan）
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c \
  "SELECT relname, seq_scan, seq_tup_read, idx_scan FROM pg_stat_user_tables WHERE seq_scan > 100 AND seq_tup_read > 10000 ORDER BY seq_scan DESC;"
```

**判断标准**：`idx_scan = 0` 且表大的索引可考虑清理；`seq_scan` 高且无对应索引的表需建索引。

---

## 分布式定时任务管理（pg_cron）

OpenTenBase 支持通过 `pg_cron` 扩展管理分布式定时任务。

```bash
# 1. 确认 pg_cron 扩展已安装
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c \
  "SELECT * FROM pg_available_extensions WHERE name='pg_cron';"

# 2. 启用扩展（需超级用户）
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c "CREATE EXTENSION pg_cron;"

# 3. 创建定时任务（格式：分 时 日 月 周 命令）
# 每天凌晨 2 点清理历史日志表
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c \
  "SELECT cron.schedule('clean_logs', '0 2 * * *', 'DELETE FROM audit_log WHERE created_at < now() - interval ''30 days''');"

# 4. 查看已配置的任务
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c "SELECT jobid, schedule, command, active FROM cron.job;"

# 5. 查看任务执行历史
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c \
  "SELECT jobid, runid, status, return_message, start_time FROM cron.job_run_details ORDER BY start_time DESC LIMIT 20;"

# 6. 取消任务（替换 <jobid>）
opentenbase-psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c "SELECT cron.unschedule(<jobid>);"
```

**判断标准**：`status` 为 `succeeded` 正常；`failed` 需查 `return_message` 定位原因。`active = false` 表示任务已暂停。

---

## 运维红线

以下红线必须严格遵守，违反任何一条可能导致集群二次故障或数据丢失：

1. **不绕过 `opentenbase-ctl` 手动用 `nohup`/前台命令拉进程**。手动拉的进程绑定 SSH 会话，断开即死。所有启停必须通过 `opentenbase-ctl start/stop/restart`。
2. **`start` 返回 exit 1 后不立刻判失败**。先等 30-60 秒让 daemon 完成启动，用 `pgrep` 确认进程状态，再下结论。
3. **判定节点状态不能只看端口**。`status` 显示 STOPPED 不等于进程不存在，必须 `pgrep` 确认进程是否存活，综合判断。
4. **生产环境破坏性操作前必须确认**。`DROP`/`TRUNCATE`/`DELETE` 无 WHERE 等操作需二次确认，建议先 `SELECT` 预览影响范围。
5. **不跳过备份直接执行数据变更**。结构变更（DDL）或大批量 DML 前先备份相关表。
6. **不在未验证的情况下声明问题已解决**。操作后必须用 `pgrep` + `ss` + `opentenbase-psql` 三重验证。
7. **不手动 kill 进程后自行拉起**。需要停用 `opentenbase-ctl stop`，需要重启用 `opentenbase-ctl restart`。

---

## 程序辅助

当任务可程序化时，使用脚本辅助执行巡检与维护：

```bash
# 集群巡检（采集状态、进程、端口、连接数、慢查询）
python3 {baseDir}/scripts/otb_ops.py --action inspect --target <host>

# 性能优化（分析指定慢 SQL 的执行计划与索引建议）
python3 {baseDir}/scripts/otb_ops.py --action optimize --target <host> --query "<slow_sql>"

# 维护操作（VACUUM/ANALYZE/日志清理等）
python3 {baseDir}/scripts/otb_ops.py --action maintain --target <host>
```

不得把脚本报错隐藏成确定结论。脚本不覆盖的场景必须进行人工复核。脚本输出需与上方手工命令交叉验证。

---

## 必读参考

- OpenTenBase 官方文档：`https://github.com/OpenAtom-OpenTenBase/OpenTenBase`
- 部署源仓库：`https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages`
- 故障排除：`docs/05-troubleshoot.md`（仓库内）
- `{baseDir}/references/README.md`（本地补充资料目录，含运维手册/监控指标/调优指南建议文件清单）
