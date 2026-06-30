# postgres_exporter 与 OpenTenBase

## 关键兼容点

VERIFIED：

- postgres_exporter 可以连接 OpenTenBase CN。
- 默认 collector 在当前实验环境可能导致 `/metrics` 卡住或超时。
- 关闭默认 collector 并使用轻量自定义 SQL 后，两个 CN 可稳定输出指标。

## 自定义查询

`/opt/otb-monitor/conf/opentenbase-postgres-exporter-queries.yaml`：

```yaml
otb_up:
  query: "SELECT 1::float AS value"
  metrics:
    - value:
        usage: "GAUGE"
        description: "OpenTenBase CN connection check"

otb_pgxc_node_total:
  query: "SELECT count(*)::float AS value FROM pgxc_node"
  metrics:
    - value:
        usage: "GAUGE"
        description: "OpenTenBase pgxc_node total count"

otb_pgxc_node_by_type:
  query: "SELECT node_type, count(*)::float AS count FROM pgxc_node GROUP BY node_type"
  metrics:
    - node_type:
        usage: "LABEL"
        description: "OpenTenBase pgxc_node node type"
    - count:
        usage: "GAUGE"
        description: "OpenTenBase pgxc_node count by type"

otb_database_total:
  query: "SELECT count(*)::float AS value FROM pg_database WHERE datistemplate = false"
  metrics:
    - value:
        usage: "GAUGE"
        description: "OpenTenBase non-template database count"
```

## 启动 exporter

每个 CN 一个 exporter，端口不要重复：

```bash
COMMON_FLAGS="\
--disable-default-metrics \
--disable-settings-metrics \
--no-collector.database \
--no-collector.locks \
--no-collector.replication \
--no-collector.replication_slot \
--no-collector.stat_bgwriter \
--no-collector.stat_database \
--no-collector.stat_user_tables \
--no-collector.statio_user_tables \
--no-collector.wal \
--extend.query-path=/opt/otb-monitor/conf/opentenbase-postgres-exporter-queries.yaml"
```

CN1：

```bash
nohup env DATA_SOURCE_NAME='postgresql://<db_user>@<cn1_host>:<cn1_port>/<database>?sslmode=disable' \
  /opt/otb-monitor/postgres_exporter/postgres_exporter \
  --web.listen-address=:9187 \
  $COMMON_FLAGS \
  >/opt/otb-monitor/logs/postgres_exporter_cn1.log 2>&1 &
```

CN2：

```bash
nohup env DATA_SOURCE_NAME='postgresql://<db_user>@<cn2_host>:<cn2_port>/<database>?sslmode=disable' \
  /opt/otb-monitor/postgres_exporter/postgres_exporter \
  --web.listen-address=:9188 \
  $COMMON_FLAGS \
  >/opt/otb-monitor/logs/postgres_exporter_cn2.log 2>&1 &
```

## 验证

```bash
curl -s http://127.0.0.1:9187/metrics | grep -E 'pg_up|pg_exporter_last_scrape_error|otb_'
curl -s http://127.0.0.1:9188/metrics | grep -E 'pg_up|pg_exporter_last_scrape_error|otb_'
```

成功示例：

```text
pg_up 1
pg_exporter_last_scrape_error 0
otb_up_value 1
otb_pgxc_node_total_value 5
otb_pgxc_node_by_type_count{node_type="C"} 2
otb_pgxc_node_by_type_count{node_type="D"} 2
otb_pgxc_node_by_type_count{node_type="G"} 1
```

## 排错

- `/metrics` 卡住：确认已关闭默认 collector。
- `pg_up 0`：检查 CN 地址、端口、用户、数据库和 `pg_hba.conf`。
- `last_scrape_error 1`：查看 exporter 日志，优先检查自定义 SQL 是否能用 `psql` 单独执行。
- Prometheus target down：先从监控主机 `curl http://127.0.0.1:<exporter_port>/metrics`。

