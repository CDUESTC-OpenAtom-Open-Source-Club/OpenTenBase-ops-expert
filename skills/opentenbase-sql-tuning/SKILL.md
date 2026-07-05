---
name: opentenbase-sql-tuning
description: 分析和优化 OpenTenBase SQL 性能。适用于慢 SQL、执行计划解读、分布键选择、跨 DN Join、广播/重分布、数据倾斜、索引和统计信息排查。默认只读分析，避免把 OpenTenBase 当单机 PostgreSQL 调优。
allowed-tools:
  - shell
metadata:
  version: 1.4.0
  author: CDUESTC OpenAtom Open Source Club
  user-invocable: true
---

# OpenTenBase SQL 调优

若目标数据库在远程 Linux，先使用 `linux-ssh-access`。若集群状态不确定，先使用 `opentenbase-cluster-ops` 只读确认 CN/DN/GTM 可用。

本 Skill 负责 SQL 性能分析和调优建议，不负责集群启停、用户授权、备份恢复或插件治理。

## 最高优先级规则

**用户报告慢 SQL 问题时，直接给出 OpenTenBase 分布式诊断框架。不说"我是XX专家"、不介绍技能体系、不解释路由过程。直接切入诊断。**

**信息完整性判断：**

1. **用户已提供完整 SQL**：直接给出 EXPLAIN 命令和分布式判断框架。
2. **用户提供 SQL 被截断/不完整**：必须先指出 SQL 不完整，给出截断位置的判断方法，要求用户补充完整后再继续分析。不要假装完整 SQL 去分析。
3. **用户没给 SQL**：先给最小采集命令，再列出 OpenTenBase 分布式场景下最常见的慢查询根因。

**SQL 截断判断方法：**

```sql
-- 检查 SQL 是否完整：
-- 1. 括号是否匹配：左括号数量 = 右括号数量
-- 2. 关键字是否完整：SELECT/FROM/WHERE/JOIN/ORDER BY 等
-- 3. 字符串是否闭合：引号/单引号成对
-- 4. 子查询是否闭合
-- 5. 以分号结尾（如果有）
```

**不要**回复成"请提供 SQL 语句我再帮你分析"就结束了——这会被评为"缺乏专业性"。

**零文件规则：** 慢 SQL 诊断只输出对话内容和 SQL/命令。除非用户明确说"写文件/保存报告/生成脚本"，禁止创建或更新任何与当前任务无关的文件。

**简洁规则：** 首轮回复控制为"初判 → 命令 → 怎么看 → 下一步"，不要输出长篇报告。

**长度规则：** 首轮最多 1 段初判、1 个命令块、6 条判断点。不要生成报告、不要写文件、不要输出装饰性符号。首轮不要把后续章节里的多个示例命令块全部复制给用户，只选择最小必需命令并放在同一个代码块。

---

## 运行用户

执行 `psql`、查看工具或读取 OpenTenBase 环境前，先确认 OpenTenBase 运行用户。不要在 root 下直接判断工具是否存在。

若用户只提供 root 账号，先询问 OpenTenBase 运行用户，并请求允许：

```bash
su - <opentenbase_user>
```

## 基本原则

- 默认只读分析，不直接改 SQL、索引、统计信息或参数。
- 应用通常连接 CN；分析计划时必须关注 SQL 是否被下推到 DN、是否广播、是否重分布、是否集中到 CN。
- 不要只按单机 PostgreSQL 思路看索引和扫描方式；同时检查分布方式、分布键、Join 键、数据倾斜和跨节点事务。
- `EXPLAIN` 可默认使用；`EXPLAIN ANALYZE` 会真实执行 SQL，必须先确认 SQL 类型和影响。
- 对 `INSERT/UPDATE/DELETE/MERGE/DDL` 不自动执行 `EXPLAIN ANALYZE`。

## 信息不足时的首轮命令

用户只说"SQL 慢/查询慢/执行很慢"但没给 SQL 时，直接给下面这组命令，让用户把输出贴回。首轮只输出这 1 个 SQL 块；如果已知表名，把表分布、倾斜和 DN 级诊断也放在同一个块里。

