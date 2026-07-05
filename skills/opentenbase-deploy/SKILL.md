---
name: opentenbase-deploy
description: OpenTenBase 集群部署。三种方式：一键脚本（推荐）、AI定制化、手动安装。支持版本切换、多节点、内存调优、tune 参数调整。包含完整前置清理逻辑，确保白板服务器100%成功。
allowed-tools:
  - shell
metadata:
  version: 5.2.3
  author: CDUESTC OpenAtom Open Source Club
  user-invocable: true
---

# OpenTenBase 集群部署

## 硬规则

- 首轮直接给命令，不反问。
- 一键脚本自动处理所有兼容性问题。
- 一键脚本包含完整前置清理逻辑，确保白板服务器100%成功。
- 回复保持短，不使用 emoji。

---

## 三种安装方式

### 方式一：一键脚本（推荐）

```bash
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/opentenbase.sh | sudo bash -s -- install --yes
```

**特点**：
- 自动前置清理（7类残留文件）
- 自动处理所有兼容性问题
- 白板服务器直接可用，无需手动清理
- 自动识别操作系统类型（OpenCloudOS/EulerOS/CentOS/Ubuntu）

### 方式二：AI 定制化

```bash
sudo bash opentenbase.sh install --yes \
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

## 前置清理逻辑（重要）

一键脚本执行前自动清理7类残留文件，确保白板部署100%成功：

| 清理项 | 清理内容 | 说明 |
|--------|---------|------|
| **1. Socket文件** | `/tmp/.s.PGSQL.*` `/tmp/.s.GTM.*` `/tmp/.s.PGPOOL.*` `/tmp/.s.*.lock` `/tmp/stargate.lock` | 防止旧socket干扰新进程启动 |
| **2. PID文件** | `gtm.pid` `postmaster.pid` (find递归清理) | 防止进程状态残留 |
| **3. 数据目录** | `/var/lib/opentenbase/{ver}/gtm/coord0001/dn0001` | 修正命名，清理完整目录 |
| **4. 日志文件** | `/var/lib/opentenbase/pgxc_ctl/pgxc_log/*` | 防止日志文件残留 |
| **5. 临时文件** | `/tmp/opentenbase-*.rpm` `/tmp/opentenbase-*.tar.gz` `/tmp/deploy*.log` | 防止下载文件残留 |
| **6. SSH配置** | `/var/lib/opentenbase/.ssh/known_hosts` | 防止SSH认证问题 |
| **7. 配置文件** | `/var/lib/opentenbase/pgxc_ctl/pgxc_ctl.conf` `pgxc_ctl_bash` | 防止配置状态残留 |

**验证案例**：
- 清理前：15个socket文件 + 3个PID文件残留
- 清理后：白板部署成功（31进程）
- 端口监听：6666/5432/15432正常
- 数据库功能：建表/读写测试通过

**相关Commit**：
- 83482fb：完善前置清理逻辑（7类文件）
- 2cf7631：首次修复GTM socket清理bug

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
# 1. 进程检查（应为31进程）
ps aux | grep -E 'gtm|postgres' | grep opentenbase | grep -v grep | wc -l

# 2. 端口检查（标准端口：GTM=6666, CN=5432, DN=15432）
ss -tlnp | grep -E '6666|5432|15432'

# 3. 数据库连接测试
export LD_LIBRARY_PATH=/usr/lib/opentenbase/5.0/lib
/usr/lib/opentenbase/5.0/bin/psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres -c 'SELECT version();'

# 4. 分布式表读写测试
/usr/lib/opentenbase/5.0/bin/psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres \
  -c "CREATE TABLE verify_test(id INT, msg TEXT) DISTRIBUTE BY SHARD(id); \
      INSERT INTO verify_test VALUES(1, '白板部署验证'); \
      SELECT * FROM verify_test; \
      DROP TABLE verify_test;"
```

**验证要点**：
- 进程数：31个（GTM 1个 + Coordinator主进程 + 子进程 + Datanode主进程 + 子进程）
- 端口监听：6666 (GTM), 5432 (Coordinator), 15432 (Datanode)
- 数据库功能：建表、INSERT、SELECT、DROP均正常

---

## 部署流程（执行时六步）

```text
Step 1/6: 环境能力预检  → OS/CPU/内存/磁盘/端口/root权限
Step 2/6: 解决依赖      → 包管理器、libpq、noaffinity.so（2核CPU）
Step 3/6: 下载二进制    → 从 CDN 拉取 OpenTenBase 5.0 预编译包
Step 4/6: 集群初始化    → 创建 opentenbase 用户、数据目录、启动 GTM→CN→DN
Step 5/6: 配置优化      → 按内存设置 shared_buffers/work_mem/max_connections
Step 6/6: 最终验证      → 进程/端口检查 + 数据库连接测试
```

---

## 常见问题（脚本自动处理）

| 问题 | 脚本处理 |
|------|---------|
| el9 目录缺失 | 自动配置兼容仓库 |
| libpq.so.5 依赖 | --nodeps 跳过，运行时 LD_LIBRARY_PATH 隔离 |
| libpq-devel 冲突 | 自动卸载 |
| 2核 CPU GTM 崩溃 | 预构建 noaffinity.so 四级下载（GitHub raw 优先 → CDN → 本地编译 → 跳过），下载后 ELF 格式验证 |
| Socket文件残留 | 自动清理7类残留文件（PGSQL/GTM/PGPOOL/PID/日志/临时/SSH） |
| OpenCloudOS未识别 | PR #72已合并，自动识别并使用pgxc_ctl |

---

## 工具选择说明

OpenTenBase 5.0 提供两种集群管理工具：

| 工具 | 状态 | 使用场景 |
|------|------|----------|
| **pgxc_ctl** | ✅ 已验证 | 当前推荐使用，一键脚本默认 |
| **opentenbase_ctl** | ⏳ 待验证 | 端口分配bug已修复，待完整RPM编译后测试 |

**当前方案**：
- 一键脚本自动识别操作系统，选择合适工具
- OpenCloudOS/EulerOS：自动使用pgxc_ctl
- CentOS/Ubuntu：可使用opentenbase_ctl（待完整验证）

---

## 资源不足处理

- 内存 < 4GB：不建议部署完整集群
- 2核 CPU：必须用 noaffinity.so
- 2TB 数据：预留 2.6TB-4TB 空间

---

## 日常运维

```bash
# pgxc_ctl 工具（推荐）
export PATH=/usr/lib/opentenbase/5.0/bin:$PATH
pgxc_ctl monitor all     # 查看状态
pgxc_ctl start all       # 启动
pgxc_ctl stop all        # 停止

# 一键脚本运维命令
opentenbase.sh status    # 快速自检（端口/进程/连接）
opentenbase.sh test      # 完整验证（建表/读写/分片）
opentenbase.sh tune      # 参数调优
```

---

## 白板部署验证流程

确保一键脚本在干净环境100%成功：

1. **彻底清理**：`pkill -u opentenbase; rm -rf /var/lib/opentenbase/* /usr/lib/opentenbase/*; userdel -r opentenbase`
2. **运行脚本**：`curl -sSL ... | bash -s -- install --yes`
3. **验证进程**：31进程，端口6666/5432/15432监听
4. **验证功能**：建表、INSERT、SELECT、DROP测试通过

**验证记录**：
- 服务器A (162.14.74.145)：✅ 31进程，正常运行
- 服务器B (150.158.77.134)：✅ 31进程，白板部署成功