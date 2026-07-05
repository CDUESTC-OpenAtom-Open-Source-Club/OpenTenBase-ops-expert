# 安装、恢复和 init

本文件用于第一次使用 `plugin_ctl`。

## 先确认是否已安装

先进入 OpenTenBase 运行用户环境，不要只在 root 下判断：

```bash
su - <opentenbase_user>
command -v plugin_ctl
plugin_ctl --version
```

预期版本：

```text
plugin_ctl 1.0.0
```

`plugin_ctl` 不是 OpenTenBase 官方自带命令；如果找不到，需要从 GitHub 下载。

## 从 GitHub 安装或恢复 plugin_ctl

若机器上没有 `plugin_ctl`：

```bash
command -v git
OTB_USER=<opentenbase_user>
OTB_GROUP=$(id -gn "$OTB_USER")
cd /opt
git clone https://github.com/iamkuangzhang/opentenbase-plugin_ctl.git opentenbase-pluginctl
chown -R "$OTB_USER:$OTB_GROUP" /opt/opentenbase-pluginctl
```

确认 Python。优先使用 3.11 或更高版本：

```bash
/opt/python3.11/bin/python3.11 --version
python3 --version
```

如果已有 `/opt/python3.11/bin/python3.11`，可创建全局入口：

```bash
cat >/usr/local/bin/plugin_ctl <<'EOF'
#!/usr/bin/env bash
export PYTHONPATH=/opt/opentenbase-pluginctl/src${PYTHONPATH:+:$PYTHONPATH}
exec /opt/python3.11/bin/python3.11 -m plugin_ctl "$@"
EOF

chmod +x /usr/local/bin/plugin_ctl
```

如果 Python 路径不同，把 `/opt/python3.11/bin/python3.11` 换成实际解释器。不要盲目升级系统 Python。

切回 OpenTenBase 运行用户后验证：

```bash
su - <opentenbase_user>
plugin_ctl --version
plugin_ctl --help
plugin_ctl list
```

验证通过应至少看到：

```text
plugin_ctl 1.0.0
```

## 旧安装损坏时的恢复方式

如果已有旧源码目录或旧入口但无法运行，先备份再重装，不要直接覆盖用户文件：

```bash
TS=$(date +%Y%m%d%H%M%S)
mv /usr/local/bin/plugin_ctl /usr/local/bin/plugin_ctl.bak.$TS 2>/dev/null || true
mv /opt/opentenbase-pluginctl /opt/opentenbase-pluginctl.bak.$TS 2>/dev/null || true
```

然后按上一节重新 clone 和创建入口。

已在真实环境验证过的恢复路径：

```text
移走 /usr/local/bin/plugin_ctl 和 /opt/opentenbase-pluginctl
从 https://github.com/iamkuangzhang/opentenbase-plugin_ctl.git 重新 clone
创建 /usr/local/bin/plugin_ctl wrapper
su - opentenbase 后执行 plugin_ctl --version / plugin_ctl list / plugin_ctl check pluginctl_smoke_plugin
```

## 运行用户

通常切换到运行 OpenTenBase 的系统用户：

```bash
su - opentenbase
```

实际用户名必须以用户环境为准；如果 SSH 登录的是 root，先询问运行用户，不要直接在 root 下运行 `plugin_ctl`。

不要用 root 创建普通插件工作目录，除非用户明确要求。

## 启动前提

`plugin_ctl init` 要求 OpenTenBase 已经启动，并且至少一个 CN 可以连接。

推荐先检查：

```bash
pgxc_ctl status
psql -h <cn_host> -p <cn_port> -U <db_user> -d <database> -c 'SELECT 1;'
```

如果集群没启动，使用 `opentenbase-cluster-ops`，不要让 `plugin_ctl` 负责启停。

## 初始化 PluginCtl 配置

```bash
plugin_ctl init
```

作用：

- 读取当前运行中的 OpenTenBase 拓扑；
- 优先使用 `pgxc_ctl status`；
- 不可用时可从 `pgxc_node` 发现 CN/DN/GTM；
- 写入默认 `cluster.toml`；
- 让后续 `deploy/register/check` 不必每次手写 `-f cluster.toml`。

`init` 不做：

- 不启动集群；
- 不停止集群；
- 不创建节点；
- 不修改 OpenTenBase 配置；
- 不部署插件。

## PluginCtl 本地配置

`plugin_ctl` 自己的状态通常在运行用户家目录：

```text
~/.plugin_ctl/cluster.toml
~/.plugin_ctl/catalog.json
~/.plugin_ctl/history
~/.plugin_ctl/packages/
```

含义：

```text
cluster.toml  当前 OpenTenBase 拓扑和连接信息，由 plugin_ctl init 生成
catalog.json  用户通过 add/new/deploy 接入的插件清单
history       交互式控制台历史
packages/     已同步的插件包元数据
```

不要手工编辑这些文件作为首选方案。优先使用：

```text
plugin_ctl init
plugin_ctl add <plugin_dir>
plugin_ctl remove <plugin_id>
plugin_ctl deploy <plugin_id_or_path>
```

如果 CN/DN/GTM、IP、端口或主机名变化，先重新执行：

```bash
plugin_ctl init
```

再用：

```bash
plugin_ctl check <plugin_id>
plugin_ctl list
```

验证结果。

## 交互式控制台

```bash
plugin_ctl
```

进入后：

```text
pluginctl> help
pluginctl> init
pluginctl> list
pluginctl> quit
```

历史命令保存在：

```text
~/.plugin_ctl/history
```
