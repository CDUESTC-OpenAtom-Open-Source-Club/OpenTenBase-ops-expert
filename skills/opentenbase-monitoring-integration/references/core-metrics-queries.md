# OpenTenBase 核心健康指标采集

> 本文件解决一个实锤问题：基础版 `postgres-exporter-opentenbase.md` 的自定义查询只有 4 个**计数类**指标（节点数、库数），
> 而默认 collector 又被 `--no-collector.*` 全禁（因为在 OpenTenBase 上会卡）。
> 结果就是——**GTM 状态、连接数、复制延迟、锁等待、XID age、2PC 残留、长事务、膨胀 一个都没采**。
> 这比没监控更危险，会让人误以为"我已经有监控了"。
>
> 本文件用**纯自定义 SQL**（走 `--extend.query-path`，不依赖任何被禁的默认 collector）补齐生产 DBA 真正要盯的核心指标。
> 全部为**只读查询**，不改任何数据。

## 适用与前提

- 每个 CN 一个 exporter，本组指标追加进现有 `opentenbase-postgres-exporter-queries.yaml`。
- OpenTenBase 基于 PostgreSQL 10 内核，下列 SQL 已按 PG 10 系统视图列名编写（`pg_stat_activity.wait_event_type`、`backend_xid` 等均存在）。
- 采集账号只需 `pg_monitor` 角色或等价只读权限：
  ```sql
  -- 用超级用户执行一次，创建专用只读监控账号
  CREATE ROLE otb_monitor LOGIN PASSWORD '<strong_pwd>';
  GRANT pg_monitor TO otb_monitor;   -- PG 10 内置角色，可读 pg_stat_* / pg_locks 等
  ```
  之后 `DATA_SOURCE_NAME` 用 `otb_monitor` 连接，避免用超级用户跑监控。

## 核心指标自定义查询

把以下内容**追加**到 `/opt/otb-monitor/conf/opentenbase-postgres-exporter-queries.yaml`（保留原有 `otb_up` 等 4 项，不要删）：

