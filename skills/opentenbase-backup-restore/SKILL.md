---
name: opentenbase-backup-restore
description: 规划、检查和执行 OpenTenBase 备份与恢复流程。适用于逻辑备份、恢复演练、备份前检查、备份文件校验、恢复验证和风险说明。默认只读评估；执行 pg_dump、pg_restore、psql restore 或物理恢复前必须获得用户确认。
version: 1.0.0
author: CDUESTC OpenAtom Open Source Club
tools: [shell, filesystem]
user-invocable: true
---

# OpenTenBase 备份与恢复

若目标数据库在远程 Linux，先使用 `linux-ssh-access`。若集群状态不确定，先使用 `opentenbase-cluster-ops` 做只读状态检查。

本 Skill 负责备份恢复方案、执行计划、只读检查和恢复验证。它不负责集群安装、节点扩缩容、故障切换或业务迁移决策。

## 运行用户

执行 `pg_dump`、`pg_restore`、`psql`、`createdb` 前，先确认 OpenTenBase 运行用户。不要在 root 下直接判断工具是否存在或执行备份。

若用户只提供 root 账号，先询问 OpenTenBase 运行用户，并请求允许：

```bash
su - <opentenbase_user>
```

备份文件目录也应确认该运行用户可写。

## 核心原则

- 备份成功不等于恢复可靠，必须做恢复演练。
- OpenTenBase 是分布式数据库，不能只按单机 PostgreSQL 文件复制理解。
- 默认先做只读检查，不直接执行 `pg_dump`、`pg_restore` 或覆盖性恢复。
- 优先使用 OpenTenBase 自带版本的 `pg_dump`、`pg_restore`、`psql`。
- 逻辑备份通过 CN 执行；不要直接从 DN 当作业务备份入口。
- 生产恢复、覆盖恢复、物理恢复、PITR、删除或替换数据目录都属于高风险操作，必须等待用户明确确认。

## 选择 reference

- 备份前只读检查：读取 `references/precheck.md`。
- 逻辑备份和恢复：读取 `references/logical-backup.md`。
- 恢复演练与验证：读取 `references/restore-verify.md`。
- 物理备份、PITR 和高风险边界：读取 `references/physical-and-risk.md`。

## 标准流程

### 1. 明确目标

先确认：

```text
目标数据库：
连接 CN：
备份范围：全库 / schema / 表 / 只结构 / 只数据
备份格式：plain SQL / custom / directory
备份位置：
是否需要压缩：
是否要立即恢复演练：
恢复目标：新库 / 空库 / 原库覆盖
```

### 2. 只读检查

读取 `references/precheck.md`，确认：

- OpenTenBase 版本；
- CN/DN/GTM 拓扑；
- 使用的 `pg_dump/pg_restore/psql/createdb` 版本；
- 数据库大小；
- schema、extension、角色和权限概况；
- 目标磁盘空间。

### 3. 生成计划

执行前展示：

```text
备份命令：
预计输出文件：
读取来源：
影响范围：
恢复命令：
验证 SQL：
风险：
```

用户确认后再执行。

### 4. 执行后验证

备份后至少检查：

```text
文件存在
文件大小非零
命令退出码为 0
日志无明显 ERROR
备份元信息记录清楚
```

恢复后至少检查：

```text
SELECT 1
对象数量
schema 列表
extension 列表
关键表行数
关键业务 SQL
pgxc_node 拓扑
```

## 使用示例

**示例 1：备份数据库**

> 用户：备份 postgres 数据库，只备结构
>
> Agent：好的。将执行 `pg_dump -h <CN_IP> -p <CN_PORT> -U opentenbase -d postgres --schema-only -F c -f postgres_schema.dump`。备份文件将保存在当前目录。确认执行？
>
> 用户：确认
>
> Agent：（执行备份）✅ 备份完成！文件：`postgres_schema.dump`（大小 256KB），命令退出码 0。

**示例 2：恢复验证**

> 用户：验证下昨天的备份能不能回复
>
> Agent：我将创建临时验证库 `verify_restore`，在其中恢复备份并检查对象数、schema 列表和关键表行数。原始数据不受影响。
>
> 用户：好
>
> Agent：（恢复并验证）✅ 恢复验证通过！对象数 42，5 个 schema，关键表行数匹配。

---

## 禁止自动执行

未经用户明确确认，不执行：

```text
pg_dump
pg_restore
psql -f <dump.sql>
DROP DATABASE
CREATE DATABASE 用于覆盖恢复
DROP SCHEMA
TRUNCATE
物理数据目录复制
WAL/PITR 操作
删除备份文件
删除数据目录
停止集群
```

## 回复格式

```text
备份恢复结论：可备份 / 可恢复演练 / 证据不足 / 高风险
目标：<database/schema/table>
连接入口：<CN host:port>
工具版本：<pg_dump/pg_restore/psql version>
计划：<备份或恢复命令摘要>
验证：<已验证 / 待验证>
风险：<空间 / 锁与负载 / 覆盖数据 / 分布式一致性 / 版本兼容 / 其他>
```
