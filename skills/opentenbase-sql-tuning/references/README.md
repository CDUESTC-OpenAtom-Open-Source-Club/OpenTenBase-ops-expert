# 参考文档目录

本目录存放 opentenbase-sql-tuning 技能专属的参考文档，按主题拆分，方便按需查阅。

Skill 通过 `{baseDir}/references/` 路径引用这些文件。

## 文档索引

| # | 文件 | 主题 | 解决什么问题 |
|---|------|------|------------|
| 1 | `explain-plan.md` | 执行计划解读 | 分析 EXPLAIN 输出，识别分布式执行瓶颈 |
| 2 | `distribution-diagnosis.md` | 分布键诊断 | 判断广播、重分布、数据倾斜，给出分布键建议 |
| 3 | `statistics-indexes.md` | 统计信息与索引 | ANALYZE / 索引在 OpenTenBase 中的正确实践 |
| 4 | `parameter-change.md` | 参数变更 | 影响性能的关键参数及变更注意事项 |
| 5 | `tuning-report.md` | 调优报告模板 | 输出格式化的 SQL 调优结论 |
