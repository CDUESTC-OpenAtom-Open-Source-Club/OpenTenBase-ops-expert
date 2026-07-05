# OpenTenBase 部署记录 - 162.14.74.145

## 客观信息
- 时间: Sat 2026-07-04 07:31 PDT
- 目标: root@162.14.74.145 (Passwordless SSH)
- 服务器: OpenCloudOS 9.4, 2核, 7.5GB RAM, 100GB磁盘(89GB可用), x86_64
- SELinux: 已关闭 | 防火墙: 未启用

## 部署详情
- 方式: 一键脚本 `opentenbase.sh --yes`
- 版本: 5.0（默认）
- 模式: 单机单节点（single: 1 GTM + 1 CN + 1 DN）
- 集群名: otb01
- 端口: GTM=11000, CN=11003, DN=11006
- 数据目录: /var/lib/opentenbase/run/instance/otb01/

## 特殊处理
- 2核CPU → 自动下载并注入 noaffinity.so 绕过 GTM 亲和性问题（/etc/ld.so.preload 全局注入）
- OpenCloudOS 9.4 的 dnf 依赖解析失败 → 自动降级为 rpm --nodeps --replacefiles 安装

## 验证结果
- 集群安装成功
- 分布式表创建/写入/查询测试通过
- 3条记录在 DN 分片写入成功

## 连接信息
```
psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres
```
