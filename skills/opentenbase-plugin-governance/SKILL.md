---
name: opentenbase-plugin-governance
description: 使用 plugin_ctl 管理 OpenTenBase 插件生命周期。适用于插件发现、创建 SQL-only 或 C 插件、PGXS 编译、分布式文件分发、CREATE EXTENSION 注册、健康检查、回滚和插件治理教学。优先使用用户已有的 plugin_ctl 工具。
version: 1.0.0
author: CDUESTC OpenAtom Open Source Club
tools: [shell, filesystem]
user-invocable: true
---

# OpenTenBase 插件治理

若目标机器在远程 Linux，先使用 `linux-ssh-access`。若不确定 OpenTenBase 是否已启动，先使用 `opentenbase-cluster-ops` 做状态检查。

本 Skill 优先使用 `plugin_ctl`。它是 OpenTenBase 插件生命周期控制台，不是集群启停工具，不负责 `opentenbase_ctl start/stop` 或 `pgxc_ctl start all`。

## 运行用户

执行 `plugin_ctl`、`pg_config`、`psql` 或插件文件分发前，先确认 OpenTenBase 运行用户。不要在 root 下直接判断工具是否存在。

若用户只提供 root 账号，先询问 OpenTenBase 运行用户，并请求允许：

```bash
su - <opentenbase_user>
```

若用户提供的是普通 Linux 用户，也要确认它是否就是 OpenTenBase 运行用户；否则询问正确用户和切换规则。

## 用户意图分流

当用户提出“下载插件、安装插件、启用插件、启动插件、部署插件、注册插件、卸载插件、回滚插件、验证插件”等请求时，不要立刻执行。先询问用户选择治理方式：

```text
请选择插件治理方式：
1. plugin_ctl（推荐，一键治理，更省 token）
2. qclaw 手动治理插件（逐步执行，更适合学习或排查细节）
```

用户选择 `plugin_ctl` 后，按本 Skill 的标准流程执行。

用户选择手动治理后，读取：

```text
references/manual-plugin-governance.md
```

若用户已经明确说“用 plugin_ctl”或“手动来”，可直接按对应方式继续，不必重复询问。

## 核心边界

- `plugin_ctl` 管插件：发现、创建、构建、分发、注册、检查、回滚。
- `opentenbase_ctl` / `pgxc_ctl` 管集群：状态、启动、停止。
- 普通插件流程默认连接 CN，物理文件分发到声明的 CN/DN 节点。
- `deploy` 分发 `.control`、安装 SQL 和 `.so` 等物理文件。
- `register` 在 primary coordinator 上执行一次 `CREATE EXTENSION`，再只读检查其他 CN。
- `rollback` 只执行 manifest 声明的回滚 SQL，不删除 CN/DN 上的物理文件。

## 何时读取 reference

- 安装、恢复和第一次使用 `plugin_ctl`：读取 `references/setup-and-init.md`。
- SQL-only 插件创建和演示：读取 `references/sql-plugin-flow.md`。
- C 插件创建、编译、部署：读取 `references/c-plugin-flow.md`。
- 解释命令含义、安全边界、故障排查：读取 `references/commands-and-troubleshooting.md`。
- 用户选择不用 `plugin_ctl` 时：读取 `references/manual-plugin-governance.md`。

## 标准流程

### 1. 确认工具存在

```bash
command -v plugin_ctl
plugin_ctl --version
plugin_ctl --help
```

若找不到 `plugin_ctl`，先读取 `references/setup-and-init.md`，按 GitHub 源码方式安装或恢复。不要把 `plugin_ctl` 当成 OpenTenBase 官方自带命令。

### 2. 确认 OpenTenBase 已启动

不要用 `plugin_ctl` 启动集群。需要时调用 `opentenbase-cluster-ops`。

至少确认一个 CN 可用：

```bash
psql -h <cn_host> -p <cn_port> -U <db_user> -d <database> -c 'SELECT 1;'
```

### 3. 初始化 PluginCtl 集群配置

```bash
plugin_ctl init
```

`init` 读取当前已启动集群拓扑，生成默认 `cluster.toml`。它不启动、不停止、不初始化 OpenTenBase。

### 4. 进入交互式控制台

```bash
plugin_ctl
```

常用命令：

```text
help
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
```

默认英文；输入 `CH` 切换中文，输入 `EN` 切回英文。

### 5. 先检查，再修改

对已有插件优先执行：

```text
check <plugin_id_or_path>
```

根据结果判断：

```text
BUILD_REQUIRED -> 先 build
READY          -> 可以 deploy
DEPLOYED       -> 可以 register
REGISTERED     -> 可以业务验证或 report
BROKEN         -> 先修 manifest、文件或环境
REMOVED        -> 需要重新 deploy/register
```

## 使用示例

**示例 1：查看已安装插件**

> 用户：看看集群装了哪些插件
>
> Agent：（通过 plugin_ctl 执行 `list --all`）
> 已注册插件：
> - pg_stat_statements（STATUS: REGISTERED）
> - pg_cron（STATUS: REGISTERED）
>
> 其他可用插件：（列出发现目录中的所有插件）

**示例 2：创建并部署新插件**

> 用户：帮我创建一个 SQL-only 插件 my_utils
>
> Agent：（通过 plugin_ctl 执行 `new -sql my_utils`，按流程初始化、编译、检查、部署）
> ✅ 插件 `my_utils` 已创建并部署完成。下一步：`register my_utils` 在数据库中注册。

---

## 修改性命令确认

以下命令会改变环境：

```text
deploy
register
rollback
remove
```

执行前必须说明：

```text
目标插件：
目标集群：
将复制的文件：
将执行的 SQL：
影响节点：
回滚边界：
风险：
```

交互式 shell 会对修改性命令显示预览并询问确认；Agent 不要替用户跳过确认。

## 回复格式

```text
插件治理结论：可部署 / 需编译 / 已分发 / 已注册 / 已回滚 / 异常
插件：<plugin_id>
状态：<NEW/BUILD_REQUIRED/READY/DEPLOYED/REGISTERED/BROKEN/REMOVED/UNKNOWN>
下一步：<具体 plugin_ctl 命令>
风险：<无 / 缺 .so / 缺 cluster.toml / 注册失败 / 回滚有限 / 其他>
```
