# 安装、启动和 init

本文件用于第一次使用 `plugin_ctl`。

## 安装或恢复 plugin_ctl

若机器上没有 `plugin_ctl`：

```bash
cd /opt
git clone https://github.com/iamkuangzhang/opentenbase-plugin_ctl.git opentenbase-pluginctl
cd /opt/opentenbase-pluginctl
python -m pip install -e .
```

验证：

```bash
plugin_ctl --version
plugin_ctl --help
```

预期版本：

```text
plugin_ctl 1.0.0
```

如果当前系统没有合适 Python，先报告，不要盲目升级系统 Python。优先使用现有 Python 3.11+ 或用户指定的解释器。

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
opentenbase_ctl status
psql -h <cn_host> -p <cn_port> -U <db_user> -d <database> -c 'SELECT 1;'
```

如果集群没启动，使用 `opentenbase-cluster-ops`，不要让 `plugin_ctl` 负责启停。

## 初始化 PluginCtl 配置

```bash
plugin_ctl init
```

作用：

- 读取当前运行中的 OpenTenBase 拓扑；
- 优先使用 `opentenbase_ctl status`；
- 不可用时可从 `pgxc_node` 发现 CN/DN/GTM；
- 写入默认 `cluster.toml`；
- 让后续 `deploy/register/check` 不必每次手写 `-f cluster.toml`。

`init` 不做：

- 不启动集群；
- 不停止集群；
- 不创建节点；
- 不修改 OpenTenBase 配置；
- 不部署插件。

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
