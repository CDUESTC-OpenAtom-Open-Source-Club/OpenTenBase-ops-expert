# Docker Compose 部署

> 本文档覆盖：容器化部署 OpenTenBase，每个节点一个容器，独立 IP，适合开发/测试/CI。

---

## 前提条件

- Docker 和 Docker Compose 已安装
- 至少 4GB 可用内存
- 中国大陆服务器需配置 Docker 镜像加速：

```bash
sudo mkdir -p /etc/docker
echo '{"registry-mirrors":["https://docker.m.daocloud.io"]}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

---

## 一键启动

```bash
# 下载并运行部署脚本（自动检测架构，下载 RPM，创建 docker-compose.yml）
curl -sLO https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/docker/test-docker.sh
bash test-docker.sh

# 启动集群（4 个容器：GTM + Coordinator + Datanode1 + Datanode2）
cd /tmp/otb-docker/compose
docker compose up -d --build
```

> **镜像 tag 说明**：`test-docker.sh` 下载的是 multi-arch 的 RPM（来自 `v5.0-multi13` tag），与裸机部署用的 `v5.0-p32` 是两套 tag 体系。这是正常的，不影响使用。

---

## 架构

```
Docker Network (172.20.0.0/24，IP 由 Docker 动态分配)
┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐
│  GTM     │  │  CN       │  │  DN01    │  │  DN02    │
│  :6666   │  │  :5432    │  │  :15432  │  │  :15433  │
└──────────┘  └───────────┘  └──────────┘  └──────────┘
              ↑ 对外端口 5432
```

每个容器独立 IP，`forward_port`（6670）和 `pooler_port`（6669）互不冲突。

> **端口提醒**：Docker 部署下 CN 端口是 **5432**（通过环境变量 `COORD_PORT=5432` 配置并映射到宿主机）；裸机 5.0 的 CN 端口是 **11003**。连接前请确认部署方式。

---

## 验证连接

```bash
# 从宿主机连接（CN 端口映射到 5432）
psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c "SELECT version();"

# 查看节点拓扑
psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres \
  -c "SELECT node_name, node_type, node_host FROM pgxc_node;"
```

---

## 集群管理

```bash
cd /tmp/otb-docker/compose

docker compose ps               # 查看容器状态
docker compose logs coordinator  # 查看 CN 日志
docker compose down              # 停止并删除容器
docker compose up -d             # 重新启动
docker compose down -v           # 停止并删除数据卷（完全重置）
```

---

## 自定义节点数量

编辑 `/tmp/otb-docker/compose/docker-compose.yml`，增加 datanode3 服务：

```yaml
  datanode3:
    build:
      context: ../runtime
      dockerfile: Dockerfile.runtime
    image: opentenbase-runtime:latest
    container_name: opentenbase-datanode3
    hostname: datanode3
    security_opt:
      - apparmor:unconfined
    depends_on:
      gtm:
        condition: service_healthy
    environment:
      - NODE_TYPE=datanode
      - NODE_NAME=datanode3
      - GTM_HOST=gtm
      - GTM_PORT=6666
      - COORD_HOST=coordinator
      - COORD_PORT=5432
      - DN_PORT=15434
    ports:
      - "15434:15434"
    volumes:
      - dn3_data:/var/lib/opentenbase/data/datanode3
    networks:
      - opentenbase
```

然后在 `volumes:` 下添加 `dn3_data:`，重新 `docker compose up -d --build`。

---

## 源码编译 Docker（进阶）

仓库另有 `docker/cluster/quick-start-source.sh`，在容器内 clone 上游源码并编译运行。

- 端口拓扑不同（CN=15432）
- 库名为 `opentenbase`（非 `postgres`）
- 仅供二次开发使用，日常部署不用

---

## 为什么用 Docker Compose 而非单容器

OpenTenBase 的 CN 和 DN 都有 **forward manager**（查询转发器），默认绑定 `127.0.0.1:6670`。单容器内多节点会报 `Address already in use`。

Docker Compose 让每个节点独占一个容器 IP，天然解决端口冲突，是实现"单机多节点体验"的正式路径。

---

## 端口对照

| 服务 | 5.0 裸机 | 5.0 Docker | 说明 |
|------|----------|------------|------|
| GTM | 6666 | 6666 | 全局事务管理器 |
| Coordinator (CN) | **11003** | **5432** | 客户端连接入口 |
| Datanode (DN) | 15432 | 15432/15433 | 多 DN 递增 |
| Pooler | 6669 | 6669 | 各容器独立 IP 不冲突 |
| Forward Manager | 6670 | 6670 | 各容器独立 IP 不冲突 |