```sql
-- 1. 版本
SELECT version();

-- 2. 拓扑
SELECT node_name, node_type, node_host, node_port
FROM pgxc_node
ORDER BY node_name;

-- 3. 慢 SQL 的只读计划，不真实执行 SQL
EXPLAIN (VERBOSE, COSTS)
<慢SQL>;

-- 4. 确认 SQL 可真实执行后再跑
EXPLAIN (ANALYZE, VERBOSE, BUFFERS)
<慢SQL>;

-- 5. 活动会话和等待
SELECT pid, state, wait_event_type, wait_event, query
FROM pg_stat_activity
WHERE state <> 'idle'
ORDER BY query_start NULLS LAST;

-- 6. 已知表名时补充：查看分布信息
SELECT c.relname, xc.pclocatortype, xc.discolnums
FROM pg_class c
JOIN pgxc_class xc ON xc.pcrelid = c.oid
WHERE c.relname = '<表名>';

-- psql 中查看表结构和索引
\d+ <表名>

-- 按疑似分布键检查倾斜
SELECT <分布键>, count(*)
FROM <表名>
GROUP BY <分布键>
ORDER BY count(*) DESC
LIMIT 20;

-- 如果版本支持 xc_node_id，直接看各 DN 行数分布
SELECT xc_node_id, count(*)
FROM <表名>
GROUP BY xc_node_id
ORDER BY count(*) DESC;

-- DN 级诊断：替换 dn001 为 pgxc_node 中的 DN 名称
EXECUTE DIRECT ON (dn001) 'SELECT pg_size_pretty(pg_database_size(current_database()))';
```

首轮判断点最多 6 条：

- 分布键是否出现在过滤条件或 JOIN 条件中；
- 是否访问全部 DN，尤其是 `Remote Subquery Scan on all datanodes`；
- 是否出现 `Broadcast` / `Redistribute`，并判断 JOIN 键与分布键是否一致；
- 过滤、聚合、排序是否下推到 DN，还是集中在 CN 做 Sort/Aggregate/Distinct；
- 是否存在数据倾斜，可用 `xc_node_id` 或疑似分布键计数验证；
- 统计信息或索引是否过期，必要时建议 `ANALYZE <表名>;`，但未经确认不执行。

## 实用调优经验（基于测试验证）

以下来自实际部署和测试验证：

### 复制表 JOIN 性能

复制表 (REPLICATION) 适合参与 JOIN 的字典表/维表（数据量小、更新少）。测试验证：
- `orders` (SHARD) JOIN `products` (REPLICATION) → Hash Join 在 DN 本地完成 ✅
- `orders` (SHARD) JOIN `users` (REPLICATION) → 同上
- 复制表行数：`products`=10行, `users`=5行，完全无广播开销

**原则：** 复制表行数不应超过 1 万行。超过 1 万行的表应考虑改为 SHARD，否则每次 JOIN 都会在 DN 上做全表扫描。

### SHARD 表未指定分布键时的倾斜问题

```sql
CREATE TABLE op_log (id serial, order_id int, action text, created_at timestamp)
DISTRIBUTE BY SHARD(order_id);  -- order_id 不是 UNIQUE，可能倾斜
```

各 DN 行数比较：
```sql
SELECT xc_node_id, count(*) FROM op_log GROUP BY xc_node_id ORDER BY xc_node_id;
```

如果分布键值存在热点（如某几个 order_id 占了大部分行），需要调整分布键设计。

## 分布式慢查询根因优先级（OpenTenBase 特有）

当用户无法提供完整 SQL 时，按以下优先级引导排查。这些都是**单机 PostgreSQL 不存在的**分布式特有的慢查询根因：

### 1. 分布键选择不当 → 查询访问全部 DN（最普遍）

**现象**：`WHERE` 条件不含分布键，或分布键值分布严重不均。
**检查**：
```sql
-- 查看表分布方式
SELECT c.relname, xc.pclocatortype, xc.discolnums
FROM pg_class c JOIN pgxc_class xc ON xc.pcrelid = c.oid
WHERE c.relname = '<table_name>';
```
**判断**：如果 `pclocatortype='H'`（HASH 分布）但 WHERE 条件不带分布键 → **全 DN 扫描**。

### 2. JOIN 导致广播或数据重分布

**现象**：`EXPLAIN` 计划中出现 `Remote Subquery Scan on all datanodes` + `Broadcast` 节点。
**判断**：
- `Remote Subquery Scan on all datanodes`：SQL 被发到所有 DN，通常说明过滤条件不能按分布键路由。
- `Broadcast`：小表被广播到所有 DN → 小表是否真的小？（>10 万行可能就需要考虑分片）
- `Redistribute`：数据需要按 JOIN 键重新分布 → JOIN 键和分布键不一致
**优化方向**：让 JOIN 键 = 分布键，或把小表改为复制表。

### 3. 数据倾斜 → 个别 DN 负载过高

**现象**：某些 DN 数据量远超其他 DN。
**检查**：
```sql
-- 各 DN 上该表的大致大小（需要到各 DN 上执行）
SELECT pg_size_pretty(pg_relation_size('<table_name>'));
```
**判断**：若某 DN 的表是其他 DN 的 3 倍以上 → 数据倾斜，分布键选择有问题。

