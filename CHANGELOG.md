# Changelog

## [1.9.0] - 2026-07-03

### Fixed（任务 1/2/3 评测反馈 — 教学解释、拓扑正确性、紧急响应简洁性）
- 部署首轮增加新手解释：GTM、CN、DN、`pgxc_ctl`、防火墙、SELinux、内核参数分别说明作用和风险。
- 明确高可用拓扑规则：三台机器只算最小可用，不宣称高可用；GTM 主备、DN 主备不能同机；同机多节点必须错开数据目录和所有端口。
- `opentenbase-deploy` 升级到 4.1.0：补充 5 台完整高可用建议拓扑，避免 DN 主备同机和端口冲突。
- `opentenbase-sql-tuning` 升级到 1.4.0：补充 `Remote Subquery Scan on all datanodes` 判断说明，并限制首轮回复长度。
- `opentenbase-log-error-analysis` 升级到 1.7.0：紧急故障首轮限制为 1 句初判、1 个命令块、6 条以内判断点。

## [1.8.0] - 2026-07-03

### Fixed（任务 1 评测反馈 — 部署入口和管理命令改为可核验路径）
- 部署默认路径改为官方源码编译 + `pgxc_ctl`，默认只使用可核验的源码仓库和目标环境本地工具。
- `opentenbase-deploy` 升级到 4.0.0：重写为源码编译、SSH 互信、`pgxc_ctl.conf`、`pgxc_ctl init/start/monitor`、SQL 验证的端到端流程。
- 集群运维、巡检、插件治理和入口工具说明统一改为默认 `pgxc_ctl`；其它管理工具必须先在目标环境验证存在。
- 全包运行文档去掉装饰性符号，紧急故障响应保持纯文本、短命令、强可操作。

## [1.7.0] - 2026-07-03

### Fixed（任务 1 评测反馈 — 部署停留在规划、缺少端到端命令）
- 强化部署首轮响应：用户要求部署时必须直接给拓扑、系统准备、SSH 方案、安装、配置、初始化、启动和验证命令，不以追问替代交付。
- `opentenbase-deploy` 升级到 3.12.0：新增默认三节点部署模板，覆盖 GTM=6666、CN=11003、DN=15432、数据目录、防火墙、SELinux、内核参数和部署后验证。
- 补充资源不足处理规则：机器内存或磁盘不足时先给可执行替代拓扑和风险标注，不能只质疑需求。
- 修正部署使用示例：移除“先确认再部署”的示例话术，改为命令优先。

## [1.6.0] - 2026-07-03

### Fixed（任务 2/3 评测反馈 — 文件副作用 + OpenTenBase 专有诊断不足）
- 强化运行纪律：默认只在对话中给命令、判断点和验证方法；用户未明确要求写文件时不落盘。
- 收紧工具声明：入口和所有子 Skill 默认移除文件系统工具声明，监控仅保留 `shell` + `http`。
- 增强慢 SQL 首轮响应：信息不足时也给 `SELECT version()`、`pgxc_node`、`EXPLAIN`、分布键、数据倾斜和等待会话采集命令。
- 增强日志错误分析：补齐 DN 崩溃/启动失败场景，覆盖 WAL 恢复失败、数据/索引文件缺失、2PC 残留、磁盘满、权限错误和端口冲突。
- 增强备份恢复：补齐 CN 端口 `11003` 的逻辑备份、恢复到验证库、备份文件校验和故障后恢复前检查命令。
- 同步 README、TOOLS 和元数据版本，清理包内 `.DS_Store`。

## [1.5.0] - 2026-07-03

### Fixed（第五轮评测反馈 — 自述过多 + 部署安全检查缺失）
- **消除技能自述行为**：Agent 在回复中花费大量篇幅介绍自己的技能体系、路由过程、能力列表，而非直接回答用户问题
  - AGENTS.md：新增铁律 4「不自述技能、不介绍路由」
  - SOUL.md：表达风格新增「回复开头直接切入正题」；说话禁忌新增「不自述技能」
  - SKILL.md：删除冗长简介段、「何时触发本专家」、3 个使用示例、「与其它专家的边界」；运行时准则新增「不自述技能体系」
  - opentenbase-deploy：新增「铁律零：直接回答，不自述」
  - opentenbase-sql-tuning：最高优先级规则新增「直接切入诊断」
  - opentenbase-log-error-analysis：最高优先级规则新增「直接进入诊断流程」
- **部署前置安全检查补全**（评测任务 1 安全性仅 0.55）
  - 环境检查新增 root 运行风险警告（醒目 blockquote）
  - 新增 SELinux 状态检查 + 关闭命令
  - 新增内核参数检查（shmmax/shmall/sem）+ 推荐值
  - 新增防火墙端口开放命令（6666/11003/15432/6669/6670）

## [1.4.0] - 2026-07-03

### Fixed（负面启动根因修复 — 第四轮评测反馈）
- **消除负面启动（Negative Priming）反模式**：4 轮评测中 Agent 持续创建无关文件的根因是——禁止规则中列出了具体文件名（`_meta.json`、`BOOT.md`、`CHANGELOG.md`、`memory/`），反而引导 LLM 去创建这些文件
  - AGENTS.md 铁律 1：从"不准创建 `_meta.json`、`BOOT.md`..."改为正面框架"只回复对话，不碰文件系统"
  - SOUL.md：核心准则第 5 条和说话禁忌最后一条全部改为正面表述，移除所有具体文件名
  - SKILL.md：删除"顶层文件"段落（列出了 6 个文件名），替换为"运行时行为准则"纯正面框架
  - opentenbase-log-error-analysis/SKILL.md：移除"不写 memory 日志"表述
  - USER.md：移除"不写入文件"表述
- 修复 `_meta.json` 中仍引用已删除的 `BOOT.md` 的问题

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