```yaml
# ---------- 连接与会话 ----------
otb_connections:
  query: >
    SELECT
      count(*)::float AS total,
      count(*) FILTER (WHERE state = 'active')::float AS active,
      count(*) FILTER (WHERE state = 'idle')::float AS idle,
      count(*) FILTER (WHERE state = 'idle in transaction')::float AS idle_in_txn,
      count(*) FILTER (WHERE wait_event_type = 'Lock')::float AS waiting_on_lock
    FROM pg_stat_activity
    WHERE backend_type = 'client backend' OR backend_type IS NULL
  metrics:
    - total:            {usage: "GAUGE", description: "当前总连接数"}
    - active:           {usage: "GAUGE", description: "活跃连接数"}
    - idle:             {usage: "GAUGE", description: "空闲连接数"}
    - idle_in_txn:      {usage: "GAUGE", description: "idle in transaction 连接数（泄露/长事务征兆）"}
    - waiting_on_lock:  {usage: "GAUGE", description: "正在等待锁的连接数"}

otb_max_connections:
  query: "SELECT setting::float AS value FROM pg_settings WHERE name = 'max_connections'"
  metrics:
    - value: {usage: "GAUGE", description: "max_connections 上限（配合 otb_connections_total 算使用率）"}

# ---------- 长事务 / 空闲事务（膨胀与阻塞的源头） ----------
otb_longest_transaction_seconds:
  query: >
    SELECT COALESCE(EXTRACT(EPOCH FROM (now() - min(xact_start))), 0)::float AS value
    FROM pg_stat_activity
    WHERE state <> 'idle' AND xact_start IS NOT NULL
  metrics:
    - value: {usage: "GAUGE", description: "当前最长事务已运行秒数"}

otb_longest_idle_in_txn_seconds:
  query: >
    SELECT COALESCE(EXTRACT(EPOCH FROM (now() - min(state_change))), 0)::float AS value
    FROM pg_stat_activity
    WHERE state = 'idle in transaction'
  metrics:
    - value: {usage: "GAUGE", description: "最长 idle in transaction 秒数（会卡住 autovacuum 回收）"}

# ---------- XID 回卷风险（数据库拒绝写入的头号杀手） ----------
otb_database_xid_age:
  query: >
    SELECT datname, age(datfrozenxid)::float AS age
    FROM pg_database WHERE datallowconn
  metrics:
    - datname: {usage: "LABEL", description: "数据库名"}
    - age:     {usage: "GAUGE", description: "库级 datfrozenxid age（接近 autovacuum_freeze_max_age≈2亿 需告警）"}

otb_max_table_xid_age:
  query: >
    SELECT COALESCE(max(age(relfrozenxid)), 0)::float AS value
    FROM pg_class WHERE relkind IN ('r','m','t')
  metrics:
    - value: {usage: "GAUGE", description: "全库最大表级 relfrozenxid age（更细粒度的回卷风险）"}

# ---------- 2PC 残留（分布式事务未清理，会长期占用 XID / 持锁） ----------
otb_prepared_xacts:
  query: >
    SELECT
      count(*)::float AS total,
      COALESCE(EXTRACT(EPOCH FROM (now() - min(prepared))), 0)::float AS oldest_seconds
    FROM pg_prepared_xacts
  metrics:
    - total:          {usage: "GAUGE", description: "prepared（2PC）事务残留数量，正常应为 0"}
    - oldest_seconds: {usage: "GAUGE", description: "最老 prepared 事务存活秒数"}

# ---------- 复制延迟（CN/DN 主备流复制） ----------
# 说明：exporter 连的是本 CN，这里查的是「以本节点为主库」的下游备机延迟。
# 若备机未连接则无行输出（指标缺失即代表可能断流，配合 count 告警）。
otb_replication:
  query: >
    SELECT
      COALESCE(client_addr::text, 'local') AS replica,
      state,
      COALESCE(EXTRACT(EPOCH FROM (now() - reply_time)), 0)::float AS reply_lag_seconds,
      COALESCE(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn), 0)::float AS replay_lag_bytes
    FROM pg_stat_replication
  metrics:
    - replica:            {usage: "LABEL", description: "备机地址"}
    - state:              {usage: "LABEL", description: "复制状态 streaming/catchup 等"}
    - reply_lag_seconds:  {usage: "GAUGE", description: "备机回包延迟秒数"}
    - replay_lag_bytes:   {usage: "GAUGE", description: "备机回放落后主库的 WAL 字节数"}

otb_replication_client_count:
  query: "SELECT count(*)::float AS value FROM pg_stat_replication"
  metrics:
    - value: {usage: "GAUGE", description: "已连接备机数量（掉到 0 = 无备机/断流）"}

# ---------- 膨胀与回收（死元组） ----------
otb_dead_tuples:
  query: >
    SELECT COALESCE(sum(n_dead_tup), 0)::float AS total,
           COALESCE(max(n_dead_tup), 0)::float AS max_single
    FROM pg_stat_user_tables
  metrics:
    - total:      {usage: "GAUGE", description: "全库死元组总数"}
    - max_single: {usage: "GAUGE", description: "单表最大死元组数（膨胀热点）"}

# ---------- 磁盘 / 数据库体积 ----------
otb_database_size_bytes:
  query: >
    SELECT datname, pg_database_size(datname)::float AS size
    FROM pg_database WHERE datallowconn
  metrics:
    - datname: {usage: "LABEL", description: "数据库名"}
    - size:    {usage: "GAUGE", description: "数据库磁盘占用字节"}

# ---------- 缓存命中 / 事务吞吐 ----------
otb_db_stats:
  query: >
    SELECT
      COALESCE(sum(xact_commit), 0)::float AS xact_commit,
      COALESCE(sum(xact_rollback), 0)::float AS xact_rollback,
      COALESCE(sum(blks_hit), 0)::float AS blks_hit,
      COALESCE(sum(blks_read), 0)::float AS blks_read,
      COALESCE(sum(deadlocks), 0)::float AS deadlocks
    FROM pg_stat_database WHERE datname NOT IN ('template0','template1')
  metrics:
    - xact_commit:   {usage: "COUNTER", description: "累计提交事务数"}
    - xact_rollback: {usage: "COUNTER", description: "累计回滚事务数"}
    - blks_hit:      {usage: "COUNTER", description: "缓存命中块数"}
    - blks_read:     {usage: "COUNTER", description: "磁盘读块数"}
    - deadlocks:     {usage: "COUNTER", description: "累计死锁次数"}
```

## 重新启动 exporter（保持默认 collector 关闭）

沿用基础版的 `COMMON_FLAGS`（`--disable-default-metrics` + 各 `--no-collector.*`），
只需确保 `--extend.query-path` 指向已追加新指标的同一个 yaml，重启即可：

```bash
# 停掉旧 exporter
pkill -f 'postgres_exporter.*:9187' || true
# 用只读监控账号重启（示例 CN1）
nohup env DATA_SOURCE_NAME='postgresql://otb_monitor@<cn1_host>:<cn1_port>/<database>?sslmode=disable' \
  /opt/otb-monitor/postgres_exporter/postgres_exporter \
  --web.listen-address=:9187 \
  $COMMON_FLAGS \
  >/opt/otb-monitor/logs/postgres_exporter_cn1.log 2>&1 &
```

## 验证新指标已输出

