# 集群管理命令参考

> 本文档覆盖：`opentenbase_ctl`（5.0）和 `pgxc_ctl`（2.5/2.6）全命令速查、分布式表操作、卸载流程。

---

## opentenbase_ctl（5.0）

### `-c` 参数规则

| 命令 | 需要 `-c` | 说明 |
|------|----------|------|
| `install` | ✅ | 安装集群 |
| `delete` | ✅ | 删除集群 |
| `expand` | ✅ | 扩容 |
| `shrink` | ✅ | 缩容 |
| `start` | ❌ | 启动（install 后状态已持久化） |
| `stop` | ❌ | 停止 |
| `status` | ❌ | 查看状态 |

### 全命令速查

```bash
# 安装集群
opentenbase_ctl install -c config.ini

# 启动 / 停止 / 查看状态（不带 -c）
opentenbase_ctl start
opentenbase_ctl stop
opentenbase_ctl status

# 删除集群（带 -c）
opentenbase_ctl delete -c config.ini

# 扩容 / 缩容（带 -c）
opentenbase_ctl expand -c config.ini
opentenbase_ctl shrink -c config.ini
```

### SSH 远程执行

通过 `sshpass` + 密码远程执行（无需密钥互信），在 INI 的 `[server]` 段配置：

```ini
[server]
ssh-user=opentenbase
ssh-password=your_password
ssh-port=22
```

### 安装流程（`install` 自动完成）

1. 处理安装包（SCP 传输到各节点并解压）
2. 安装 GTM 主节点（initdb → 配置 → 启动 → 注册）
3. 安装 CN/DN 主节点（initdb → 配置 → 启动 → 节点互注册）
4. 创建默认节点组和分片映射

---

## pgxc_ctl（2.5 / 2.6）

### 全命令速查

```bash
# 部署集群
pgxc_ctl deploy -c pgxc_ctl.conf

# 初始化节点
pgxc_ctl init -c pgxc_ctl.conf

# 启停
pgxc_ctl start -c pgxc_ctl.conf
pgxc_ctl stop -c pgxc_ctl.conf

# 监控
pgxc_ctl monitor -c pgxc_ctl.conf

# 查看集群状态
pgxc_ctl show cluster -c pgxc_ctl.conf
```

> 所有命令统一带 `-c pgxc_ctl.conf`。

### ⚠️ initdb 限制

2.5/2.6 的 `initdb` 在 bootstrap 阶段会执行 `create gtm node` 注册 GTM，但它自身没有 `--gtmhost`/`--gtmport` 参数。

**必须通过 `pgxc_ctl deploy` 或 `pgxc_ctl init` 间接调用 initdb**，由 `pgxc_ctl` 通过环境变量传入 GTM 连接信息。直接调用 `initdb` 会导致 `create gtm node (null)` 语法错误。

```bash
# ✅ 正确
pgxc_ctl deploy -c pgxc_ctl.conf

# ❌ 错误 — 会触发 (null) bug
initdb --nodename=coord1 --nodetype=coordinator -D /data/coord
```

---

## 分布式表操作

### 分发策略

| 策略 | 语法 | 适用场景 |
|------|------|---------|
| **SHARD** | `DISTRIBUTE BY SHARD(col)` | 大表、高写入（数据按哈希分布到各 DN） |
| **REPLICATION** | `DISTRIBUTE BY REPLICATION` | 小表、字典表（每 DN 存全量副本） |

### 建表示例

```sql
-- 分片表（最常用）
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount DECIMAL(10,2)
) DISTRIBUTE BY SHARD(id) TO GROUP default_group;

-- 复制表
CREATE TABLE regions (
    id INT PRIMARY KEY,
    name VARCHAR(50)
) DISTRIBUTE BY REPLICATION TO GROUP default_group;
```

### 查看节点拓扑

```sql
SELECT node_name, node_type, node_host FROM pgxc_node;
```

---

## 连接方式

### 5.0 裸机（CN 端口 11003）

```bash
export LD_LIBRARY_PATH=/var/lib/opentenbase/install/opentenbase/5.0/lib
psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres
```

### 5.0 Docker（CN 端口 5432）

```bash
psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres
```

### 2.5 / 2.6（CN 端口 5432）

```bash
psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres
```

> 连接前请用集群管理工具确认端口：`opentenbase_ctl status`（5.0）或 `pgxc_ctl monitor`（2.5/2.6）。

---

## 卸载

### 方式一/二（裸机部署）

```bash
# 1. 删除集群（delete 需要 -c）
opentenbase_ctl delete -c /tmp/otb_config.ini

# 2. 卸载软件包
sudo apt remove --purge opentenbase    # APT
sudo dnf remove opentenbase             # RPM
```

### 方式三（Docker 部署）

```bash
cd /tmp/otb-docker/compose && docker compose down -v
```

> 卸载前先告知用户会删什么，全量卸载（`--purge` / `-v`）会清数据，让用户确认。

---

## 后续参数调整

修改配置（换 IP、加节点等）：

```bash
# 方案 A：删除旧集群重新安装
opentenbase_ctl delete -c /tmp/otb_config.ini
opentenbase_ctl install -c /tmp/otb_config.ini

# 方案 B：扩容（不删除现有数据）
opentenbase_ctl expand -c /tmp/otb_config.ini
```

---

## 官方脚本速查

| 脚本 | 用途 | 调用方式 |
|------|------|---------|
| `opentenbase.sh` | 统一管理脚本（安装/卸载/切换/状态/测试） | `curl ... \| sudo bash` 或 `sudo bash opentenbase.sh [command]` |
| `setup-apt.sh` | APT 仓库配置 | `curl ... \| sudo bash` |
| `setup-rpm.sh` | RPM 仓库配置 | `curl ... \| sudo bash` |
| `uninstall.sh` | 卸载 | `curl ... \| sudo bash`（或 `opentenbase.sh uninstall`） |
| `extras/deploy-lowmem-datanode.sh` | 低内存 DN 部署 | `curl ... \| sudo bash` |
| `test-docker.sh` | Docker Compose 部署 | `curl -sLO && bash` |

所有脚本来源：`https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/`
