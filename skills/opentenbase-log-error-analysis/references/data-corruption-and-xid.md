# XID 回卷、autovacuum 停摆、表膨胀与磁盘满：数据库拒绝写入类故障

这一类故障的共同表现是：**数据库突然拒绝写入、报错停摆，但进程还在、端口还通**。它们不是连接问题，日志关键字很明确，是生产库最危险的一类，必须能第一时间识别。分布式集群下要**逐 DN / CN 排查**，任一节点触发都会影响全局。

---

## 1. XID 回卷（事务 ID 耗尽）—— 最高危

### 日志/报错特征
```
WARNING:  database "xxx" must be vacuumed within N transactions
HINT:  To avoid a database shutdown, execute a database-wide VACUUM in that database.
ERROR:  database is not accepting commands to avoid wraparound data loss in database "xxx"
```
出现第二条时，该节点已**拒绝一切写入**（只读都可能受限），属于最高优先级事故。

### 根因
PostgreSQL/OpenTenBase 用 32 位事务 ID，靠 autovacuum 周期性 freeze 老元组来回收 XID 空间。一旦 autovacuum 长期没跑到（被关掉、被长事务/长期未提交的 2PC 阻塞、写入量极大），XID age 逼近 20 亿上限，数据库主动停写自保。

### 只读定位（每个节点都要查）
```sql
-- 库级 XID age，datfrozenxid 越大越危险（接近 autovacuum_freeze_max_age，默认 2 亿）
SELECT datname, age(datfrozenxid) AS xid_age
FROM pg_database ORDER BY xid_age DESC;

-- 表级 age，定位到底是哪张表拖住了 freeze
SELECT relname, age(relfrozenxid) AS xid_age
FROM pg_class WHERE relkind='r' ORDER BY xid_age DESC LIMIT 20;

-- 是否有长事务 / 未提交 2PC 阻塞 freeze（分布式尤其常见）
SELECT pid, state, xact_start, now()-xact_start AS dur, query
FROM pg_stat_activity WHERE state <> 'idle' ORDER BY xact_start LIMIT 10;
SELECT gid, prepared, owner, database FROM pg_prepared_xacts ORDER BY prepared;
```

### 处置方向（写操作，需用户确认）
- 已停写：对告警库执行 `VACUUM`（必要时 `VACUUM FREEZE`）回收 XID；大表可先针对性 vacuum 高 age 表。
- 先清障：结束阻塞 freeze 的长事务、`COMMIT/ROLLBACK PREPARED` 处理悬挂 2PC，否则 vacuum 追不上。
- 治本：恢复 autovacuum（见第 2 节），把 XID age 纳入日常巡检与监控告警。

> 分布式提醒：回卷是**逐节点**发生的。修一个 DN 不够，要对每个库/每个节点都查 age 并处理。

---

## 2. autovacuum 停摆 / 被抑制

### 现象
表膨胀持续变大、XID age 不断上涨、慢查询变多，但看不到明显 ERROR——属于"温水煮青蛙"型。

### 只读定位
```sql
SHOW autovacuum;                       -- 是否被关成 off
-- 各表死元组、最近一次 (auto)vacuum/analyze 时间
SELECT relname, n_live_tup, n_dead_tup,
       last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 20;
-- 是否有 worker 正卡在某张大表上
SELECT pid, query, now()-query_start AS dur
FROM pg_stat_activity WHERE query ILIKE '%autovacuum%';
```

### 常见根因
- 被显式关闭（`autovacuum = off`）或单表 `autovacuum_enabled=false`。
- 长事务 / 悬挂 2PC 持有旧快照，使 vacuum 无法回收 → dead_tup 回收不掉。
- `autovacuum_max_workers` 太少、`cost_delay` 太保守，追不上高写入。

### 处置方向（需确认）
- 打开 autovacuum；对高 dead_tup 表手动 `VACUUM (ANALYZE)`。
- 清掉长事务与悬挂 2PC。
- 高写入库调 `autovacuum_max_workers` / `autovacuum_vacuum_cost_delay` / `*_scale_factor`。

---

## 3. 表 / 索引膨胀（bloat）

### 现象
磁盘占用与实际数据量严重不符；全表扫描变慢；`n_dead_tup` 长期居高。

### 只读定位
```sql
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) AS total,
       n_live_tup, n_dead_tup,
       round(n_dead_tup*100.0/nullif(n_live_tup+n_dead_tup,0),1) AS dead_pct
FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 20;
```

### 处置方向（需确认，注意锁）
- 轻度：`VACUUM (ANALYZE)` 回收可复用空间（不还盘给 OS）。
- 重度：`VACUUM FULL`（**持表级排它锁、期间不可用**，业务低峰做）或用 `pg_repack` 在线重建。
- 索引膨胀：`REINDEX`（分布式下逐节点评估影响）。
- 分布式提醒：膨胀发生在各 DN 本地，`VACUUM FULL` 要评估对整个分片查询的影响。

---

## 4. 磁盘 / WAL 空间满

### 日志特征
```
ERROR: could not extend file ... No space left on device
PANIC: could not write to file "pg_wal/..." No space left on device
```
`pg_wal` 写不下会直接 PANIC 使节点崩溃，非常危险。

### 只读定位
```bash
df -h                      # 数据盘 / WAL 盘
du -sh <data_dir>/pg_wal   # WAL 是否异常堆积
```
```sql
-- WAL 堆积常见于归档失败或复制槽卡住
SELECT * FROM pg_stat_archiver;                 -- failed_count 是否在涨
SELECT slot_name, active, restart_lsn FROM pg_replication_slots;  -- 有无失效槽拖住 WAL 回收
```

### 处置方向（需确认）
- 先扩容 / 清理**非数据库**文件腾出应急空间，切忌手删 `pg_wal` 里的文件。
- 归档失败：修复 `archive_command` / 归档目标，让 WAL 能正常回收。
- 失效复制槽：确认无用后 `pg_drop_replication_slot` 释放被它 pin 住的 WAL。

---

## 排查次序建议

1. 看日志关键字先归类：`wraparound / must be vacuumed`（→ 第1节）、`No space left`（→ 第4节）、无 ERROR 但变慢（→ 第2/3节）。
2. XID 回卷和磁盘满是**会停库/崩库**的，最高优先，先止血。
3. 所有处置前先做只读定位，写操作（VACUUM FULL / REINDEX / drop slot / 处理 2PC）一律先向用户说明影响并确认。
4. 分布式集群：每一类都要**逐节点**确认，不要只修报错的那台。
