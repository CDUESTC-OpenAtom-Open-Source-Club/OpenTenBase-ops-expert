# 版本切换与共存

> 本文档覆盖：一台机器上安装多个版本、版本间切换、各版本管理工具差异。

---

## 多版本 Side-by-Side 安装

`opentenbase.sh`（旧版 `install.sh`）支持在一台机器上同时安装多个版本，各版本安装到独立目录：

| 版本 | 安装路径 |
|------|---------|
| 5.0 | `/usr/lib/opentenbase/5.0/` |
| 2.6.0 | `/usr/lib/opentenbase/2.6.0/` |
| 2.5.0 | `/usr/lib/opentenbase/2.5.0/` |

### 安装多版本

> **2026-06-30 变更**：官方仓库已将 `install.sh` 合并到统一入口 `opentenbase.sh`。以下用法更新。

```bash
# 通过 opentenbase.sh 安装版本（推荐）
sudo bash opentenbase.sh install --yes --version 5.0

# 安装其他版本（不会覆盖之前版本）
sudo bash opentenbase.sh install --yes --version 2.6.0
sudo bash opentenbase.sh install --yes --version 2.5.0

# 旧版 install.sh 用法（供参考）
# sudo bash install.sh --version 5.0
# sudo bash install.sh --version 2.6.0
# sudo bash install.sh --version 2.5.0
```

每次安装都会部署 `/usr/bin/opentenbase-switch-version` 命令。

---

## 版本切换

### `opentenbase-switch-version` 命令

```bash
# 列出已安装版本并显示当前激活版本
opentenbase-switch-version

# 切换到指定版本（需 root）
sudo opentenbase-switch-version 5.0       # 或 2.6.0 / 2.5.0
```

### 切换原理

切换操作修改 `/etc/opentenbase/current` 符号链接，指向目标版本目录：

```
/etc/opentenbase/current → /usr/lib/opentenbase/5.0/
```

同时更新 `/usr/bin/` 下的命令符号链接（`opentenbase_ctl`、`psql`、`initdb` 等），使其指向当前版本。

### 切换影响范围

| 影响项 | 说明 |
|--------|------|
| **新起的会话/命令** | ✅ 使用新版本 |
| **已运行的集群进程** | ❌ 不受影响（进程已加载旧版本二进制） |
| **数据目录** | ❌ 不受影响（数据目录与版本无关） |

> **注意**：切换版本后，已运行的集群不会自动重启。如需使用新版本，需手动停止旧集群再用新工具启动。

---

## 各版本管理工具差异

### 2.5 / 2.6 — `pgxc_ctl` 链路

```bash
pgxc_ctl deploy -c pgxc_ctl.conf    # 部署集群
pgxc_ctl init -c pgxc_ctl.conf      # 初始化节点
pgxc_ctl start -c pgxc_ctl.conf     # 启动
pgxc_ctl stop -c pgxc_ctl.conf      # 停止
pgxc_ctl monitor -c pgxc_ctl.conf   # 监控
pgxc_ctl show cluster -c pgxc_ctl.conf  # 查看状态
```

- CN 端口：**5432**
- 配置文件：`pgxc_ctl.conf`
- **已知限制**：`initdb` 不能直接调用（会报 `create gtm node (null)`），必须通过 `pgxc_ctl` 间接调用

### 5.0 — `opentenbase_ctl` 链路

```bash
opentenbase_ctl install -c config.ini   # 安装集群（需 -c）
opentenbase_ctl start                   # 启动（不带 -c）
opentenbase_ctl stop                    # 停止（不带 -c）
opentenbase_ctl status                  # 查看状态（不带 -c）
opentenbase_ctl delete -c config.ini    # 删除集群（需 -c）
opentenbase_ctl expand -c config.ini    # 扩容（需 -c）
opentenbase_ctl shrink -c config.ini    # 缩容（需 -c）
```

- CN 端口：**11003**（裸机）
- 配置文件：INI 格式（`config.ini`）
- `-c` 规则：`install`/`delete`/`expand`/`shrink` 必须带 `-c`；`start`/`stop`/`status` 不带

---

## 版本选择建议

| 场景 | 推荐版本 | 理由 |
|------|---------|------|
| 新部署、生产环境 | **5.0** | 最新链路，`opentenbase_ctl` 功能完善，p32 端到端验证 |
| 已有 2.x 集群维护 | **2.5 / 2.6** | 兼容现有 `pgxc_ctl` 链路 |
| 学习/测试 | **5.0** | 官方主推，文档齐全 |
| 需要源码定制 | master | `opentenbase.sh install --build-from-source`（旧 `install.sh --build-from-source`） |

> **红线**：2.5/2.6 用 `pgxc_ctl`，5.0 用 `opentenbase_ctl`，工具不能混用。

---

## 版本迁移注意事项

从 2.x 迁移到 5.0 时：

1. **数据不兼容**：2.x 和 5.0 的数据目录格式不同，不能直接切换版本启动旧数据
2. **需要导出导入**：用 `pg_dump` 导出 2.x 数据，在 5.0 新集群中导入
3. **端口变化**：CN 端口从 5432 变为 11003，更新应用连接串
4. **工具变化**：管理脚本从 `pgxc_ctl` 改为 `opentenbase_ctl`

```bash
# 2.x 导出
pg_dump -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -F c -f backup.dump

# 5.0 导入
pg_restore -h 127.0.0.1 -p 11003 -U opentenbase -d postgres backup.dump
```
