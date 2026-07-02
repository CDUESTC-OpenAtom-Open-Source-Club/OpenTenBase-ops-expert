---
name: opentenbase-monitoring-integration
description: 为已有 OpenTenBase 分布式集群接入 Prometheus、Grafana 和 postgres_exporter 监控。用于用户要求安装监控、采集 CN 指标、配置 Prometheus targets、创建 Grafana 数据源/面板、验证监控是否可用时。
version: 1.0.0
user-invocable: true
---

# OpenTenBase 监控接入

若目标在远程 Linux，先使用 `linux-ssh-access`。本 Skill 默认面向已安装、已启动或可启动的 OpenTenBase 集群。

## 默认目标

搭建最小可用监控链路：

```text
OpenTenBase CN
-> postgres_exporter
-> Prometheus
-> Grafana
```

第一版只覆盖二进制部署方式、CN 级采集、Prometheus 抓取、Grafana 数据源和基础面板。不默认部署 Docker、node_exporter、Loki、Alertmanager 或 systemd。

## 标准流程

1. 确认拓扑和监控主机：

```bash
hostname
ip addr
ss -lntp 2>/dev/null || ss -lnt 2>/dev/null
```

确认至少一个可连接 CN，优先列出所有 CN：

```bash
psql -h <cn_host> -p <cn_port> -U <db_user> -d <database> \
  -Atqc 'SELECT node_name,node_type,node_host,node_port FROM pgxc_node ORDER BY node_name;'
```

2. 检查依赖和端口：

```bash
command -v curl wget tar gzip nohup
ss -lntp 2>/dev/null | grep -E ':(3000|9090|9187|9188)\b' || true
```

3. 按需读取：

```text
references/binary-deploy.md
```

完成 postgres_exporter、Prometheus、Grafana 的二进制部署。

4. 遇到 postgres_exporter 默认指标卡住时，读取：

```text
references/postgres-exporter-opentenbase.md
```

关闭默认 collector，只启用 OpenTenBase 兼容的轻量自定义查询。

5. 验证：

```bash
curl -s http://127.0.0.1:<exporter_port>/metrics | grep -E 'pg_up|pg_exporter_last_scrape_error|otb_'
curl -s http://127.0.0.1:9090/-/ready
curl -s 'http://127.0.0.1:9090/api/v1/query?query=otb_pgxc_node_total_value'
curl -s http://127.0.0.1:3000/api/health
```

## 安全边界

默认不执行：

```text
数据库写操作
OpenTenBase 启停
配置修改
清理数据目录
安装系统服务
开放防火墙端口
配置告警通知
```

需要启动 OpenTenBase 时，改用 `opentenbase-cluster-ops`。需要日志排错时，改用 `opentenbase-log-error-analysis`。

## 成功标准

- 每个目标 CN 对应一个 postgres_exporter。
- exporter `/metrics` 中 `pg_up=1` 且 `pg_exporter_last_scrape_error=0`。
- Prometheus targets 为 `up`。
- Prometheus 能查询到 `otb_pgxc_node_total_value`。
- Grafana `/api/health` 返回 `database: ok`。
- Grafana 有 Prometheus 数据源和 OpenTenBase dashboard。

## 输出格式

```text
监控状态：可用 / 部分可用 / 失败
监控主机：<host>
CN 目标：<cn list>
Exporter：<port list and status>
Prometheus：<url and target status>
Grafana：<url and login info>
已验证指标：<pg_up / otb_pgxc_node_total_value / others>
问题：<仅异常时填写>
下一步：<截图 / 增加指标 / 接入 node_exporter / 告警>
```

