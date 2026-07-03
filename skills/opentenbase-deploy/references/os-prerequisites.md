# 操作系统前置检查与内核调优

> 本文件补齐 deploy 一直缺失的一层：现有前置条件止步于**内存/磁盘/OS 发行版**，
> 但 OpenTenBase 是 PostgreSQL 内核的分布式数据库，**不做 OS 级调优会直接踩雷**：
> - 透明大页（THP）开启 → 内存抖动、延迟毛刺
> - `shmmax/shmall` 过小 → 大共享内存的 Coordinator 起不来
> - 文件描述符/进程数限制过低 → 高连接下 "too many open files"
> - **NTP 不同步 → GTM 全局时间戳错乱**，分布式事务出诡异错误（troubleshooting 里的 `invalid global timestamp` 即此类）
>
> 所有检查项分为【检查】（只读）和【建议修改】（需 root，改前先确认）。默认只做检查+给建议，不擅自改系统。

## 一键只读体检脚本

先跑这段（纯只读，不改任何配置），拿到全景再决定改什么：

```bash
echo "===== OS 前置体检 ====="
echo "--- 1. 发行版/内核 ---"
cat /etc/os-release | grep -E '^(NAME|VERSION)=' ; uname -r
echo "--- 2. 内存/CPU ---"
free -h ; nproc
echo "--- 3. 透明大页 THP（期望 [never]）---"
cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null
cat /sys/kernel/mm/transparent_hugepage/defrag 2>/dev/null
echo "--- 4. 共享内存内核参数 ---"
sysctl kernel.shmmax kernel.shmall kernel.shmmni 2>/dev/null
echo "--- 5. 信号量 ---"
sysctl kernel.sem 2>/dev/null
echo "--- 6. 网络/连接 backlog ---"
sysctl net.core.somaxconn net.ipv4.tcp_max_syn_backlog 2>/dev/null
echo "--- 7. 内存策略 ---"
sysctl vm.overcommit_memory vm.overcommit_ratio vm.swappiness vm.dirty_ratio vm.dirty_background_ratio 2>/dev/null
echo "--- 8. 文件描述符 / 进程数限制 ---"
ulimit -n ; ulimit -u
grep -E 'nofile|nproc' /etc/security/limits.conf 2>/dev/null | grep -v '^#' || echo "(limits.conf 无显式配置)"
echo "--- 9. 时间同步（关键：GTM 依赖）---"
timedatectl 2>/dev/null | grep -Ei 'synchronized|NTP' || true
chronyc tracking 2>/dev/null | grep -Ei 'Leap|System time' || \
  ntpq -p 2>/dev/null | head -3 || echo "(未检测到 chrony/ntpd，NTP 可能未配置)"
echo "--- 10. SELinux / 防火墙 ---"
getenforce 2>/dev/null || echo "(无 SELinux)"
systemctl is-active firewalld 2>/dev/null || systemctl is-active ufw 2>/dev/null || echo "(防火墙未激活或未安装)"
echo "===== 体检结束 ====="
```

## 判读标准与建议值

| 检查项 | 期望/推荐 | 不达标后果 | 建议动作 |
|---|---|---|---|
| **THP** | `[never]` | 内存回收抖动、TP 延迟毛刺 | 关闭 THP（见下） |
| `kernel.shmmax` | ≥ 物理内存的 50%（字节） | 大共享内存 CN 启动失败 | 调大 |
| `kernel.shmall` | ≥ shmmax/页大小(4096) | 同上 | 调大 |
| `vm.overcommit_memory` | `2`（生产建议） | OOM Killer 误杀 postgres 进程 | 设 2 + ratio |
| `vm.swappiness` | `10`（低） | 频繁换页拖慢数据库 | 调低 |
| `vm.dirty_ratio` | `10` / `dirty_background_ratio 3` | 脏页堆积后集中刷盘卡顿 | 调低 |
| `net.core.somaxconn` | ≥ `1024` | 高并发连接被拒 | 调大 |
| `ulimit -n`（nofile） | ≥ `65536` | high conn 下 "too many open files" | limits.conf 提高 |
| `ulimit -u`（nproc） | ≥ `65536` | 无法 fork 新后端进程 | limits.conf 提高 |
| **NTP 同步** | `synchronized: yes` | **GTM 时间戳错乱 / 分布式事务异常** | 装并启用 chrony |
| SELinux | `Permissive`/`Disabled` 或已配策略 | 端口/文件访问被拦 | 视安全策略处理 |

