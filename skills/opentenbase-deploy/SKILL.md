---
name: opentenbase-deploy
description: OpenTenBase 集群部署。三种方式：一键脚本（推荐）、AI定制化、手动安装。支持版本切换、多节点、内存调优、tune 参数调整。
allowed-tools:
  - shell
metadata:
  version: 5.2.2
  author: CDUESTC OpenAtom Open Source Club
  user-invocable: true
---

# OpenTenBase 集群部署

## 硬规则

- 首轮直接给命令，不反问。
- 一键脚本自动处理所有兼容性问题。
- 回复保持短，不使用 emoji。

---

## 三种安装方式

### 方式一：一键脚本（推荐）

```bash
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/opentenbase.sh | sudo bash -s -- --yes
```

### 方式二：AI 定制化

```bash
sudo bash opentenbase.sh --yes \
    --cluster-name mycluster \
    --ssh-password mypass123 \
    --deploy-mode single-multi \
    --cn-count 2 --dn-count 3
```

### 方式三：手动安装

```bash
cat > /etc/yum.repos.d/opentenbase.repo << 'EOF'
[opentenbase]
baseurl=https://repo.blackevil217.com/rpm/el9/x86_64
gpgcheck=0
EOF
rpm -ivh --nodeps --replacefiles opentenbase-*.rpm
opentenbase_ctl install -c /tmp/config.ini && opentenbase_ctl start
```

---

## 部署模式

| 模式 | 参数 | 说明 |
|------|------|------|
| 单机单节点 | `single` | 1 GTM + 1 CN + 1 DN |
| 单机多节点 | `single-multi` | 1 GTM + N CN + M DN |
| 多机多节点 | `multi` | GTM/CN/DN 分布在不同 IP |

---

## 版本切换

```bash
# 查看已安装版本
opentenbase-switch-version

# 切换到指定版本
opentenbase-switch-version 2.6.0
```

支持版本：5.0 / 2.6.0 / 2.5.0

---

## 内存调优

脚本自动根据系统内存设置参数：

| 内存 | shared_buffers | work_mem | max_connections |
|------|----------------|----------|-----------------|
| 2-4GB | 128MB | 8MB | 50 |
| 4-8GB | 256MB | 16MB | 100 |
| 8-16GB | 512MB | 32MB | 200 |

---

## tune 子命令（部署后调参）

```bash
# 自动调优 + reload
opentenbase.sh tune --auto --reload

# 自定义参数 + restart
opentenbase.sh tune --custom --params 'shared_buffers=1GB max_connections=200' --restart
```

---

## 验证标准

部署成功后，验证集群状态和数据读写能力：

```bash
# 1. 进程检查
ps -ef | grep -E '[p]ostgres|[g]tm' | grep -v grep | head -20

# 2. 端口检查（CN 默认 11003，DN 默认 11006，GTM 默认 11000）
ss -lntp 2>/dev/null | grep -E ':(11003|11006|11000)\b'

# 3. 使用 opentenbase 运行用户连接测试
export PGHOME=/var/lib/opentenbase/install/opentenbase/5.0
export PATH=$PGHOME/bin:$PATH
export LD_LIBRARY_PATH=$PGHOME/lib:$LD_LIBRARY_PATH

psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres -c 'SELECT version();'
psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres -c 'SELECT * FROM pgxc_node;'
psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres \
  -c "CREATE TABLE t(id int) DISTRIBUTE BY SHARD(id); INSERT INTO t VALUES(1); SELECT * FROM t; DROP TABLE t;"
```

⚠️ `opentenbase_ctl` 是 RPM 包安装方式的工具。一键脚本部署后使用 `psql` + 进程/端口检查验证。脚本部署的二进制位于 `/var/lib/opentenbase/install/opentenbase/<version>/`。

---

## 部署流程（执行时大致分五步）

```text
Step 1/6: 环境能力预检  → OS/CPU/内存/磁盘/端口/root权限
Step 2/6: 解决依赖      → 包管理器、libpq、noaffinity.so（2核CPU）
Step 3/6: 下载二进制    → 从 CDN 拉取 OpenTenBase 5.0 预编译包
Step 4/6: 集群初始化    → 创建 opentenbase 用户、数据目录、启动 GTM→CN→DN
Step 5/6: 配置优化      → 按内存设置 shared_buffers/work_mem/max_connections
Step 6/6: 最终验证      → 端口检查 + PC 连接测试
```

---

## 常见问题（脚本自动处理）

| 问题 | 脚本处理 |
|------|---------|
| el9 目录缺失 | 自动配置兼容仓库 |
| libpq.so.5 依赖 | --nodeps 跳过，运行时 LD_LIBRARY_PATH 隔离 |
| libpq-devel 冲突 | 自动卸载 |
| 2核 CPU GTM 崩溃 | 预构建 noaffinity.so 四级下载（GitHub raw 优先 → CDN → 本地编译 → 跳过），下载后 ELF 格式验证 |

---

## 资源不足处理

- 内存 < 4GB：不建议部署完整集群
- 2核 CPU：必须用 noaffinity.so
- 2TB 数据：预留 2.6TB-4TB 空间

---

## 日常运维

```bash
opentenbase_ctl status     # 查看状态
opentenbase_ctl start      # 启动
opentenbase_ctl stop       # 停止
opentenbase_ctl expand     # 扩容
opentenbase.sh test        # 完整测试
opentenbase.sh tune        # 参数调优
```