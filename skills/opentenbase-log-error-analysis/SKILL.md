---
name: opentenbase-log-error-analysis
description: 分析 OpenTenBase 日志、启动失败、连接失败、节点异常、pgxc_ctl 管理工具报错和插件/SQL 执行错误。用于用户要求排查报错、查看日志、解释 ERROR/FATAL/WARNING、判断 CN/DN/GTM 或 pgxc_ctl 问题时。
allowed-tools:
  - shell
metadata:
  version: 1.7.0
  author: CDUESTC OpenAtom Open Source Club
  user-invocable: true
---

# OpenTenBase 日志与错误分析

若目标在远程 Linux，先使用 `linux-ssh-access`。默认只读分析，不启停集群、不修改配置、不清理日志。

## 最高优先级规则（强制）

**【禁止事项】- 首轮必须遵守：**

❌ **禁止创建文件**：除非用户明确说"写文件/保存报告/生成脚本"，**禁止创建任何文件**，包括但不限于：
- ❌ _meta.json、BOOT.md、CHANGELOG.md、MEMORY.md、README.md
- ❌ 启动文档、变更记录、临时脚本、诊断报告、日志摘要文件
- ❌ 任何元数据文件、记忆记录、与当前任务无关的文件

❌ **禁止冗长输出**：首轮最多 1 句初判、1 个命令块、6 条判断点。不初始化项目、不写文件、不输出装饰性符号。

❌ **禁止臆造数据**：不编造"占比60%"、"概率最高"等无统计依据数字。用"常见原因"、"优先排查"等定性描述。

❌ **禁止反问式敷衍**：用户没给日志时，不只追问日志路径；必须先给出**最小采集命令**（含pgxc_ctl状态、GTM检查、2PC检查），再让用户贴回。

✅ **首轮直接给命令**：用户报告故障 → 直接给出OpenTenBase分布式诊断命令（含pgxc_ctl、GTM、2PC检查）。

---

**信息收集策略（首轮）：**

- 用户**已提供日志**：直接分析，定位根因，给出修复命令。
- 用户**未提供日志**：先给出**分布式诊断命令清单**（见下方），等用户贴回输出后再下结论。

---

**首轮最小命令（OpenTenBase特有诊断）：**

```bash
# 1. pgxc_ctl集群状态（优先）
export PATH=/var/lib/opentenbase/install/opentenbase/5.0/bin:$PATH
pgxc_ctl monitor all 2>&1 | head -50

# 2. GTM进程和连通性（CN/DN依赖GTM）
ps -ef | grep '[g]tm' && ss -lntp | grep 6666

# 3. CN/DN节点拓扑和状态（分布式诊断必须）
psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres \
  -c "SELECT node_name,node_type,node_host,node_port,node_state FROM pgxc_node;"

# 4. 2PC残留事务检查（跨节点事务悬挂）
psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres \
  -c "SELECT gid,prepared,owner,database FROM pg_prepared_xacts;"

# 5. 进程和端口（标准端口：GTM=6666、CN=11003、DN=15432）
ps -ef | grep -E '[g]tm|[p]ostgres' | grep -v grep | wc -l
ss -lntp | grep -E '6666|11003|15432|6669|6670'

# 6. 日志关键字提取（各节点）
tail -n 50 /data/opentenbase/gtm*/gtm_log/*.log | grep -Ei 'FATAL|PANIC|binding|pthread'
tail -n 50 /data/opentenbase/cn*/pg_log/*.log | grep -Ei 'FATAL|ERROR|could not connect'
tail -n 50 /data/opentenbase/dn*/pg_log/*.log | grep -Ei 'FATAL|PANIC|WAL|invalid'
```

**分布式诊断核心判断点：**
- `pgxc_node`有节点状态≠`ready` → 该节点异常
- GTM进程不存在或日志有FATAL → **先处理GTM**（CN/DN依赖GTM）
- `pg_prepared_xacts`有残留 → **先清理2PC**（不能直接重启）
- 2核CPU且GTM日志有`binding threads failed` → 需要 noaffinity.so

---

**响应格式（强制）：**

```text
问题：<启动失败 / GTM异常 / 2PC残留 / 端口冲突 / 资源不足>
证据：<命令输出摘要或日志路径:行号>
判断：<1-2句，OpenTenBase特有根因>
风险：<低/中/高>
下一步：<需要用户贴回的输出或确认修复动作>
```

