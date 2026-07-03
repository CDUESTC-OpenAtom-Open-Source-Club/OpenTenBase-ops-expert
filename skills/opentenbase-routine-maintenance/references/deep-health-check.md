# 深度健康巡检（P0 隐患提前发现）

本文件是每日/每周巡检的**深度补充**，全部为只读 SQL，不做任何修复。
目的：在数据库还没报错停摆之前，提前发现 XID 回卷、autovacuum 停摆、长事务、2PC 残留、复制延迟、表膨胀这几类**会导致停库或严重性能事故**的隐患。
发现异常只报告并给出处置方向（详见 `opentenbase-log-error-analysis` 的 `references/data-corruption-and-xid.md`），修复动作交由用户确认后执行。

分布式提醒：以下检查在 CN 上能看到全局的 `pgxc_node`，但 **XID age、死元组、膨胀是各节点本地状态**，条件允许时应逐 DN/CN 采集，不能只看一个节点。

---

## 1. XID age（防事务回卷，最高优先）

```sql
-- 库级：age 越接近 autovacuum_freeze_max_age（默认 2 亿）越危险，逼近 20 亿会强制停写
SELECT datname, age(datfrozenxid) AS xid_age
FROM pg_database ORDER BY xid_age DESC;

-- 表级：定位拖住 freeze 的具体表
SELECT relname, age(relfrozenxid) AS xid_age
FROM pg_class WHERE relkind='r' ORDER BY xid_age DESC LIMIT 10;
```

判读阈值参考：
- `xid_age < 2 亿`：正常。
- `2 亿 ~ 10 亿`：关注，检查 autovacuum 是否正常、有无长事务/2PC 阻塞 freeze。
- `> 10 亿`：**告警**，尽快安排 VACUUM，避免逼近停写线。

## 2. autovacuum 与死元组

```sql
SHOW autovacuum;   -- 不应为 off
SELECT relname, n_live_tup, n_dead_tup, last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC LIMIT 10;
```

关注：`autovacuum=off`、`last_autovacuum` 长期为空/很旧、`n_dead_tup` 持续走高。

## 3. 长事务与空闲事务（会阻塞 freeze 和 vacuum 回收）

```sql
SELECT pid, state, now()-xact_start AS xact_age,
       now()-query_start AS query_age, left(query,80) AS query
FROM pg_stat_activity
WHERE state <> 'idle' AND xact_start IS NOT NULL
ORDER BY xact_start LIMIT 10;
```

关注：`xact_age` 超过数小时的事务、`idle in transaction` 长期挂起的连接。

## 4. 分布式 2PC 残留（悬挂 prepared 事务）

```sql
SELECT gid, prepared, now()-prepared AS age, owner, database
FROM pg_prepared_xacts ORDER BY prepared;
```

正常应为空。存在长期悬挂的 prepared 事务会阻塞 vacuum、拖住 XID 回收，并破坏跨节点一致性——需人工核对后 `COMMIT/ROLLBACK PREPARED` 处理。

## 5. 复制延迟（主备高可用健康）

```sql
-- 在主节点查看各备节点延迟
SELECT client_addr, state, sync_state,
       pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS replay_lag_bytes
FROM pg_stat_replication;

-- 复制槽是否有失效槽在拖住 WAL 回收
SELECT slot_name, active, pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) AS retained_bytes
FROM pg_replication_slots ORDER BY retained_bytes DESC;
```

关注：`replay_lag_bytes` 持续增大、`state` 非 `streaming`、存在 `active=false` 但仍 pin 住大量 WAL 的槽。

## 6. 连接水位与锁等待

```sql
SELECT count(*) AS conns, (SELECT setting::int FROM pg_settings WHERE name='max_connections') AS max_conns
FROM pg_stat_activity;

-- 是否有被阻塞的锁等待
SELECT bl.pid AS blocked_pid, ka.pid AS blocking_pid,
       left(bl_act.query,60) AS blocked_query
FROM pg_locks bl
JOIN pg_stat_activity bl_act ON bl_act.pid = bl.pid
JOIN pg_locks kl ON kl.locktype=bl.locktype AND kl.relation IS NOT DISTINCT FROM bl.relation AND kl.granted
JOIN pg_stat_activity ka ON ka.pid = kl.pid
WHERE NOT bl.granted LIMIT 10;
```

关注：连接数逼近 `max_connections`、存在长时间锁等待链。

## 7. WAL 归档健康（有开归档时）

```sql
SELECT archived_count, failed_count, last_archived_time, last_failed_time
FROM pg_stat_archiver;
```

`failed_count` 持续增长说明归档失败，WAL 会堆积、PITR 链会断——需尽快修 `archive_command` 或归档目标。

---

## 巡检结论输出建议

对以上每项给出"正常 / 关注 / 告警"三档，并对"关注/告警"项标注：受影响节点、当前值、建议处置方向（引用 log-error 的 data-corruption-and-xid.md）。不要在巡检阶段直接执行 VACUUM / 处理 2PC / drop slot 等写操作。
