# 备份策略、WAL 归档、PITR 与跨节点一致性

本文件提供 OpenTenBase 分布式备份的**策略规划层**：分层备份组合、WAL 归档、物理基础备份、PITR 恢复框架、以及跨节点时间点一致性。
它给出可落地的命令与参数，但所有覆盖性/物理级操作在执行前必须获得用户明确确认，且命令中的路径、端口、版本相关语法必须结合当前集群核对。

---

## 1. 先讲清楚：为什么分布式备份不能只靠 pg_dumpall

`pg_dumpall` 定时逻辑备份只是最基础的一层，它有三个硬伤，恰恰是生产库最怕的：

- **无时间点恢复**：只能回到"上一次全量备份"的时刻，两次备份之间的数据全丢（RPO 等于备份间隔，可能是 24 小时）。
- **无跨节点一致性保证**：多个 DN 上的逻辑备份不是同一个全局事务时刻，恢复后可能出现分片间数据错位。
- **大库不可行**：TB 级数据逻辑导出/导入耗时以小时甚至天计，RTO 无法接受。

所以一套**认真的备份策略**至少要三层叠加：**逻辑备份（对象级/迁移）+ 物理基础备份（快速整库恢复）+ WAL 归档（时间点恢复）**。

---

## 2. 分层备份策略矩阵

| 层次 | 手段 | 作用 | 典型频率 | 覆盖的恢复目标 |
|---|---|---|---|---|
| L1 逻辑备份 | `pg_dump` / `pg_dumpall`（经 CN） | 对象级恢复、跨版本迁移、误删单表找回 | 每日/每周 | 单库、单 schema、单表 |
| L2 物理基础备份 | 每节点 `pg_basebackup` | 快速整节点/整库恢复，RTO 低 | 每日/每周全量 | 整节点、整集群基线 |
| L3 WAL 归档 | `archive_mode` + `archive_command` | 时间点恢复（PITR），把 RPO 压到分钟级 | 持续 | 任意时间点 |
| L4 GTM 备份 | GTM 数据目录 + 拓扑元数据 | 恢复全局事务/序列状态与节点拓扑 | 随物理备份 | 全局一致性恢复的前提 |

**RTO/RPO 参考**：
- 只有 L1：RPO = 备份间隔，RTO = 逻辑导入耗时（大库很长）。
- L2 + L3：RPO ≈ WAL 归档延迟（分钟级），RTO = 恢复基础备份 + 重放 WAL（远快于逻辑导入）。
- 生产库**推荐 L2+L3+L4 组合**，L1 作为对象级找回和迁移补充。

---

## 3. WAL 归档配置（PITR 的前提，每个 DN / CN / GTM 节点都要配）

分布式集群里，**每个数据节点都有自己的 WAL 流**，PITR 要求所有参与节点都开启归档。

在每个节点的 `postgresql.conf`（或经 `pgxc_ctl` / `pgxc_ctl` 下发的配置）中：

```ini
wal_level = replica            # 或更高；物理备份+归档的最低要求
archive_mode = on
archive_command = 'test ! -f /data/wal_archive/%f && cp %p /data/wal_archive/%f'
# 生产建议用带校验和远端存储的归档脚本，而非本地 cp
max_wal_senders = 10           # 若同时用流复制
```

配置后需**重启该节点**使 `archive_mode` 生效（`wal_level`、`archive_mode` 是重启级参数）。

**只读核对归档是否真正生效**（不改任何东西）：

```sql
SHOW archive_mode;
SHOW archive_command;
SELECT * FROM pg_stat_archiver;   -- archived_count 应持续增长，failed_count 应为 0
```

```bash
ls -lt /data/wal_archive/ | head    # 确认归档文件在持续落地
```

> 修改 `archive_mode` / `wal_level` 并重启节点属于高风险操作，必须先获得用户确认，并在业务低峰逐节点滚动执行。

---

## 4. 物理基础备份（pg_basebackup，每节点执行）

物理备份要**逐节点**做，每个 CN/DN 各产出一份基础备份，配合各自的 WAL 归档。

```bash
# 在目标节点上，以 OpenTenBase 运行用户执行；<node_port> 为该节点端口
pg_basebackup \
  -h 127.0.0.1 -p <node_port> -U <repl_user> \
  -D /backup/basebackup/<node_name>_$(date +%Y%m%d) \
  -Fp -Xs -P -c fast
# -Xs 流式抓取备份期间产生的 WAL；-c fast 立即做检查点
```