## 建议修改（需 root，改前请向用户确认）

> 以下会修改系统配置。**属于中风险操作，执行前必须让用户确认**，并说明改了什么、如何回滚。

### 1. 关闭透明大页（THP）

```bash
# 临时（立即生效，重启失效）
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/defrag
# 永久（写入 rc.local 或 grub，重启保持）——rc.local 方式：
cat <<'EOF' | sudo tee /etc/tuned/no-thp.sh >/dev/null
#!/bin/sh
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
EOF
```

### 2. 内核参数（写入 /etc/sysctl.d/99-opentenbase.conf）

```bash
# 先按物理内存算 shmmax（示例：取物理内存的 50%）
MEM_BYTES=$(free -b | awk '/Mem:/{print $2}')
SHMMAX=$((MEM_BYTES / 2))
SHMALL=$((SHMMAX / 4096))

sudo tee /etc/sysctl.d/99-opentenbase.conf >/dev/null <<EOF
kernel.shmmax = ${SHMMAX}
kernel.shmall = ${SHMALL}
kernel.shmmni = 4096
kernel.sem = 250 512000 100 2048
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 4096
vm.overcommit_memory = 2
vm.overcommit_ratio = 90
vm.swappiness = 10
vm.dirty_ratio = 10
vm.dirty_background_ratio = 3
EOF

sudo sysctl -p /etc/sysctl.d/99-opentenbase.conf
```

> 回滚：删除该文件后 `sudo sysctl --system`，或重启。
> `vm.overcommit_memory=2` 较严格，内存紧张的小机器可先用默认 `0`，避免影响低内存 DN 场景。

### 3. 文件描述符 / 进程数限制

```bash
# 假设 OpenTenBase 运行用户为 opentenbase，按实际改
sudo tee /etc/security/limits.d/99-opentenbase.conf >/dev/null <<'EOF'
opentenbase  soft  nofile  65536
opentenbase  hard  nofile  65536
opentenbase  soft  nproc   65536
opentenbase  hard  nproc   65536
EOF
# 重新登录该用户 shell 后 ulimit -n 生效；systemd 服务另需在 unit 里设 LimitNOFILE
```

### 4. 时间同步（GTM 强依赖，务必配置）

```bash
# RPM 系
sudo dnf install -y chrony && sudo systemctl enable --now chronyd
# APT 系
sudo apt install -y chrony && sudo systemctl enable --now chrony
# 验证已同步（关键）
chronyc tracking | grep -E 'Leap|System time|Stratum'
timedatectl | grep -i synchronized
```

> **多机部署必须全节点时间同步**。GTM 依赖单调递增的全局时间戳分配 XID，
> 节点间时钟漂移会导致 `invalid global timestamp`、事务可见性异常、2PC 卡住等诡异问题——
> 这类故障排查极其困难，务必在部署前就把 NTP 打通。

## 部署前置检查清单（多机拓扑，逐台执行）

- [ ] 内存 ≥ 4GB（完整集群 Coordinator 硬性要求）
- [ ] 磁盘 ≥ 10GB 可用
- [ ] THP 已关闭（`[never]`）
- [ ] `kernel.shmmax/shmall` 已按内存调大
- [ ] `vm.overcommit_memory` 已按场景设置
- [ ] `ulimit -n / -u` ≥ 65536
- [ ] **所有节点 NTP 已同步**（`timedatectl` synchronized: yes）
- [ ] 节点间 SSH 互信已配（走 `linux-ssh-access`）
- [ ] 防火墙已放行：6666(GTM) / 11003(CN) / 15432(DN)（见 `deploy-multi-node.md`）
- [ ] SELinux 已按安全策略处理

> 与 `deploy-multi-node.md` 的"Step 1 各节点安装 + 系统准备"衔接：**先过本清单，再装包**。
