# C 插件流程

C 插件需要先用 PGXS 编译生成 `.so`，再分发和注册。

## 创建 C 插件

```text
pluginctl> new -c hello_c
```

生成结构通常包括：

```text
hello_c/
├── README.md
├── manifest.yml
├── Makefile
├── hello_c.control
├── src/
│   └── hello_c.c
├── sql/
│   ├── hello_c--0.1.0.sql
│   ├── verify.sql
│   └── rollback.sql
└── .pluginctlignore
```

manifest 应包含：

```yaml
type: c
build:
  system: pgxs
  workdir: .
  pg_config: auto
library_files:
  - hello_c.so
```

## 检查编译状态

```text
pluginctl> check hello_c
```

新生成的 C 插件还没有 `.so`，应显示：

```text
BUILD_REQUIRED
```

这不是坏状态，只表示需要先编译。

## 编译

```text
pluginctl> build hello_c
```

`build` 会：

- 寻找 OpenTenBase 对应的 `pg_config`；
- 检查 `make`；
- 执行 `make clean`；
- 执行 `make PG_CONFIG=<实际路径>`；
- 检查 `.so` 是否生成。

`build` 不会执行：

```text
make install
```

编译成功后：

```text
pluginctl> check hello_c
```

应进入：

```text
READY
```

## 部署

```text
pluginctl> deploy hello_c
```

部署计划应包含：

```text
.control -> extension_dir
安装 SQL -> extension_dir
.so -> lib_dir
```

如果 `.so` 缺失，`deploy` 必须阻止，并提示先执行：

```text
build hello_c
```

## 注册和验证

```text
pluginctl> register hello_c
pluginctl> check hello_c
```

注册阶段执行 `CREATE EXTENSION`。如果安装 SQL 中的 C 函数符号、`.so` 名称、control 文件不一致，注册可能失败。

默认模板使用标准：

```sql
LANGUAGE C STRICT
```

不要主动添加 `SHIPPABLE`，除非当前 OpenTenBase 构建明确支持该语法。

## 回滚边界

```text
pluginctl> rollback hello_c
```

回滚只执行 SQL 清理数据库对象，不删除已分发的 `.so`、`.control` 或安装 SQL 文件。