```bash
curl -s http://127.0.0.1:9187/metrics | grep -E \
 'otb_connections_|otb_max_connections|otb_longest_|otb_database_xid_age|otb_max_table_xid_age|otb_prepared_xacts|otb_replication|otb_dead_tuples|otb_database_size|otb_db_stats'
```

任何一条自定义 SQL 若 `psql` 单独执行报错，`/metrics` 里对应指标会缺失、且 `pg_exporter_last_scrape_error 1`。
先用 `psql` 单独跑那条 SQL 排错，通常是列名版本差异或权限不足。

## Prometheus 告警规则（可选，强烈建议）

写入 `/opt/otb-monitor/prometheus/rules/opentenbase.rules.yml`，在 `prometheus.yml` 里 `rule_files` 引用后 reload：

```yaml
groups:
- name: opentenbase-core
  rules:
  # —— 可用性 ——
  - alert: OTB_CN_Down
    expr: pg_up == 0
    for: 1m
    labels: {severity: critical}
    annotations: {summary: "CN {{ $labels.instance }} 不可达（pg_up=0）"}

  - alert: OTB_ScrapeError
    expr: pg_exporter_last_scrape_error == 1
    for: 5m
    labels: {severity: warning}
    annotations: {summary: "exporter {{ $labels.instance }} 采集出错，指标可能失真"}

  # —— XID 回卷（最高优先级，触发即数据库将拒绝写入） ——
  - alert: OTB_XID_Wraparound_Warning
    expr: otb_database_xid_age_age > 150000000
    for: 10m
    labels: {severity: warning}
    annotations: {summary: "库 {{ $labels.datname }} XID age={{ $value }} 逼近回卷，尽快 VACUUM FREEZE"}

  - alert: OTB_XID_Wraparound_Critical
    expr: otb_database_xid_age_age > 1800000000
    for: 1m
    labels: {severity: critical}
    annotations: {summary: "库 {{ $labels.datname }} XID age 极度危险，数据库即将进入只读保护"}

  # —— 连接数使用率 ——
  - alert: OTB_Connections_High
    expr: otb_connections_total / otb_max_connections_value > 0.85
    for: 5m
    labels: {severity: warning}
    annotations: {summary: "CN {{ $labels.instance }} 连接使用率 >85%"}

  # —— 2PC 残留 ——
  - alert: OTB_Prepared_Xact_Stuck
    expr: otb_prepared_xacts_oldest_seconds > 600
    for: 5m
    labels: {severity: warning}
    annotations: {summary: "存在 >10min 未清理的 2PC 事务，检查分布式事务与 GTM"}

  # —— 复制断流 / 延迟 ——
  - alert: OTB_Replication_Down
    expr: otb_replication_client_count_value == 0
    for: 3m
    labels: {severity: critical}
    annotations: {summary: "{{ $labels.instance }} 无备机连接，主备复制可能中断"}

  - alert: OTB_Replication_Lag_High
    expr: otb_replication_replay_lag_bytes > 268435456   # 256MB
    for: 5m
    labels: {severity: warning}
    annotations: {summary: "备机 {{ $labels.replica }} 回放落后 >256MB"}

  # —— 长事务 / idle in txn（膨胀源头） ——
  - alert: OTB_Long_Transaction
    expr: otb_longest_transaction_seconds_value > 1800
    for: 5m
    labels: {severity: warning}
    annotations: {summary: "存在 >30min 长事务，阻塞 autovacuum 回收"}

  - alert: OTB_Idle_In_Transaction
    expr: otb_longest_idle_in_txn_seconds_value > 600
    for: 5m
    labels: {severity: warning}
    annotations: {summary: "存在 >10min idle in transaction，可能是应用未提交/连接泄露"}
```

> 阈值按经验给的保守默认值，生产环境请按实际容量调整。`autovacuum_freeze_max_age` 默认约 2 亿，
> 150000000（1.5 亿）留出充足处置窗口；18 亿是接近 21 亿硬上限前的最后红线。

## 分布式采集的重要局限（必须向用户说明）

- exporter 连的是 **CN**，`pg_stat_replication` 只反映**以该 CN 为主库**的下游备机。
- **DN 的主备复制延迟 / DN 本地 XID age** 不会出现在 CN 的查询里。要完整覆盖，需**对每个 DN 主节点也部署一个 exporter**（同一份 yaml、不同 `DATA_SOURCE_NAME` 和端口）。
- GTM 无 SQL 接口，其存活只能靠 `linux-ssh-access` + 进程/端口探测（`ss -lntp | grep <gtm_port>`），不在本 exporter 覆盖范围。
- 因此"监控齐全"的标准是：**每个 CN + 每个 DN 主节点各一个 exporter**，GTM 用外部端口探测补齐。
