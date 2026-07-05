# Skill 完善记录（基于实战测试）

> 2026-07-04 | 基于 `162.14.74.145` 单机单节点 OpenTenBase 5.0 全链路测试总结

---

## 1. opentenbase-monitoring-integration 🔴 重大完善

### 修改文件
- `SKILL.md` — 主流程重构
- `references/binary-deploy.md` — 添加镜像策略
- `references/postgres-exporter-opentenbase.md` — 重写启动部分

### 具体改进
1. **LD_LIBRARY_PATH** ✅ 所有 postgres_exporter 启动命令新增 `env LD_LIBRARY_PATH=$PGHOME/lib:$LD_LIBRARY_PATH`。未设置时 libpq 版本不匹配会导致 /metrics 卡住。
2. **中国服务器下载优化** ✅ 新增 ghproxy 代理策略、清华镜像、离线 SCP 三种下载来源，附带 tar 完整性校验命令。
3. **引导式流程** ✅ 主 Skill 新增运行用户切换、PGHOME 导出、DATA_SOURCE_NAME 清理步骤。
4. **最小必须组件** ✅ 明确 postgres_exporter 可独立部署，Prometheus+Grafana 为可选后续补充。
5. **快速验证** ✅ 启动后立即 sleep 2 && curl 验证，不再等用户手动检查。

---

## 2. opentenbase-deploy 🟡 增强

### 修改文件
- `SKILL.md` — 验证标准 + 部署流程描述

### 具体改进
1. **验证命令重构** ✅ 从单行 `opentenbase_ctl status` 改为进程检查 + 端口检查 + psql 全链路。说明 `opentenbase_ctl` 仅 RPM 包安装可用，一键脚本部署用进程/端口/psql 验证。
2. **可见性提升** ✅ 新增 6 步部署流程概览（环境预检→解决依赖→下载二进制→集群初始化→配置优化→最终验证）。
3. **端口文档化** ✅ CN=11003, DN=11006, GTM=11000（实际测试值）。
4. **2核CPU处理** ✅ 已由脚本自动处理 noaffinity.so，无需额外配置。

---

## 3. opentenbase-backup-restore 🟡 增强

### 修改文件
- `references/restore-verify.md` — 新增行数比较 + 已知告警

### 具体改进
1. **表行数批量比对** ✅ 新增 `UNION ALL SELECT count(*) FROM ...` 一条 SQL 比对所有表。
2. **已知可忽略告警** ✅ 记录 `opentenbase_ora already exists` 和 `opentenbase_plpgsql already exists` 为正常跳过行为。
3. **自定义 extension 警告** ✅ 提示恢复自定义 extension（pgcrypto 等）需先 CREATE EXTENSION 否则会报错。

---

## 4. opentenbase-log-error-analysis 🟡 增强

### 修改文件
- `references/error-patterns.md` — 新增已知可忽略 WARNING 清单
- `references/log-locations.md` — 新增 RPM 包安装日志路径

### 具体改进
1. **已知可忽略 WARNING** ✅ 记录 `create extension pg_clean please`（CN 后台清理线程定期检查，每若干分钟出现一次，无需处理）。
2. **日志路径双模式** ✅ 源码编译 (`/data/opentenbase/`) 和 RPM 包安装 (`/var/lib/opentenbase/*/`) 两种路径同时覆盖。
3. **自动定位命令** ✅ 新增从进程获取数据目录的 ps 命令。

---

## 5. opentenbase-cluster-ops 🟡 增强

### 修改文件
- `SKILL.md` — 管理方式自动检测

### 具体改进
1. **双工具检测** ✅ 自动检测 `pgxc_ctl` / `opentenbase_ctl` / manual（进程+psql），适配三种部署方式。
2. **分类表** ✅ 源码编译 → pgxc_ctl，一键脚本 → 进程检查，RPM 包 → opentenbase_ctl。

---

## 6. opentenbase-sql-tuning 🟢 增强

### 修改文件
- `SKILL.md` — 新增调优经验板块

### 具体改进
1. **复制表 JOIN 经验** ✅ 实测 orders(SHARD)+products(REPLICATION) Hash Join 在 DN 本地完成，完全不产生广播开销。
2. **复制表行数边界** ✅ 建议不超过 1 万行，超过后应改 SHARD。
3. **SHARD 表倾斜检查** ✅ 新增 `xc_node_id` 分 DN 行数查询示例。

---

## 7. opentenbase-routine-maintenance 🟢 增强

### 修改文件
- `references/daily-checklist.md` — 日志检查路径双模式 + 可忽略 WARNING

### 具体改进
1. **日志路径双模式** ✅ 兼容 `/data/opentenbase` 和 `/var/lib/opentenbase`。
2. **已知可忽略 WARNING** ✅ 同 log-error-analysis，`create extension pg_clean please`。

---

## 8. opentenbase-plugin-governance — 无需改动

测试中 `CREATE EXTENSION pgcrypto` 运行正常，Skill 已有完整流程。无需更新。

---

## 总结

| Skill | 修改程度 | 核心改进 |
|-------|---------|---------|
| monitoring-integration | 🔴 大改 | LD_LIBRARY_PATH、镜像下载、引导流程 |
| deploy | 🟡 中改 | 验证命令重构、部署流程可见性 |
| backup-restore | 🟡 中改 | 行数比对、可忽略告警 |
| log-error-analysis | 🟡 中改 | 已知 WARNING 清单、双路径 |
| cluster-ops | 🟡 中改 | 双管理工具自动检测 |
| sql-tuning | 🟢 小改 | 复制表经验、倾斜检查 |
| routine-maintenance | 🟢 小改 | 双路径、可忽略 WARNING |
| plugin-governance | - | 无需改动 |
