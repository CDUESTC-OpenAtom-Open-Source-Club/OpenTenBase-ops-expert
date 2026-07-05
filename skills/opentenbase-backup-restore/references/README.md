# 参考文档目录

本目录存放 opentenbase-backup-restore 技能专属的参考文档，按主题拆分，方便按需查阅。

Skill 通过 `{baseDir}/references/` 路径引用这些文件。

## 文档索引

| # | 文件 | 主题 | 解决什么问题 |
|---|------|------|------------|
| 1 | `precheck.md` | 备份前只读检查 | 确认版本、拓扑、大小、权限后再备份 |
| 2 | `logical-backup.md` | 逻辑备份与恢复 | pg_dump / pg_restore 在 OpenTenBase 上的正确用法 |
| 3 | `restore-verify.md` | 恢复演练与验证 | 恢复后如何验证数据完整性与一致性 |
| 4 | `physical-and-risk.md` | 物理备份与风险边界 | 物理备份、PITR、高风险操作说明 |
