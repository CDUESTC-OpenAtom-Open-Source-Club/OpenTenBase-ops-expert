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

### v3.5.0（2026-07-01）

- 同步官方仓库 2026-07-01 最新提交（#44–#56）
- CDN 优先：`opentenbase.sh`/`setup-apt.sh`/`setup-rpm.sh` 改为 CDN 优先下载（`repo.blackevil217.com/scripts/`），GitHub raw 回退
- 版本显式锁定：安装时 pin 版本号（`dnf install opentenbase-<ver>` / `apt install opentenbase=<ver>`），确保 `--version` 参数生效
- RPM `--nodeps` 回退链解决非 RHEL 发行版 RHPG 符号依赖问题
- `pgxc_ctl` 2.5/2.6 修复：`chown -R` 工作目录 + 显式 `--home` 参数
- 版本检测重构：`detect_installed_version()` 通过 rpm -q 或目录扫描
- `resolve_script()`：`uninstall`/`switch` 子命令在 curl|bash 下自动从 CDN 下载 helper
- 日常运维分离：安装后提示明确区分 `opentenbase_ctl`/`pgxc_ctl` 与一键脚本
- 验证测试修复：移除 timestamp/now() 列、加入 `pgxc_pool_reload` + sleep 2s
- 新已知问题：pgxc_ctl `--home` 参数说明