### 4. CN 汇总成为瓶颈

**现象**：`EXPLAIN` 计划中 CN 层有大量 Sort/Aggregate 操作。
**判断**：`GROUP BY` 的列不是分布键 → 数据需要从各 DN 汇集到 CN 做聚合。
**优化方向**：让 GROUP BY 列包含分布键，或使用窗口函数推到 DN 执行。

### 5. 跨节点事务等待

**现象**：`pg_stat_activity` 中大量 `waiting` 状态，涉及 GTM 事务号分发。
**检查**：
```sql
SELECT pid, state, wait_event_type, wait_event, query
FROM pg_stat_activity
WHERE state != 'idle';
```

---

## 选择 reference

- 看执行计划：读取 `references/explain-plan.md`。
- 判断分布键、广播、重分布、数据倾斜：读取 `references/distribution-diagnosis.md`。
- 需要分布式架构 / 分布键 / SQL 路由 / 表类型 / 执行计划关注点 / 常见误区的底层原理：读取 `references/distributed-fundamentals.md`。
- 检查索引、统计信息、VACUUM/ANALYZE：读取 `references/statistics-indexes.md`。
- 涉及 `postgresql.conf`、`postgresql.auto.conf` 或数据库参数变更建议：读取 `references/parameter-change.md`。
- 给用户输出完整调优结论：读取 `references/tuning-report.md`。

## 标准流程

### 1. 收集上下文

先给采集命令，再要求用户贴回：

```text
慢 SQL
数据库名
连接 CN
表结构
表分布方式
数据量级
是否允许执行 EXPLAIN ANALYZE
是否允许建索引或 ANALYZE
```

### 2. 确认环境

```sql
SELECT version();
SELECT node_name,node_type,node_host,node_port
FROM pgxc_node
ORDER BY node_name;
```

### 3. 只读执行计划

```sql
EXPLAIN (VERBOSE, COSTS)
<SQL>;
```

不要先跑 `EXPLAIN ANALYZE`。

### 4. 分布式判断

重点判断：

```text
是否能按分布键路由到少量 DN
是否访问全部 DN
是否有广播
是否有数据重分布
Join 是否本地化
CN 是否承担大量汇总或排序
是否存在数据倾斜
```

### 5. 给出建议

建议按优先级输出：

```text
1. SQL 改写
2. 分布键或表类型调整
3. 索引建议
4. 统计信息建议
5. 参数或资源建议
6. 需要进一步验证的证据
```

涉及写操作时，只给计划，等待用户确认。

## 使用示例

**示例 1：分析慢 SQL 执行计划**

> 用户：这条 SQL 跑得很慢，帮我看看
> ```sql
> SELECT * FROM orders WHERE user_id = 123;
> ```
>
> Agent：（执行 EXPLAIN 分析）分析结果：
> - 主要瓶颈：未走分布键，数据分布在所有 DN 但查询只命中一个 DN（数据倾斜）
> - 建议：如果 WHERE 条件主要按 user_id 过滤，考虑将分布键改为 `DISTRIBUTE BY SHARD(user_id)`
> - 风险：改分布键需要重分布数据，建议在维护窗口执行

**示例 2：检查跨节点数据流量**

> 用户：为什么这个 JOIN 查询那么慢？
>
> Agent：（分析计划发现 `Remote Subquery Scan on all datanodes` 和 `Broadcast` 操作）
> 结论：小表 `regions` 作为复制表但实际查出 100 万行，触发了广播操作，每次查询都要将 100 万行广播到所有 DN。
> 建议：
> 1. 确认 `regions` 表是否应为小表（正常应 <1 万行）
> 2. 如果数据量确实大，改用 `DISTRIBUTE BY SHARD` 分片存储
> 3. 加索引优化 JOIN 条件

---

## 禁止自动执行

未经确认，不执行：

```text
CREATE INDEX
DROP INDEX
ANALYZE
VACUUM
ALTER TABLE
ALTER SYSTEM
SET GLOBAL
EXPLAIN ANALYZE 写 SQL
任何 INSERT/UPDATE/DELETE/MERGE/DDL
```

## 回复格式

```text
初判：<证据不足 / 疑似分布键问题 / 疑似广播或重分布 / 疑似 CN 汇总瓶颈 / 疑似统计信息或索引问题>
命令：<最小 SQL/psql 命令>
怎么看结果：<Broadcast / Redistribute / all datanodes / Sort/Aggregate on CN / 行数倾斜 / 过期统计信息>
下一步：<贴回 SQL、EXPLAIN、\d+、pgxc_class 输出；或确认是否允许 EXPLAIN ANALYZE / ANALYZE / 建索引>
```
