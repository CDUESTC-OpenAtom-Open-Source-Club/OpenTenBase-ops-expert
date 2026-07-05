---
name: opentenbase-monitoring-integration
description: 为已有 OpenTenBase 分布式集群接入 Prometheus、Grafana 和 postgres_exporter 监控。用于用户要求安装监控、采集 CN 指标、配置 Prometheus targets、创建 Grafana 数据源/面板、验证监控是否可用时。
allowed-tools:
  - shell
  - http
metadata:
  version: 1.1.0
  author: CDUESTC OpenAtom Open Source Club
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

## 前置：确认 OpenTenBase 运行用户与连接路径

执行 `psql`、`pg_dump` 等工具前必须切换为 OpenTenBase 运行用户。不要在 root 下直接操作。

```bash
su - opentenbase
whoami
```

导出 OpenTenBase 工具链到 PATH（根据实际安装路径调整）：

```bash
export PGHOME=/var/lib/opentenbase/install/opentenbase/5.0
export PATH=$PGHOME/bin:$PATH
export LD_LIBRARY_PATH=$PGHOME/lib:$LD_LIBRARY_PATH
```

## 标准流程

### 1. 确认拓扑和监控主机

```bash
hostname
ip addr
ss -lntp 2>/dev/null || ss -lnt 2>/dev/null
```

确认至少一个可连接 CN：

```bash
psql -h <cn_host> -p <cn_port> -U <db_user> -d <database> \
  -Atqc 'SELECT node_name,node_type,node_host,node_port FROM pgxc_node ORDER BY node_name;'
```

### 2. 检查依赖和端口

```bash
command -v curl tar gzip nohup
ss -lntp 2>/dev/null | grep -E ':(3000|9090|9187|9188)\b' || true
```

### 3. 解决中国服务器下载慢的问题

默认下载源（GitHub / Grafana 官方）在中国大陆可能极慢或超时。尝试以下来源：

```bash
# 策略 1：使用镜像代理（推荐）
export GH_PROXY=https://ghproxy.1888866.xyz/

export PG_EXPORTER_URL="https://github.com/prometheus-community/postgres_exporter/releases/download/v0.15.0/postgres_exporter-0.15.0.linux-amd64.tar.gz"
export PROM_URL="https://github.com/prometheus/prometheus/releases/download/v2.53.1/prometheus-2.53.1.linux-amd64.tar.gz"
export GRAFANA_URL="https://dl.grafana.com/oss/release/grafana-10.4.2.linux-amd64.tar.gz"

# 用代理下载
curl -sL -o postgres_exporter.tar.gz "${GH_PROXY}$PG_EXPORTER_URL"
curl -sL -o prometheus.tar.gz "${GH_PROXY}$PROM_URL"
curl -sL -o grafana.tar.gz "${GRAFANA_URL}"   # Grafana 国内直连通常可用

# 策略 2：清华大学镜像（Prometheus）
# https://mirrors.tuna.tsinghua.edu.cn/github-release/prometheus/prometheus/v2.53.1/prometheus-2.53.1.linux-amd64.tar.gz

# 策略 3：离线传包
# 本地下载后 SCP 上传：scp /path/to/files.tar.gz root@<host>:/opt/otb-monitor/downloads/
```

下载后必须验证完整性：

```bash
ls -lh *.tar.gz
tar -tzf postgres_exporter.tar.gz >/dev/null && echo "postgres_exporter VALID" || echo "postgres_exporter CORRUPT"
tar -tzf prometheus.tar.gz >/dev/null && echo "prometheus VALID" || echo "prometheus CORRUPT"
tar -tzf grafana.tar.gz >/dev/null && echo "grafana VALID" || echo "grafana CORRUPT"
```

### 4. 部署 postgres_exporter（最小必须）

postgres_exporter 是唯一必须的组件。Prometheus + Grafana 可选后续补充。

读取 `references/binary-deploy.md` 完成全部组件的二进制部署。

**关键：postgres_exporter 启动时，必须添加 LD_LIBRARY_PATH 指向 OpenTenBase 的 lib 目录，否则 libpq 版本不匹配会连接失败：**

```bash
# 确定 OpenTenBase lib 路径
export PGHOME=/var/lib/opentenbase/install/opentenbase/5.0
export DATA_SOURCE_NAME="postgresql://opentenbase@127.0.0.1:11003/postgres?sslmode=disable"

nohup env LD_LIBRARY_PATH=$PGHOME/lib:$LD_LIBRARY_PATH \
  DATA_SOURCE_NAME="$DATA_SOURCE_NAME" \
  /opt/otb-monitor/postgres_exporter/postgres_exporter \
  --web.listen-address=:9187 \
  --disable-default-metrics \
  --disable-settings-metrics \
  --extend.query-path=/opt/otb-monitor/conf/opentenbase-postgres-exporter-queries.yaml \
  > /opt/otb-monitor/logs/postgres_exporter.log 2>&1 &

sleep 2
# 快速验证
curl -s http://127.0.0.1:9187/metrics | grep -E 'pg_up|otb_|pg_exporter_last_scrape_error'
```

遇到默认指标卡住时，读取 `references/postgres-exporter-opentenbase.md` 了解优化方案。

### 5. 部署 Prometheus（可选）

读取 `references/binary-deploy.md` 完成配置和启动。

### 6. 部署 Grafana（可选）

读取 `references/binary-deploy.md` 完成配置和启动。

### 7. 全链路验证

```bash
echo "=== postgres_exporter ==="
curl -s http://127.0.0.1:9187/metrics | grep -E 'pg_up|pg_exporter_last_scrape_error|otb_'

echo "=== Prometheus ==="
curl -s http://127.0.0.1:9090/-/ready
curl -s 'http://127.0.0.1:9090/api/v1/query?query=otb_pgxc_node_total_value'

echo "=== Grafana ==="
curl -s http://127.0.0.1:3000/api/health
```

### 8. 退出前清理环境（避免泄露 DATA_SOURCE_NAME）

```bash
unset DATA_SOURCE_NAME
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
> 监控已就绪：
> - postgres_exporter: http://192.168.1.10:9187/metrics
> - Prometheus: http://192.168.1.10:9090 （targets 全部 UP）
> - Grafana: http://192.168.1.10:3000 （admin / 初始密码已生成）

**示例 2：检查监控状态**

> 用户：监控还在跑吗？
>
> Agent：（检查各组件运行状态和指标）
> 全部正常：
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
