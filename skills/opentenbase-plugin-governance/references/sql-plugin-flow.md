# SQL-only 插件流程

SQL-only 插件不需要编译，适合教学、简单函数、简单 schema 对象和插件生命周期演示。

## 创建

```text
pluginctl> new hello_sql
```

等价于：

```text
pluginctl> new -sql hello_sql
```

生成结构通常包括：

```text
hello_sql/
├── README.md
├── manifest.yml
├── hello_sql.control
├── sql/
│   ├── hello_sql--0.1.0.sql
│   ├── verify.sql
│   └── rollback.sql
└── .pluginctlignore
```

manifest 应包含：

```yaml
type: sql
```

## 检查

```text
pluginctl> check hello_sql
```

若文件完整，通常应进入：

```text
READY
```

## 部署

```text
pluginctl> deploy hello_sql
```

作用：

- 把 `.control` 复制到 OpenTenBase extension 目录；
- 把安装 SQL 复制到 OpenTenBase extension 目录；
- 同步 PluginCtl 元数据到 `~/.plugin_ctl/packages/<plugin_id>/`；
- 不复制用户源码目录到另一台机器的工作目录。

成功后 `check` 通常进入：

```text
DEPLOYED
```

## 注册

```text
pluginctl> register hello_sql
```

作用：

- 在 primary coordinator 上检查 `pg_available_extensions`；
- 如果未注册，执行一次 `CREATE EXTENSION hello_sql;`；
- 再只读检查其他 CN 的 `pg_extension` 视图。

成功后 `check` 通常进入：

```text
REGISTERED
```

## 验证业务函数

按插件实际 SQL 执行，例如：

```sql
SELECT hello_sql.hello();
```

具体 schema 和函数名以插件安装 SQL 为准。

## 回滚

```text
pluginctl> rollback hello_sql
```

只执行 manifest 中声明的 `rollback_sql`。它不删除远端 `.control`、安装 SQL 或 `.so` 文件。

