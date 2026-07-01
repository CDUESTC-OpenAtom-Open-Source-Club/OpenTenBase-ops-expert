# 配置参数参考

> 本文档覆盖：5.0 INI 配置文件详解、多拓扑配置示例、端口参考、已知问题解决方案。

---

## 5.0 INI 配置文件

### 完整模板

```ini
[instance]
name=opentenbase01          # 集群名称
type=distributed             # distributed（分布式）
package=/tmp/opentenbase-5.0.tar.gz  # 必须是 tar.gz 文件，不能是目录！

[gtm]
master=127.0.0.1            # GTM 主节点 IP

[coordinators]
master=127.0.0.1            # CN 节点 IP（多个用逗号分隔）
nodes-per-server=1          # 每台服务器上部署几个 CN

[datanodes]
master=127.0.0.1            # DN 节点 IP（多个用逗号分隔）
nodes-per-server=1

[server]
ssh-user=opentenbase        # SSH 用户（所有节点必须一致）
ssh-password=your_password  # SSH 密码（单节点本地可省略，多机必填）
ssh-port=22

[log]
level=INFO
```

### 段落说明

| 段 | 必填 | 说明 |
|----|------|------|
| `[instance]` | 是 | 集群元信息（名称、类型、安装包路径） |
| `[gtm]` | 是 | GTM 节点定义 |
| `[coordinators]` | 是 | CN 节点定义 |
| `[datanodes]` | 是 | DN 节点定义 |
| `[server]` | 是 | SSH 连接信息 |
| `[log]` | 否 | 日志级别 |

### 关键字段说明

**`package`**：
- 必须是 tar.gz 文件，不能是目录
- `excute_cp_file()` 对本地 IP 使用 `cp` 不支持目录
- 手动安装时需先打包：`cd /usr/lib/opentenbase/5.0 && tar -zcf /tmp/opentenbase-5.0.tar.gz *`

**`ssh-password`**：
- 单节点本地部署（127.0.0.1）可省略——本地 IP 走 `cp` 不走 SSH
- 多机部署必填
- 一键脚本通过 `--ssh-password` 参数自动写入

**`nodes-per-server`**：
- 每台服务器上部署几个同类节点，通常为 1

---

## 多拓扑配置示例

### 单节点（GTM + CN + DN 同机）

```ini
[gtm]
master=127.0.0.1

[coordinators]
master=127.0.0.1
nodes-per-server=1

[datanodes]
master=127.0.0.1
nodes-per-server=1
```

### 多机 3 节点（1 GTM + 1 CN + 1 DN）

```ini
[gtm]
master=192.168.1.10

[coordinators]
master=192.168.1.11
nodes-per-server=1

[datanodes]
master=192.168.1.12
nodes-per-server=1
```

### 多 DN（1 GTM + 1 CN + 3 DN）

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

### 多 CN + 多 DN（1 GTM + 2 CN + 3 DN）

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

---

## 端口参考

| 服务 | 2.5 / 2.6 | 5.0 裸机 | 5.0 Docker | 说明 |
|------|-----------|----------|------------|------|
| GTM | 6666 | 6666 | 6666 | 全局事务管理器 |
| CN | 5432 | 11003 | 5432 | 客户端连接入口 |
| DN | 15432 | 15432 | 15432/15433 | Docker 多 DN 递增 |
| Pooler | 6669 | 6669 | 6669 | 各节点需不同 IP |
| Forward | 6670 | 6670 | 6670 | 各节点需不同 IP |

### 端口速记

- 2.5/2.6 CN = **5432**
- 5.0 裸机 CN = **11003**
- 5.0 Docker CN = **5432**

### 检查端口占用

```bash
ss -tlnp | grep -E ":(11003|6666|15432|6669|6670)" || echo "端口空闲"
```

---

## 已知问题与解决方案

### 1. OSS_INSTALL_DIR 路径不匹配

`opentenbase_ctl` 硬编码 `/usr/local/install/opentenbase`，但包安装到 `/usr/lib/opentenbase/5.0/`。

```bash
sudo mkdir -p /usr/local/install
sudo ln -sf /usr/lib/opentenbase/5.0 /usr/local/install/opentenbase
```

### 2. ≤2 核 GTM 启动崩溃

GTM 线程绑核逻辑在低核机器上生成非法 cpuset。

```bash
# 编译 noaffinity.so
cat > /tmp/noaffinity.c << 'EOF'
#define _GNU_SOURCE
#include <pthread.h>
int pthread_setaffinity_np(pthread_t t, size_t s, const cpu_set_t *c) { return 0; }
EOF
gcc -shared -fPIC -o /usr/lib/opentenbase/noaffinity.so /tmp/noaffinity.c -lpthread

# 全局注入（必须，LD_PRELOAD 不会传播到 SSH 子进程）
echo "/usr/lib/opentenbase/noaffinity.so" > /etc/ld.so.preload
chmod 644 /etc/ld.so.preload
```

### 3. libpqxx.so 缺失（旧包）

当前版本已打包 libpqxx/CLI11。如遇旧包报错：

```bash
sudo cp /usr/lib/x86_64-linux-gnu/libpqxx* /usr/lib/opentenbase/5.0/lib/ 2>/dev/null || true
sudo cp /usr/lib64/libpqxx* /usr/lib/opentenbase/5.0/lib/ 2>/dev/null || true
sudo ldconfig
```

### 4. 2.5/2.6 initdb 报 `create gtm node (null)`

必须通过 `pgxc_ctl deploy` 调用 initdb，不能直接调用。

---

## 安装后目录结构

| 路径 | 用途 |
|------|------|
| `/usr/lib/opentenbase/5.0/bin/opentenbase_ctl` | 集群管理二进制 |
| `/usr/lib/opentenbase/5.0/bin/` | 其他二进制（postgres, psql 等） |
| `/usr/lib/opentenbase/5.0/lib/` | 运行时库 |
| `/var/lib/opentenbase/install/opentenbase/5.0/` | 运行时部署目录 |
| `/etc/opentenbase/5.0/` | 配置文件目录 |
| `/usr/local/install/opentenbase` | 符号链接 → `/usr/lib/opentenbase/5.0` |
| `/usr/lib/opentenbase/noaffinity.so` | GTM 2核修复 stub |

---

## 部署源仓库信息

- 仓库：`https://github.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages`
- 维护：CDUESTC 开源社团（blackEvil217 / muzimu217）
- 许可证：Apache 2.0
- 最新版本：`v5.0-p32`（2026-06-29）
- CDN 加速：脚本下载路径 `https://repo.blackevil217.com/scripts/opentenbase.sh`（Cloudflare 全球加速，国内速度提升约 150-200 倍，自动回退 GitHub raw）
- GPG 指纹：`D8B2E316E1FF88EE178703549D8FA46F3A55D5F0`
- 支持发行版：Ubuntu 18.04–25.04 / Debian 10–13 / CentOS Stream 8/9 / Rocky 8/9 / AlmaLinux 8/9 / Fedora 40 / openEuler 22.03
- 架构：x86_64 + aarch64
