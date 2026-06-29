# 手动治理 OpenTenBase 插件

本文件用于用户明确选择“qclaw 手动治理插件”时。默认仍推荐 `plugin_ctl`，因为它能生成计划、同步元数据、检查状态并减少重复命令。

手动治理适合：

- 学习 PostgreSQL/OpenTenBase extension 机制；
- 排查 `plugin_ctl` 失败原因；
- 处理临时实验插件；
- 用户明确不希望使用 `plugin_ctl`。

## 运行用户

先确认 OpenTenBase 运行用户并切换：

```bash
su - <opentenbase_user>
```

不要在 root 下直接判断 `pg_config`、`psql` 或 extension 目录。

## 安全边界

手动治理更容易漏步骤。执行前必须说明：

```text
目标插件：
目标 CN：
目标 DN：
extension_dir：
lib_dir：
将复制的文件：
将执行的 SQL：
回滚方式：
风险：
```

不要对 `otb_timeseries` 或真实业务插件做破坏性回滚，除非用户明确确认。

## 1. 确认集群和入口 CN

```bash
opentenbase_ctl status
```

或从用户提供的信息确认 CN 连接：

```bash
psql -h <cn_host> -p <cn_port> -U <db_user> -d <database> -c 'SELECT 1;'
```

查看拓扑：

```sql
SELECT node_name,node_type,node_host,node_port
FROM pgxc_node
ORDER BY node_name;
```

普通插件注册连接 CN，不把 DN 当业务入口。

## 2. 确认插件文件

SQL-only 插件通常需要：

```text
<extension>.control
<extension>--<version>.sql
```

C 插件还需要：

```text
<extension>.so
```

检查 control 文件：

```bash
cat <extension>.control
```

确认：

```text
default_version
module_pathname
relocatable
```

## 3. 确认 OpenTenBase 目录

从目标环境查询：

```bash
pg_config --sharedir
pg_config --pkglibdir
```

常见位置：

```text
extension_dir = $(pg_config --sharedir)/extension
lib_dir       = $(pg_config --pkglibdir)
```

必须使用 OpenTenBase 自带 `pg_config`，不要混用系统 PostgreSQL。

## 4. 分发文件

在每个需要的 CN/DN 节点上放置文件：

```bash
cp <extension>.control <extension_dir>/
cp <extension>--<version>.sql <extension_dir>/
cp <extension>.so <lib_dir>/        # C 插件才需要
```

跨机器时用 `scp` 或用户确认的分发方式。

分发后检查：

```bash
ls -l <extension_dir>/<extension>.control
ls -l <extension_dir>/<extension>--<version>.sql
ls -l <lib_dir>/<extension>.so      # C 插件才需要
```

## 5. 注册 extension

只在 primary coordinator 或用户确认的入口 CN 上执行一次：

```sql
CREATE EXTENSION <extension>;
```

不要循环在每个 CN 上执行 `CREATE EXTENSION`。执行后只读验证其他 CN：

```sql
SELECT extname, extversion
FROM pg_extension
WHERE extname = '<extension>';
```

如果 `CREATE EXTENSION` 报 already exists，先查询 `pg_extension`，不要重复执行。

## 6. 功能验证

执行插件自己的 verify SQL 或最小业务 SQL：

```sql
SELECT <schema>.<function>();
```

具体 schema、函数名、表名以插件安装 SQL 为准。

## 7. 手动回滚

优先使用插件提供的 rollback SQL。

示例：

```sql
DROP EXTENSION <extension>;
```

或执行插件自己的对象清理 SQL。

回滚前必须说明：

- 会删除哪些对象；
- 是否影响业务数据；
- 是否只删除数据库对象；
- 是否保留 `.control`、`.sql`、`.so` 物理文件。

默认不删除物理文件。

## 8. 常见错误

`extension is not available`：

- `.control` 没在 extension 目录；
- 安装 SQL 文件名和 `default_version` 不匹配；
- 连接的不是预期 CN。

`could not access file "$libdir/xxx"`：

- C 插件 `.so` 没在 `pkglibdir`；
- `.so` 文件名和 SQL `MODULE_PATHNAME` 不一致；
- 编译使用了错误 PostgreSQL/OpenTenBase 头文件。

`function ... does not exist`：

- SQL 函数名、C 符号名、schema 或 search_path 不一致。

多 CN 状态不一致：

- 不要重复注册；
- 先查询各 CN 的 `pg_extension`；
- 检查是否连接到了不同集群或旧配置。
