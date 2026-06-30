# 参考文档目录

本目录存放 opentenbase-deploy 技能专属的参考文档，按主题拆分，方便按需查阅。

Skill 通过 `{baseDir}/references/` 路径引用这些文件。

## 文档索引

| # | 文件 | 主题 | 解决什么问题 |
|---|------|------|------------|
| 1 | `install-and-deploy-single-node.md` | 多版本安装 + 单节点部署 | 怎么装包 + 一台机器最快跑起来 |
| 2 | `version-switch.md` | 版本切换与共存 | 一台机器装多个版本，切换、迁移 |
| 3 | `deploy-docker-compose.md` | Docker Compose 部署 | 容器化开发测试环境 |
| 4 | `deploy-multi-node.md` | 多机多节点生产部署 | 生产级多机拓扑、防火墙、高可用 |
| 5 | `cluster-management.md` | 集群管理命令参考 | `pgxc_ctl` / `opentenbase_ctl` 全命令速查 |
| 6 | `config-reference.md` | 配置参数参考 | INI 参数详解、`pgxc_ctl.conf` 模板、多拓扑示例 |
| 7 | `troubleshooting.md` | 故障排查 | 已知故障场景及解决方案 |

> 以上 7 篇文档均已完成。

## 外部参考

- 仓库 README：`https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages`
- 快速开始：仓库 `docs/01-quickstart.md`、`docs/QUICKSTART.md`
- 部署指南：仓库 `docs/07-deployment.md`
- 故障排除：仓库 `docs/05-troubleshoot.md`
- 上游 opentenbase_ctl 源码：`https://github.com/OpenTenBase/OpenTenBase/tree/v5.0/contrib/opentenbase_ctl`

## 官方脚本索引

所有部署脚本均从官方仓库直接引用，本技能不维护本地副本：

| 脚本 | 用途 | 来源 |
|------|------|------|
| `opentenbase.sh` | 统一管理脚本（原 deploy-opentenbase.sh + install.sh 合并） | `scripts/opentenbase.sh` |
| `setup-apt.sh` | 配置 APT 仓库 | `scripts/setup-apt.sh` |
| `setup-rpm.sh` | 配置 RPM 仓库 | `scripts/setup-rpm.sh` |
| `uninstall.sh` | 卸载 | `scripts/uninstall.sh` |
| `switch-version.sh` | 版本切换 | `scripts/switch-version.sh` |
| `extras/deploy-lowmem-datanode.sh` | 低内存 DN 部署 | `scripts/extras/deploy-lowmem-datanode.sh` |
| `test-docker.sh` | Docker Compose 部署 | `docker/test-docker.sh` |

## 重要变更记录

### v3.4.0（2026-06-30）

- 同步官方仓库 2026-06-30 变更：`deploy-opentenbase.sh` + `install.sh` → 合并为 `opentenbase.sh` 统一入口
- `opentenbase.sh` 新增子命令：`install`、`uninstall`、`switch`、`status`、`test`
- `install.sh` 已从官方仓库删除
- `deploy-lowmem-datanode.sh` 移至 `scripts/extras/`
- SKILL.md 添加 `--clean` 参数、主目录权限修复已知问题
- 更新版本号至 3.4.0