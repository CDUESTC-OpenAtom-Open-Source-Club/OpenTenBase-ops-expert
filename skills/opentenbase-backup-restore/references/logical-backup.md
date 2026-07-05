# 逻辑备份与恢复

逻辑备份适合开发、测试、迁移演练和对象级恢复。大规模生产数据应先评估性能、时间窗口和恢复目标。

## 推荐格式

自定义格式便于 `pg_restore` 选择性恢复：

```bash
pg_dump -h <cn_host> -p <cn_port> -U <db_user> \
  -d <database> -F c -f <backup_file>.dump
```

plain SQL 便于阅读：

```bash
pg_dump -h <cn_host> -p <cn_port> -U <db_user> \
  -d <database> -F p -f <backup_file>.sql
```

执行前必须确认输出目录、文件名和磁盘空间。

## 常见范围

全库：

```bash
pg_dump -h <cn_host> -p <cn_port> -U <db_user> \
  -d <database> -F c -f <database>.dump
```

指定 schema：

```bash
pg_dump -h <cn_host> -p <cn_port> -U <db_user> \
  -d <database> -n <schema> -F c -f <schema>.dump
```

只结构：

```bash
pg_dump -h <cn_host> -p <cn_port> -U <db_user> \
  -d <database> --schema-only -F p -f <database>_schema.sql
```

只数据：

```bash
pg_dump -h <cn_host> -p <cn_port> -U <db_user> \
  -d <database> --data-only -F c -f <database>_data.dump
```

## 备份后检查

```bash
ls -lh <backup_file>
test -s <backup_file>
```

custom 格式可列目录：

```bash
pg_restore -l <backup_file> | head
```

plain SQL 可只查看头部：

```bash
head -40 <backup_file>.sql
```

## 恢复到新库

优先恢复到新库或测试库，不要直接覆盖原库：

```bash
createdb -h <cn_host> -p <cn_port> -U <db_user> <restore_database>
pg_restore -h <cn_host> -p <cn_port> -U <db_user> \
  -d <restore_database> <backup_file>.dump
```

plain SQL：

```bash
psql -h <cn_host> -p <cn_port> -U <db_user> \
  -d <restore_database> -f <backup_file>.sql
```

执行恢复前必须确认目标库是否为空、是否允许写入、是否会覆盖已有对象。

## 注意事项

- 逻辑备份通过 CN 执行。
- 备份可能消耗 IO、CPU、网络和 CN 资源。
- 恢复可能失败于角色、权限、extension、表空间、分布语法或版本差异。
- 备份文件包含敏感数据时，必须注意权限和脱敏。