**字数控制：首轮回复控制在150字以内（不含命令块）。**

---

## 信息不足时的最小采集命令

用户只说"启动失败/节点崩了/连接不上/报错"但没给日志时，直接给：

```bash
# 1. 进程与端口（OpenTenBase 特有端口：GTM=6666、CN=11003、DN=15432、pooler=6669、forward=6670）
ps -ef | grep -E '[g]tm|[p]ostgres' | grep -v grep
ss -lntp 2>/dev/null | grep -E ':(6666|11003|15432|6669|6670)' || netstat -lntp | grep -E '6666|11003|15432|6669|6670'

# 2. OpenTenBase 集群拓扑（分布式诊断必须先看 pgxc_node）
export PATH=/var/lib/opentenbase/install/opentenbase/5.0/bin:$PATH
export LD_LIBRARY_PATH=/var/lib/opentenbase/install/opentenbase/5.0/lib:$LD_LIBRARY_PATH
psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres \
  -c "SELECT node_name,node_type,node_host,node_port,node_state FROM pgxc_node ORDER BY node_name;"

# 3. GTM 健康检查（GTM 是全局事务管理器，GTM 挂了 CN/DN 全部受影响）
ps -ef | grep '[g]tm'
tail -n 50 /data/opentenbase/gtm/gtm_log/gtm-*.log 2>/dev/null | grep -Ei 'FATAL|PANIC|binding|pthread|cpuset|error'

# 4. 2PC / prepared transaction 残留（跨节点事务悬挂会锁住整集群）
psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres \
  -c "SELECT gid,prepared,owner,database FROM pg_prepared_xacts ORDER BY prepared;"

# 5. 节点日志，按实际数据目录调整
tail -n 100 /data/opentenbase/gtm*/gtm_log/*.log 2>/dev/null | grep -Ei 'FATAL|PANIC|ERROR|could not'
tail -n 100 /data/opentenbase/cn*/pg_log/*.log 2>/dev/null | grep -Ei 'FATAL|PANIC|ERROR|could not|gtm|connection'
tail -n 100 /data/opentenbase/dn*/pg_log/*.log 2>/dev/null | grep -Ei 'FATAL|PANIC|ERROR|could not|WAL|redo|invalid'

# 6. 资源和权限
df -h
du -sh /data/opentenbase/* 2>/dev/null
ls -ld /data/opentenbase /data/opentenbase/* 2>/dev/null
```

**分布式诊断的核心判断点：**
- `pgxc_node` 中有节点状态不是 `ready` → 该节点异常
- GTM 进程不存在或 GTM 日志有 `FATAL` → **先处理 GTM**，CN/DN 依赖 GTM
- `pg_prepared_xacts` 有残留记录 → 先清理 2PC，不能直接重启节点
- CN 日志有 `could not connect to GTM` → GTM 未启动，先启动 GTM
- CN 日志有 `could not connect to node` → **同时看 DN 侧日志**，不能只看 CN
- WAL/redo 错误 → **不要手工删 WAL**，先确认备份和恢复目标
- 2 核 CPU 机器 GTM 日志有 `binding threads failed` → 需要 noaffinity.so


## OpenTenBase CN 崩溃常见原因（按排查优先级）

当用户报告 CN 节点崩溃或起不来时，按以下顺序逐项检查，每项附带具体命令：

### 1. GTM 连接失败（常见，优先排查）

CN 启动时首先连接 GTM 注册，GTM 不可用会导致 CN 直接 FATAL 退出。

```bash
# 检查 GTM 进程和端口
ps -ef | grep '[g]tm'
ss -lntp | grep 6666

# 检查 CN 日志中的 GTM 连接错误
grep -i 'gtm\|could not connect\|connection refused' <CN数据目录>/pg_log/postgresql-*.log | tail -20
```

典型日志：`FATAL: could not connect to GTM: Connection refused` → **先启动 GTM 再启动 CN**。

### 2. Forward Manager 端口冲突（单机多节点场景）

CN 和 DN 都有 forward manager，默认绑定 `127.0.0.1:6670`。单机部署时如果 CN 和 DN 共享 IP，第二个节点启动会报 `Address already in use`。

```bash
ss -lntp | grep -E '6670|6669'
ps -ef | grep '[p]ostgres' | grep forward
```

解决方案：不同节点必须用不同 IP（Docker 多容器 / 多机部署），或用 `listen_addresses` 绑定不同 IP。

