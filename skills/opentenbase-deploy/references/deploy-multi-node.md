# 多机多节点生产部署

> 本文档覆盖：生产级多机拓扑、一键脚本多机部署、手动多机部署、低内存 DN 扩展、防火墙配置。

---

## 拓扑规划

### 生产推荐拓扑

| 角色 | 数量 | 说明 |
|------|------|------|
| GTM | 1 台（独立） | 全局事务管理器，单点，需独立机器避免资源争抢 |
| Coordinator (CN) | 1–2 台 | 客户端入口，可多 CN 负载均衡 |
| Datanode (DN) | 2+ 台 | 数据存储，按分片策略分布 |

> **不支持的拓扑**：单机多节点裸机部署。CN 和 DN 的 forward manager 都绑定 `127.0.0.1:6670`，同机第二个节点会报端口冲突。想在一台机器上跑多节点，用 Docker Compose。

---

## 前提条件

- 每台服务器 ≥ 4GB 内存
- 所有服务器间网络互通
- 所有节点使用**相同的 SSH 用户名和密码**
- 每台服务器都已安装 `opentenbase` 软件包
- 每台服务器都已创建路径符号链接
- 执行机已安装 `sshpass`
- 防火墙开放端口：6666（GTM）、11003（CN）、15432（DN）

---

## 一键脚本多机部署

场景：3 台服务器，GTM 在 `.10`，CN 在 `.11`，DN 在 `.12`。

在任意一台服务器（推荐 GTM 所在机器）执行：

```bash
sudo bash opentenbase.sh install --yes \
    --gtm-ip 192.168.1.10 \
    --cn-ip 192.168.1.11 \
    --dn-ip 192.168.1.12 \
    --ssh-password MyPass123
```

**各节点需提前完成**：

```bash
# 在每台服务器上执行
# 1. 安装软件包
sudo apt install -y opentenbase sshpass    # 或 dnf install

# 2. 创建用户
sudo useradd -m -s /bin/bash opentenbase
sudo passwd opentenbase  # 设置相同密码

# 3. 路径符号链接
sudo mkdir -p /usr/local/install
sudo ln -sf /usr/lib/opentenbase/5.0 /usr/local/install/opentenbase
```

---

## 手动多机部署

### Step 1：各节点安装软件包 + 系统准备

参考 `install-and-deploy-single-node.md` 的安装途径和系统准备步骤，在**每台**服务器上完成。

### Step 2：创建 tar.gz 包（执行机上）

```bash
cd /usr/lib/opentenbase/5.0
sudo tar -zcf /tmp/opentenbase-5.0.tar.gz *
```

### Step 3：编写多机 INI 配置

#### 基础 3 节点（1 GTM + 1 CN + 1 DN）

```ini
[instance]
name=prod01
type=distributed
package=/tmp/opentenbase-5.0.tar.gz

[gtm]
master=192.168.1.10

[coordinators]
master=192.168.1.11
nodes-per-server=1

[datanodes]
master=192.168.1.12
nodes-per-server=1

[server]
ssh-user=opentenbase
ssh-password=MyPass123
ssh-port=22

[log]
level=INFO
```

#### 多 DN 配置（1 GTM + 1 CN + 3 DN）

```ini
[gtm]
master=192.168.1.10

[coordinators]
master=192.168.1.11
nodes-per-server=1

[datanodes]
master=192.168.1.12,192.168.1.13,192.168.1.14
nodes-per-server=1
```

#### 多 CN + 多 DN 配置（1 GTM + 2 CN + 3 DN）

```ini
[gtm]
master=192.168.1.10

[coordinators]
master=192.168.1.11,192.168.1.12
nodes-per-server=1

[datanodes]
master=192.168.1.13,192.168.1.14,192.168.1.15
nodes-per-server=1
```

### Step 4：安装集群

```bash
sudo -u opentenbase opentenbase_ctl install -c /tmp/otb_config.ini
```

`opentenbase_ctl install` 会通过 SSH（`sshpass` + 密码）自动：
1. 传输 tar.gz 到各节点并解压
2. 安装 GTM 主节点
3. 安装 CN/DN 节点并完成互注册
4. 创建默认节点组和分片映射

### Step 5：验证

```bash
# 全节点状态
opentenbase_ctl status

# 连接 CN（5.0 端口 11003）
export LD_LIBRARY_PATH=/var/lib/opentenbase/install/opentenbase/5.0/lib
psql -h 192.168.1.11 -p 11003 -U opentenbase -d postgres -c "SELECT version();"

# 查看节点拓扑
psql -h 192.168.1.11 -p 11003 -U opentenbase -d postgres \
  -c "SELECT node_name, node_type, node_host FROM pgxc_node;"
```

---

## 防火墙配置

各角色需开放的端口：

| 角色 | 开放端口 | 用途 |
|------|---------|------|
| GTM | 6666 | GTM 服务 |
| CN | 11003 | 客户端连接 |
| CN | 6666, 15432 | 到 GTM 和 DN 的内部通信 |
| DN | 15432 | 数据节点服务 |
| DN | 6666 | 到 GTM 的内部通信 |

```bash
# firewalld 示例（CN 节点）
sudo firewall-cmd --permanent --add-port=11003/tcp
sudo firewall-cmd --permanent --add-port=6666/tcp
sudo firewall-cmd --permanent --add-port=15432/tcp
sudo firewall-cmd --reload

# ufw 示例（CN 节点）
sudo ufw allow 11003/tcp
sudo ufw allow 6666/tcp
sudo ufw allow 15432/tcp
```

---

## 低内存 DN 部署（1–2GB 服务器）

场景：1–2GB 内存的小机器，跑不了完整集群，但想作为 Datanode 加入已有远程集群。

专用脚本 `deploy-lowmem-datanode.sh`（位于官方仓库 `scripts/extras/`）：自动建 1GB swap、只起 DN 进程、直连远程 GTM，内存占用约 **400–600MB**。

```bash
# 在低内存机器上执行（--gtm-ip 必填，指向已有集群的 GTM）
```bash
# CDN 加速（推荐）
curl -sSL https://repo.blackevil217.com/scripts/extras/deploy-lowmem-datanode.sh | sudo bash -s -- --gtm-ip 192.168.1.10

# GitHub 直连（备用）
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/extras/deploy-lowmem-datanode.sh | sudo bash -s -- --gtm-ip 192.168.1.10

# 完整参数
sudo bash extras/deploy-lowmem-datanode.sh \
    --gtm-ip 192.168.1.10 \
    --gtm-port 6666 \
    --dn-name dn2 \
    --dn-port 15432 \
    --version 5.0
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--gtm-ip IP` | 远程 GTM 的 IP | **必填** |
| `--gtm-port PORT` | GTM 端口 | `6666` |
| `--dn-name NAME` | 本 Datanode 名称 | `dn1` |
| `--dn-port PORT` | 本 Datanode 端口 | `15432` |
| `--version VER` | OpenTenBase 版本 | `5.0` |

> 该脚本直接用 `initdb` + `pg_ctl` 启动 DN（不走 opentenbase_ctl），加入后需在 CN 侧用 `CREATE NODE` 注册该 DN 并重分布数据。

---

## 扩容与缩容

部署完成后，如需增减节点：

```bash
# 扩容（在 INI 中添加新节点 IP 后执行）
opentenbase_ctl expand -c /tmp/otb_config.ini

# 缩容（在 INI 中移除节点 IP 后执行）
opentenbase_ctl shrink -c /tmp/otb_config.ini
```

> `expand`/`shrink` 都需要 `-c` 参数。扩容不删除现有数据。
