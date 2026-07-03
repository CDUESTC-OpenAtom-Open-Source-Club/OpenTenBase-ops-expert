# Changelog

## [1.1.0] - 2026-07-03

### Fixed（基于 QClaw 可用性评测反馈修复）
- **修复 Agent 创建无关工程文件的核心问题**（三个评测任务均因此严重失分）：
  - 重写 AGENTS.md：添加「任务聚焦」最高优先级规则，明确禁止创建与用户任务无关的文件
  - 重写 BOOT.md：从"初始化清单"改为"最小自检清单"，移除所有创建文件的行为
  - **删除 BOOTSTRAP.md**：该文件直接指示 Agent 创建 memory 目录和写入日志，是脚手架问题的直接根因
- **增强 opentenbase-log-error-analysis (v1.1.0)**：添加 OpenTenBase CN 崩溃快速诊断决策树（GTM 连接失败、forward manager 端口冲突、2 核 GTM 崩溃、libpqxx 缺失、OSS_INSTALL_DIR 不匹配、残留 PID），覆盖 6 种按概率排序的特有崩溃模式
- **增强 opentenbase-deploy (v3.7.0)**：添加三条核心输出铁律（首次回复必须含可执行命令、已知信息不重复追问、复杂场景必须给完整拓扑含端口+数据目录+GTM Standby）
- **增强 opentenbase-sql-tuning (v1.1.0)**：添加分布式慢查询根因优先级（分布键选择、广播/重分布、数据倾斜、CN 汇总、跨节点事务），添加信息不完整时的结构化诊断引导

### Changed
- 更新 _meta.json 版本号至 1.1.0
- 更新 README.md 移除 BOOTSTRAP.md 引用

## [1.0.0] - 2026-07-02

### Added
- 10 个业务 Skill：部署、集群运维、备份恢复、用户权限、SQL 调优、插件治理、监控接入、日志分析、日常巡检、SSH 连接
- 完整的前置文件体系：AGENTS.md、SOUL.md、IDENTITY.md、USER.md、TOOLS.md、MEMORY.md
- 启动流程支持：BOOT.md、BOOTSTRAP.md、HEARTBEAT.md
- 长期记忆与每日记录机制
- LICENSE (MIT-0)
- CHANGELOG.md
- _meta.json 元数据
- 各 SKILL.md 添加 `## 使用示例` 章节
- 各 SKILL.md frontmatter 补充 author/tools 字段

### Changed
- 清理 example-skill 模板占位
- 更新 .gitignore 忽略规则