### 3. 低核心数 GTM 崩溃（≤2 核 CPU）

GTM 的 `bind_service_threads()` 在 ≤2 核机器上生成空 cpuset，导致 `pthread_setaffinity_np` 返回 EINVAL。CN 因 GTM 不可用而连锁崩溃。

```bash
# 检查 CPU 核数
nproc

# 检查 GTM 日志中的崩溃关键字
grep -i 'binding threads\|pthread_setaffinity\|cpuset\|FATAL' <GTM数据目录>/gtm_log/gtm-*.log | tail -20
```

典型日志：`FATAL: binding threads failed` → 需要安装 `noaffinity.so` 桩（参考 `opentenbase-deploy` 的已知问题 #2）。

### 4. libpqxx 等动态库缺失

CN 二进制在启动时找不到依赖库。

```bash
ldd $(which postgres 2>/dev/null || find /usr/lib/opentenbase -name postgres -type f 2>/dev/null | head -1) | grep 'not found'
echo "$LD_LIBRARY_PATH"
```

典型：`error while loading shared libraries: libpqxx-6.4.so` → `export LD_LIBRARY_PATH=/usr/lib/opentenbase/5.0/lib`。

### 5. 安装路径或运行库环境不匹配

源码编译或多机分发后，运行用户的 `PATH`、`LD_LIBRARY_PATH` 或安装目录不一致，会导致 CN/DN 启动失败或工具找不到动态库。

```bash
command -v pgxc_ctl psql postgres gtm_ctl 2>/dev/null || true
echo "$PATH"
echo "$LD_LIBRARY_PATH"
ldd $(command -v postgres 2>/dev/null) | grep 'not found' || true
```

缺运行库时，先修正运行用户环境变量，例如 `export LD_LIBRARY_PATH=/data/opentenbase/install/lib:$LD_LIBRARY_PATH`，不要直接改数据目录。

### 6. 残留 PID 文件

上次非正常停止遗留的 `postmaster.pid` 导致 CN 认为已有实例在运行。

```bash
find /data/opentenbase -name 'postmaster.pid' -exec ls -la {} \;
```

→ **只报告，不自动删除**。删除 PID 文件前必须确认对应进程确实不存在。

---

## OpenTenBase DN 启动失败/崩溃常见原因

DN 问题不能只看 CN 日志。CN 中的 `could not connect to node` 常常只是表象，根因在 DN 日志、磁盘、权限、端口或 WAL 恢复。

### 1. WAL 恢复失败或 WAL 损坏

典型关键字：`WAL redo failed`、`invalid record length`、`could not locate required checkpoint record`、`requested WAL segment has already been removed`。

```bash
grep -Ein 'WAL|redo|checkpoint|invalid record|requested WAL|PANIC|FATAL' <DN数据目录>/log/*.log | tail -n 80
```

处理原则：不要手工删除 WAL；先确认备份、归档、时间线和恢复目标。物理恢复/PITR 必须单独确认。

### 2. 数据文件或索引文件损坏/缺失

典型关键字：`could not open file`、`No such file or directory`、`invalid page`、`checksum`。

```bash
grep -Ein 'could not open file|No such file|invalid page|checksum|PANIC' <DN数据目录>/log/*.log | tail -n 80
```

处理原则：先定位对象和文件；怀疑索引损坏时优先考虑在确认后重建索引，不直接改数据目录。

### 3. 未完成的 2PC / prepared transaction

典型现象：恢复后锁长期不释放、跨节点事务卡住、日志出现 `prepared transaction` 或 2PC 相关错误。

```sql
SELECT gid, prepared, owner, database
FROM pg_prepared_xacts
ORDER BY prepared;
```

处理原则：不要盲目 `COMMIT PREPARED` 或 `ROLLBACK PREPARED`；必须结合业务事务结果确认。

### 4. 磁盘满或 WAL 盘满

```bash
df -h
du -sh <DN数据目录>/* 2>/dev/null
grep -Ein 'No space left|could not write|disk full' <DN数据目录>/log/*.log | tail -n 80
```

### 5. 权限或属主错误

```bash
ls -ld <DN数据目录> <DN数据目录>/*
grep -Ein 'Permission denied|could not access|Operation not permitted' <DN数据目录>/log/*.log | tail -n 80
```

### 6. 端口冲突