关键约束：
- 每个节点的基础备份要**和该节点的归档 WAL 一一对应**，不能混用。
- 记录每份基础备份的**起始 LSN / 时间戳**，PITR 时按最早可用基线选择。
- 备份存储要与数据盘分离，避免同盘故障双丢。

### GTM 节点备份（分布式必需）

GTM 存储全局事务状态和序列，恢复时必须与各节点时间点匹配。**GTM 目录备份是分布式备份策略的必要组成部分**：

```bash
# GTM 数据目录备份（简单文件级即可）
GTM_DATA=/data/opentenbase/gtm
BACKUP_DIR=/backup/gtm/gtm_$(date +%Y%m%d)

# 停止 GTM 或确保一致时刻（建议随全集群备份窗口执行）
mkdir -p "$BACKUP_DIR"
cp -a "$GTM_DATA"/* "$BACKUP_DIR/"

# 记录备份时刻的 pgxc_node 拓扑快照（恢复时需要一致）
export PATH=/var/lib/opentenbase/install/opentenbase/5.0/bin:$PATH
psql -h <CN_IP> -p 11003 -U <user> -d postgres \
  -c "SELECT node_name,node_type,node_host,node_port FROM pgxc_node ORDER BY node_name;" \
  > "$BACKUP_DIR/pgxc_node_snapshot.txt"
```

**恢复时：** GTM 恢复顺序、拓扑一致性检查见第 6 节。

**只读评估空间与节点清单**（规划阶段先跑）：

```sql
SELECT node_name, node_type, node_host, node_port FROM pgxc_node ORDER BY node_type, node_name;
```

```bash
df -h /backup          # 确认备份目标空间充足
du -sh <data_dir>      # 估算单节点数据量
```

---

## 5. 跨节点时间点一致性（BARRIER —— 分布式 PITR 的核心）

单机 PostgreSQL 的 PITR 恢复到某个时间点即可。但分布式集群里，**各节点独立重放 WAL 到"同一墙上时钟时间"并不能保证全局事务一致**——一个跨节点事务可能在 DN1 已提交、在 DN2 还没到。

OpenTenBase 继承了 Postgres-XC/XL 血统的 **BARRIER（屏障）机制**来解决这个问题：在集群上打一个全局一致性点，所有节点的 PITR 都恢复到**同一个 barrier**，从而保证跨节点一致。

```sql
-- 在 CN 上创建一个命名 barrier（会协调所有节点，写入各自 WAL）
CREATE BARRIER 'daily_consistent_20260703';
```

> 语法与是否需要额外参数随 OpenTenBase 版本略有差异，执行前用 `\h CREATE BARRIER` 或版本文档核对。若当前版本不支持 CREATE BARRIER，则退化为"所有节点恢复到同一 recovery_target_time"，并需在恢复后额外校验跨分片一致性（见第 7 节）。

**运维习惯**：定期（如每小时）打一个 barrier，PITR 时优先恢复到**目标时间点之前最近的 barrier**，一致性最稳。

---

## 6. PITR 恢复框架（逐节点，恢复到同一 barrier / 时间点）

> 以下为**恢复流程框架**，涉及停库、覆盖数据目录、写 recovery 配置，全部为高危操作。Agent 不得自动执行，必须由用户逐步确认。这里给出正确的**顺序和参数**，避免用户遗漏关键步骤。

对**每一个节点**（GTM → DN → CN 顺序，或按版本恢复文档要求的顺序）：

1. **停止该节点**（确认用户已知业务中断）。
2. **备份当前数据目录**（`mv` 到旁边，绝不直接删——留回退路）。
3. **展开基础备份**到数据目录。
4. **投放归档 WAL**：确保 `restore_command` 能读到第 3 步基线之后的所有归档 WAL。
5. **写 recovery 配置**：

```ini
# postgresql.conf（PG12+ 恢复配置合并到主配置，并需 recovery.signal 文件）
restore_command = 'cp /data/wal_archive/%f %p'
recovery_target_name = 'daily_consistent_20260703'   # 优先按 barrier 名恢复
# 或按时间点：recovery_target_time = '2026-07-03 02:00:00+08'
recovery_target_action = 'promote'
```

