# OpenTenBase 部署参考索引

## 参考文件

| 文件 | 内容 |
|------|------|
| `one-click-install.md` | 一键安装使用 |
| `memory-tuning.md` | 内存调优规则 |
| `deploy-multi-node.md` | 多节点部署 |
| `install-and-deploy-single-node.md` | 源码编译 |
| `version-switch.md` | 版本切换 |
| `cluster-management.md` | 集群管理命令 |
| `config-reference.md` | 配置文件参考 |
| `troubleshooting.md` | 故障排查 |
| `deploy-docker-compose.md` | Docker 部署 |

## 三种安装方式

1. 一键脚本（推荐）
2. AI 定制化
3. 手动安装

## 快速命令

```bash
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/opentenbase.sh | sudo bash -s -- --yes
```