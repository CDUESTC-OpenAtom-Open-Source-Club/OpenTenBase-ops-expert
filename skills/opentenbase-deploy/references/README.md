# 参考文档目录

本目录存放 opentenbase-deploy 技能专属的参考文档。

Skill 通过 `{baseDir}/references/` 路径引用这些文件。

## 文档索引

| 文件 | 内容 |
|------|------|
| `deploy-guide.md` | 部署操作详细指南（单节点 / 多机多节点 / Docker） |
| `config-params.md` | INI 配置文件参数说明 + 多节点拓扑示例 |
| `troubleshooting.md` | 部署故障排查（端口冲突 / GTM 崩溃 / libpqxx 缺失等） |
| `cluster-topology.md` | 集群拓扑设计参考（单节点 / 多机多节点 / Docker 多节点） |

## 外部参考

- 仓库 README：`https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages`
- 快速开始：仓库 `docs/QUICKSTART.md`
- 部署指南：仓库 `docs/07-deployment.md`
- 上游 opentenbase_ctl 源码：`https://github.com/OpenTenBase/OpenTenBase/tree/v5.0/contrib/opentenbase_ctl`

## 重要变更记录

### v3.1.0（2026-06-29）

以下修正基于 `162.14.74.145`（OpenCloudOS 9.4, 2核）服务器端到端测试验证：

1. **所有 opentenbase_ctl 命令都需要 `-c` 参数**
   - 之前认为只有 `install` 需要，实测 `status`/`start`/`stop`/`delete` 全部需要
   - 不带 `-c` 报错：`Failed to extract version from package name`

2. **CN 连接端口是 11003，不是 5432**
   - `opentenbase_ctl` 部署的单节点集群 CN 监听 11003
   - Docker Compose 部署的 CN 映射到宿主机 5432
   - 连接前用 `opentenbase_ctl status -c config.ini` 确认端口

3. **GTM 2核修复必须用 /etc/ld.so.preload**
   - `LD_PRELOAD` 无效：GTM 由 opentenbase_ctl 通过 SSH 启动为独立进程，环境变量不传播
   - 正确方案：将 `noaffinity.so` 写入 `/etc/ld.so.preload` 全局注入

4. **INI 配置 package= 必须是 tar.gz 文件**
   - `opentenbase_ctl` 的 `excute_cp_file()` 对本地 IP 用 `cp`（无 `-r`），不支持目录
   - 正确：`package=/tmp/opentenbase-5.0.tar.gz`
   - 错误：`package=/usr/lib/opentenbase/5.0`

5. **运行时库路径**
   - 部署后 psql 连接需设置 `LD_LIBRARY_PATH`
   - 路径：`/var/lib/opentenbase/install/opentenbase/5.0/lib`

### v3.2.0（2026-06-29）

CI 自动化打包流程修复：

6. **libpqxx 条件构建导致 RPM 包缺失**
   - 根因：EPEL 提供的旧版 libpqxx（7.6.x/7.7.x）存在 `range.hxx` bug，编译 `opentenbase_ctl` 时报 `invalid use of 'this' at top level`
   - CI 原逻辑 `if ! test -f /usr/include/pqxx/pqxx` 仅检查头文件是否存在，不检查版本兼容性
   - 在 rockylinux-8、almalinux-8、centos-stream-8、fedora-40 上，EPEL 安装了不兼容的旧版头文件，导致源码构建被跳过
   - **修复**：所有 CI workflow（build-rpm.yml / build-deb.yml）和 opentenbase.spec 中，改为**始终从源码构建 libpqxx 7.9.2**，先移除系统已安装的不兼容版本
   - 修复涉及 5 处代码：build-rpm.yml x86_64+aarch64、build-deb.yml amd64+aarch64、opentenbase.spec %build

7. **RPM spec 中 COORD_PORT 配置修正**
   - `opentenbase.spec` 生成的 `opentenbase.conf` 中 `COORD_PORT=5432` → 改为 `11003`
   - 与实际部署验证结果一致（`ss -tlnp` 确认 postgres 监听 `0.0.0.0:11003`）

8. **0MB DEB 包说明**
   - `opentenbase_5.0-1_all.deb`（0MB）是合法的**元包（metapackage）**，仅依赖 `opentenbase-server` + `opentenbase-client`，无实际文件
   - `debian/control` 明确标注 `Architecture: all` + `Description: ... (metapackage)`
   - `opentenbase.install` 为空文件（0字节），0MB 是预期行为
   - `opentenbase-client` 和 `libopentenbase-dev` 有实际内容，正常构建时不会为 0MB

9. **RHEL-8 GCC 8.x 兼容性修复**
   - GCC 8.x（RHEL-8 默认）不支持 libpqxx 7.9.2 中 `*this` 在 `noexcept(noexcept(...))` 的使用
   - 修复：在 RHEL-8 系发行版（rockylinux-8/almalinux-8/centos-stream-8）上安装 `gcc-toolset-11`（提供 GCC 11）
   - `build-rpm.yml`：安装 gcc-toolset-11 并导出到 GITHUB_PATH
   - `opentenbase.spec`：`%build` 开头 `source /opt/rh/gcc-toolset-11/enable`（如果可用）
   - 这是 Red Hat 官方推荐的做法，用于在 RHEL-8 上编译现代 C++17 代码
   - CI 验证结果：全部 18 个 RPM 构建 job 100% 通过（包括之前失败的 4 个发行版）

10. **RPM spec 工作目录恢复修复**
    - libpqxx 从源码构建时 `cd /tmp` 会离开 OpenTenBase 源码目录
    - 后续 `make -C src/interfaces/libpq` 在 `/tmp` 中执行失败（路径不存在）
    - 修复：构建 libpqxx 前保存 `OTB_SRCDIR_ABS="$(pwd)"`，构建后 `cd "$OTB_SRCDIR_ABS"`