```bash
touch <data_dir>/recovery.signal   # PG12+ 触发恢复模式
```

6. **启动节点**，观察日志确认重放到目标点并 promote。
7. 全部节点恢复后，做**跨节点一致性验证**（第 7 节）再对外提供服务。

关键红线：
- **所有节点必须恢复到同一 barrier / 时间点**，否则全局不一致。
- GTM 状态与节点拓扑（`pgxc_node`）必须与恢复时点匹配，否则路由错乱。
- 恢复顺序、`recovery_target_*` 语法随版本不同，务必核对当前版本恢复文档。

---

## 7. 恢复后的跨节点一致性验证（不可跳过）

物理/PITR 恢复"成功启动"不等于数据正确，必须验证：

```sql
-- 1. 拓扑完整：节点数量、类型、端口与恢复前一致
SELECT node_name, node_type, node_host, node_port FROM pgxc_node ORDER BY node_type, node_name;

-- 2. 无残留的分布式 prepared 事务（2PC 悬挂会破坏一致性）
SELECT gid, prepared, owner, database FROM pg_prepared_xacts ORDER BY prepared;

-- 3. 关键分片表行数抽样比对（在 CN 上查全局，与业务预期比对）
SELECT count(*) FROM <关键业务表>;

-- 4. 序列/全局对象未回退（GTM 恢复正确的标志）
SELECT last_value FROM <关键序列>;
```

```bash
# 5. 各节点日志无 recovery / consistency 相关 ERROR
grep -iE 'recovery|consisten|barrier|FATAL|PANIC' <各节点log>
```

任一项异常 → 停止对外服务，回退到第 6 步第 2 步保存的原数据目录，并升级为人工方案。

---

## 8. 按集群规模的策略推荐（可直接作为方案输出模板）

**小集群 / 非核心库**：
- L1 每日 `pg_dumpall` 逻辑全量 + 保留 7 天。
- 可选 L3 WAL 归档，把 RPO 从 1 天压到分钟。

**中大型 / 核心生产库（推荐）**：
- L2 每周一次各节点 `pg_basebackup` 全量基线。
- L3 持续 WAL 归档到独立存储，保留覆盖两个全量周期。
- L4 随基础备份一并备份 GTM 数据目录与 `pgxc_node` 拓扑快照。
- 每小时 `CREATE BARRIER` 打全局一致性点。
- L1 每日逻辑备份作为对象级找回与迁移补充。
- **每季度至少一次真实恢复演练**（见 `restore-verify.md`），记录实测 RTO/RPO。
- **安全加固**：
  - 备份目录权限 700，文件权限 600
  - 使用 `.pgpass` 而非环境变量/命令行传密码
  - 备份存储与数据盘物理分离

**输出方案时必须一并给出**：备份存储位置与容量、保留策略、归档监控告警（`pg_stat_archiver.failed_count`）、演练计划、安全加固检查项。只给"跑个 pg_dumpall 定时任务"不算完整策略。

---

## 9. 安全加固检查项（所有备份方案必查）

### 9.1 备份文件权限

```bash
# 备份目录：仅运行用户可访问
chmod 700 /backup
chown <opentenbase_user>:<opentenbase_user> /backup

# 备份文件：仅所有者可读写
chmod 600 /backup/*.dump
chmod 600 /backup/basebackup/*

# 审计：找出权限不当的文件
find /backup -type f \( ! -user <opentenbase_user> -o ! -perm 600 \) -ls
```

### 9.2 密码安全

**禁止：**
```bash
# 错误：密码暴露在进程列表、日志、脚本中
PGPASSWORD='Secret123' pg_dump ...
export PGPASSWORD='Secret123'
```

**正确：** 使用 `.pgpass` 文件：
```bash
cat > ~/.pgpass << 'EOF'
127.0.0.1:11003:*:opentenbase:Secret123
EOF
chmod 600 ~/.pgpass

# 之后无需密码参数
pg_dump -h 127.0.0.1 -p 11003 -U opentenbase -d mydb ...
```

### 9.3 备份存储分离

```bash
# 检查数据盘和备份盘是否分离
df -h /data /backup
# 必须挂载在不同设备上，否则单盘故障导致数据+备份双丢
```

### 9.4 网络与访问控制

- 备份服务器与数据库服务器网络隔离
- 备份传输使用加密通道（SSH / TLS）
- 定期审计备份服务器的访问日志

---
