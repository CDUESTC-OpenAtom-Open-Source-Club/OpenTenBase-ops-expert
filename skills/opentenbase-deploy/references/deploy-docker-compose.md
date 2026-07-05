# Docker Compose 部署

适用于快速体验、开发测试。

## 前置条件

```bash
# 验证 Docker 已安装
docker --version
docker-compose --version
```

## 部署命令

```bash
git clone https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages.git
cd OpenTenBase-Packages/docker/cluster
docker-compose up -d
```

## 连接测试

```bash
docker exec -it coordinator psql -U opentenbase -d postgres
```

## 注意事项

- Docker 方式不适合生产环境
- 数据存储在容器内，重启会丢失
- 国内需要配置镜像加速