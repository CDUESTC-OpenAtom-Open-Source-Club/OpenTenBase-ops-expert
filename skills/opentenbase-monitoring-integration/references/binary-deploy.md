# 二进制部署流程

适用于没有 Docker、但可以下载二进制包的 Linux 环境。以下命令默认在监控主机执行。

## 目录

```bash
mkdir -p /opt/otb-monitor/{downloads,conf,logs,data}
cd /opt/otb-monitor/downloads
```

## 下载组件

默认下载源（GitHub / Grafana 官方）在中国大陆可能极慢或超时。优先使用镜像策略：

```bash
# 策略 1：ghproxy 代理（推荐，仅对 GitHub 资源使用）
export GH_PROXY="https://ghproxy.1888866.xyz/"

curl -sL -o postgres_exporter.tar.gz "${GH_PROXY}https://github.com/prometheus-community/postgres_exporter/releases/download/v0.15.0/postgres_exporter-0.15.0.linux-amd64.tar.gz"

curl -sL -o prometheus.tar.gz "${GH_PROXY}https://github.com/prometheus/prometheus/releases/download/v2.53.1/prometheus-2.53.1.linux-amd64.tar.gz"

# Grafana CDN 国内通常直连可用
curl -sL -o grafana.tar.gz \
  https://dl.grafana.com/oss/release/grafana-10.4.2.linux-amd64.tar.gz
```

```bash
# 策略 2：清华大学镜像（仅 Prometheus）
# curl -sL -o prometheus.tar.gz https://mirrors.tuna.tsinghua.edu.cn/github-release/prometheus/prometheus/v2.53.1/prometheus-2.53.1.linux-amd64.tar.gz

# 策略 3：离线传包（以上均失败时用）
# 本地下载后 SCP 上传：scp postgres_exporter.tar.gz root@<host>:/opt/otb-monitor/downloads/
```

下载后必须验证 tar 完整性：

```bash
tar -tzf postgres_exporter.tar.gz >/dev/null && echo "postgres_exporter VALID" || echo "postgres_exporter CORRUPT"
ls -lh *.tar.gz   # postgres_exporter=~4.1MB, prometheus=~85MB, grafana=~80MB
```

`-C -` 支持断点续传。无法访问外网时，要求用户提供离线包，不要临时更换未知来源下载地址。

## 解压

```bash
cd /opt/otb-monitor

tar -xzf downloads/prometheus.tar.gz
mv prometheus-*.linux-amd64 prometheus

tar -xzf downloads/postgres_exporter.tar.gz
mv postgres_exporter-*.linux-amd64 postgres_exporter

tar -xzf downloads/grafana.tar.gz
mv grafana-* grafana
```

## 版本检查

```bash
/opt/otb-monitor/prometheus/prometheus --version | head -n 2
/opt/otb-monitor/postgres_exporter/postgres_exporter --version 2>&1 | head -n 2
/opt/otb-monitor/grafana/bin/grafana-server -v 2>&1 | head -n 2
```

## Prometheus 配置

用实际 exporter 端口生成 `/opt/otb-monitor/conf/prometheus.yml`：

```yaml
global:
  scrape_interval: 5s
  evaluation_interval: 5s

scrape_configs:
  - job_name: 'opentenbase-cn'
    static_configs:
      - targets: ['127.0.0.1:9187']
        labels:
          instance: 'cn001'
          cn_host: '<cn1_host>'
          cn_port: '<cn1_port>'
      - targets: ['127.0.0.1:9188']
        labels:
          instance: 'cn002'
          cn_host: '<cn2_host>'
          cn_port: '<cn2_port>'
```

启动：

```bash
mkdir -p /opt/otb-monitor/data/prometheus
nohup /opt/otb-monitor/prometheus/prometheus \
  --config.file=/opt/otb-monitor/conf/prometheus.yml \
  --storage.tsdb.path=/opt/otb-monitor/data/prometheus \
  --web.listen-address=0.0.0.0:9090 \
  --web.enable-lifecycle \
  >/opt/otb-monitor/logs/prometheus.log 2>&1 &
```

## Grafana 配置

创建目录：

```bash
mkdir -p \
  /opt/otb-monitor/conf/grafana/provisioning/datasources \
  /opt/otb-monitor/conf/grafana/provisioning/dashboards \
  /opt/otb-monitor/conf/grafana/dashboards \
  /opt/otb-monitor/data/grafana \
  /opt/otb-monitor/logs
```

`/opt/otb-monitor/conf/grafana.ini`：

```ini
[paths]
data = /opt/otb-monitor/data/grafana
logs = /opt/otb-monitor/logs
plugins = /opt/otb-monitor/data/grafana/plugins
provisioning = /opt/otb-monitor/conf/grafana/provisioning

[server]
http_addr = 0.0.0.0
http_port = 3000

[security]
admin_user = admin
admin_password = admin
```

`/opt/otb-monitor/conf/grafana/provisioning/datasources/prometheus.yml`：

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://127.0.0.1:9090
    isDefault: true
    editable: true
```

启动：

```bash
nohup /opt/otb-monitor/grafana/bin/grafana server \
  --homepath /opt/otb-monitor/grafana \
  --config /opt/otb-monitor/conf/grafana.ini \
  >/opt/otb-monitor/logs/grafana.log 2>&1 &
```

实验环境可用 `admin/admin`，正式环境必须修改密码。

