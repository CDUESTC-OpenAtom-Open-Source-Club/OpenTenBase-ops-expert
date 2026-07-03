---
name: opentenbase-monitoring-integration
description: 为已有 OpenTenBase 分布式集群接入 Prometheus、Grafana 和 postgres_exporter 监控。用于用户要求安装监控、采集 CN 指标、配置 Prometheus targets、创建 Grafana 数据源/面板、验证监控是否可用时。
version: 1.1.0
author: CDUESTC OpenAtom Open Source Club
tools: [shell, filesystem, http]
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

覆盖二进制部署方式、CN 级采集、Prometheus 抓取、Grafana 数据源和面板。基础链路通后，可按需追加核心健康指标（连接数/复制延迟/锁/XID age/长事务/2PC，见 `references/core-metrics-queries.md`）与告警规则。不默认部署 Docker、node_exporter、Loki、Alertmanager 或 systemd。

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

5. **采集核心健康指标（不要停在"节点计数"）**：基础自定义查询只有节点数/库数等计数指标，看不见业务健康。用户要"能用于生产的监控"、要看连接数/复制延迟/锁/XID age/长事务/2PC 时，读取：

```text
references/core-metrics-queries.md
```

追加连接数、长事务、XID 回卷风险、2PC 残留、复制延迟、死元组、库体积等只读指标，并按需配置 Prometheus 告警规则。**注意分布式局限：exporter 连的是 CN，DN 的复制延迟/XID age 需对每个 DN 主节点单独部署 exporter；GTM 无 SQL 接口，靠端口探测补齐。**

6. 验证：

```bash
curl -s http://127.0.0.1:<exporter_port>/metrics | grep -E 'pg_up|pg_exporter_last_scrape_error|otb_'
curl -s http://127.0.0.1:9090/-/ready
curl -s 'http://127.0.0.1:9090/api/v1/query?query=otb_pgxc_node_total_value'
curl -s http://127.0.0.1:3000/api/health
```

## 使用示例

**示例 1：接入基础监控**

> 用户：帮我的 OpenTenBase CN 接上 Prometheus + Grafana
>
> Agent：好的。先确认：CN 在 192.168.1.10:11003 可用吗？监控组件部署在同一台机器上？
>
> 用户：是的，都在这台上
>
> Agent：（下载并部署 postgres_exporter、Prometheus、Grafana，配置采集 CN 指标）
> ✅ 监控已就绪：
> - postgres_exporter: http://192.168.1.10:9187/metrics
> - Prometheus: http://192.168.1.10:9090 （targets 全部 UP）
> - Grafana: http://192.168.1.10:3000 （admin / 初始密码已生成）

**示例 2：检查监控状态**

> 用户：监控还在跑吗？
>
> Agent：（检查各组件运行状态和指标）
> ✅ 全部正常：
> - postgres_exporter: pg_up=1, scrape_error=0
> - Prometheus: /-/ready OK
> - Grafana: database OK
> - 最新指标：otb_pgxc_node_total_value=3

---

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

- 每个目标 CN 对应一个 postgres_exporter（生产完整覆盖时每个 DN 主节点也各一个）。
- exporter `/metrics` 中 `pg_up=1` 且 `pg_exporter_last_scrape_error=0`。
- Prometheus targets 为 `up`。
- Prometheus 能查询到 `otb_pgxc_node_total_value`。
- **核心健康指标可用**（用户要生产级监控时）：连接数、长事务、`otb_database_xid_age`、`otb_prepared_xacts`、`otb_replication` 等已在 `/metrics` 输出，关键告警规则已加载。
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

