# 命令含义与排错

## 常用命令

```text
plugin_ctl                 进入交互式控制台
plugin_ctl --version       查看版本
plugin_ctl init            发现当前集群拓扑并生成默认 cluster.toml
plugin_ctl list            列出用户插件
plugin_ctl list --all      列出用户插件和内置参考插件
plugin_ctl check <plugin>  一站式检查插件包、部署、注册和验证状态
```

交互式命令：

```text
help
help advanced
init
new <plugin_id>
new -sql <plugin_id>
new -c <plugin_id>
build <plugin_id>
list
list --all
deploy <plugin_id_or_path>
register <plugin_id>
check <plugin_id_or_path>
rollback <plugin_id>
quit
CH
EN
```

## deploy 与 register 的区别

`deploy`：

```text
分发插件物理文件
```

包括 `.control`、安装 SQL、C 插件 `.so` 等。它让 OpenTenBase 各节点具备加载插件的文件条件。

`register`：

```text
执行 CREATE EXTENSION
```

只在 primary coordinator 上执行一次，然后检查其他 CN 的扩展视图是否一致。

## list 为什么能看到插件

`list` 来自三类来源：

- 用户 catalog 中登记的插件；
- PluginCtl 已同步到 `~/.plugin_ctl/packages/` 的包元数据；
- `list --all` 时显示的内置参考插件。

把插件目录放到任意位置后，通常可以直接：

```text
deploy /path/to/plugin_dir
```

它会自动接入用户 catalog。也可以显式：

```text
add /path/to/plugin_dir
```

## 常见状态

```text
NEW             插件目录可识别，但还没进入 catalog 或未开始生命周期
BUILD_REQUIRED  C 插件缺少 .so，需要 build
READY           本地插件包完整，可以 deploy
DEPLOYED        物理文件已分发，可以 register
REGISTERED      CREATE EXTENSION 成功并验证通过
BROKEN          包结构、环境、部署或注册存在失败项
REMOVED         已回滚并通过移除验证
UNKNOWN         状态证据不足
```

## 常见问题

### plugin_ctl 找不到

```bash
command -v plugin_ctl
type -a plugin_ctl 2>/dev/null || true
plugin_ctl --version
```

`plugin_ctl` 不是 OpenTenBase 官方自带命令。找不到时先读 `setup-and-init.md`，从 GitHub 安装：

```text
https://github.com/iamkuangzhang/opentenbase-plugin_ctl
```

如果只有源码目录、没有全局入口，可临时使用：

```bash
PYTHONPATH=/opt/opentenbase-pluginctl/src \
  /opt/python3.11/bin/python3.11 -m plugin_ctl --version
```

上面的 Python 路径和源码目录必须按实际环境替换。找不到时读取 `setup-and-init.md`。

### init 失败

检查：

```bash
opentenbase_ctl status
psql -h <cn_host> -p <cn_port> -U <db_user> -d <database> -c 'SELECT * FROM pgxc_node;'
```

`init` 失败通常表示：

- OpenTenBase 没启动；
- CN 连接失败；
- `opentenbase_ctl` 配置不一致；
- 当前用户没有读配置或连接数据库的条件。

### deploy 后另一台机器看不到源码目录

这是正常的。`deploy` 分发的是数据库需要的 extension 文件和 PluginCtl 元数据，不会把用户源码目录复制到另一台机器的家目录。

另一台机器的 `plugin_ctl list` 能看到已部署插件，依赖 `deploy` 同步到远端的 `~/.plugin_ctl/packages/<plugin_id>/` 元数据。

### register 失败

优先检查：

```sql
SELECT name, default_version
FROM pg_available_extensions
WHERE name = '<plugin_id>';

SELECT extname, extversion
FROM pg_extension
WHERE extname = '<plugin_id>';
```

常见原因：

- `.control` 没分发到 extension 目录；
- 安装 SQL 文件名和 control 的 `default_version` 不匹配；
- C 插件 `.so` 不存在或符号名不匹配；
- SQL 中使用当前版本不支持的语法；
- 已经注册过。

### rollback 后物理文件还在

这是当前设计。`rollback` 清理数据库对象，不负责删除远端 extension 物理文件。