```bash
ss -lntp 2>/dev/null | grep -E ':(15432|6669|6670)\b'
grep -Ein 'Address already in use|could not bind' <DN数据目录>/log/*.log | tail -n 80
```

处理原则：确认实际监听进程和节点配置，不能直接 kill。

---

## 标准流程

1. **确认目标和时间范围**：
```bash
hostname && whoami && date
```

询问或推断：启动失败、停止异常、连接失败、SQL 报错、节点间通信异常、插件部署异常，还是管理工具报错。

2. **获取状态证据**：
```bash
# 进程检查（OpenTenBase 特有：关注 GTM/CN/DN 三个角色的进程）
ps -ef | grep -E '[p]ostgres|[g]tm' | grep -v grep
# 端口检查（OpenTenBase 特有端口：11003=CN、6666=GTM、15432=DN、6669=pooler、6670=forward）
ss -lntp 2>/dev/null | grep -E ':(11003|6666|15432|6669|6670)\b'
```

本机命令不可用时，只报告原因，不自动切换工具做状态变更。

3. **定位日志**：

读取 `references/log-locations.md`。先从管理工具日志和相关节点日志开始，不无边界 `find /`。

4. **提取关键错误**：
```bash
grep -Ein 'ERROR|FATAL|PANIC|could not|failed|invalid|permission denied|No such file|already in use|Connection refused|not found' <log_file> | tail -n 50
tail -n 100 <log_file>
```

5. **关联判断**：

读取 `references/error-patterns.md`。把日志时间、节点名、节点角色、端口、进程和连接结果对齐后再下结论。涉及事务/2PC 残留、集群健康分层判断、跨节点诊断模型时，读取 `references/distributed-diagnosis-model.md`。若日志出现 `must be vacuumed` / `wraparound` / `No space left` 等**数据库拒绝写入类**故障（XID 回卷、autovacuum 停摆、表膨胀、磁盘/WAL 满），读取 `references/data-corruption-and-xid.md`。

---

## 安全边界

禁止自动执行：

```text
start、stop、restart、init、clean、kill、failover、expand、shrink
删除/截断/压缩/移动日志
修改配置
删除 postmaster.pid / gtm.pid
执行写数据库 SQL
```

需要查看系统日志时，先说明原因；若需要 root、sudo 或敏感日志，先请求用户确认。

---

## 结果格式

```text
问题类型：启动失败 / 连接失败 / 节点通信异常 / 管理工具异常 / SQL 错误 / 未确定
影响节点：<CN/DN/GTM/管理工具>
关键证据：<日志路径:行号 或 命令输出摘要>
初步判断：<一两句话，尽量指出 OpenTenBase 特有根因>
风险等级：低 / 中 / 高
建议下一步：<只读补充检查 或 需用户确认的修复动作>
```

---

## 使用示例

**示例 1：CN 起不来（GTM 未启动）**

> 用户：CN 起不来，帮我看看日志
>
> Agent：（诊断流程）
> 1. 检查进程：GTM 进程不存在
> 2. CN 日志：`FATAL: could not connect to GTM: Connection refused`
> 3. 判断：**GTM 未启动导致 CN 无法连接**（OpenTenBase 最常见 CN 崩溃原因）
> 4. 建议：先启动 GTM，再启动 CN

**示例 2：单机多节点端口冲突**

> 用户：第二个 DN 起不来
>
> Agent：（诊断流程）
> 1. 检查端口：6670 已被占用
> 2. 错误日志：`Address already in use`
> 3. 判断：**forward manager 端口冲突**（CN 和 DN 共享 127.0.0.1:6670）
> 4. 建议：单机部署多个节点必须用不同 IP，推荐用 Docker Compose 多容器方案

**示例 3：2 核机器 GTM 崩溃**

> 用户：GTM 启动就挂
>
> Agent：（诊断流程）
> 1. 检查 CPU：`nproc` → 2
> 2. GTM 日志：`FATAL: binding threads failed`
> 3. 判断：**≤2 核 CPU 触发的 pthread_setaffinity_np 崩溃**（OpenTenBase 已知缺陷）
> 4. 建议：编译安装 noaffinity.so 桩到 `/usr/lib/opentenbase/noaffinity.so` 并写入 `/etc/ld.so.preload`

---

不要只凭单条 `ERROR` 下结论。`FATAL: terminating connection due to administrator command` 在正常停止期间可能是预期现象。
