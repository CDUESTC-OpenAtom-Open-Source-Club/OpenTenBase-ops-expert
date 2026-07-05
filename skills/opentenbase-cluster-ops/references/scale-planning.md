# 扩容与缩容规划

本参考用于用户询问增加或删除 CN/DN、扩容、缩容、节点迁移时。默认只读评估，不自动执行。

## 先给结论

扩缩容不是普通启停操作。它可能涉及配置变更、节点初始化、元数据注册、`pgxc_node` 对齐、连接池刷新、数据重分布和回滚预案。除非用户明确要求并确认完整计划，不执行任何变更命令。

## 已验证事实

VERIFIED：

- 当前实验环境中 `pgxc_ctl help add/remove` 存在节点增删命令入口。
- 当前实验环境中安装版 `pgxc_ctl --help` 未显示 `expand`、`shrink` 子命令。
- OpenTenBase 文档源码中 `add-node.sgml` 描述了手工增加 CN/DN 的流程。

DOCUMENTED：

- 增加 CN 通常需要初始化新 CN、同步 schema、在其他 CN 上 `CREATE NODE`，并执行 `pgxc_pool_reload()`。
- 增加 DN 除初始化和注册外，还可能需要在现有 DN 上同步节点定义，并对已有分布表执行数据重分布。

UNVERIFIED：

- 当前用户环境中的 `pgxc_ctl expand/shrink` 是否可用。
- `pgxc_ctl add/remove` 在当前环境中的完整成功路径。
- 删除节点后的数据迁移、残留清理和失败回滚流程。

## 只读评估步骤

1. 切换到 OpenTenBase 运行用户：

```bash
su - <opentenbase_user>
```

2. 确认管理工具和配置：

```bash
command -v pgxc_ctl pgxc_ctl psql 2>/dev/null || true
find /data /opt /usr/local /home -maxdepth 6 \
  \( -name config.ini -o -name opentenbase_config.ini -o -name pgxc_ctl.conf \) \
  -print 2>/dev/null
```

3. 查看本机帮助，不猜测语法：

```bash
pgxc_ctl --help
pgxc_ctl expand --help
pgxc_ctl shrink --help
printf 'help add\nhelp remove\nquit\n' | pgxc_ctl --home <pgxc_home> -c <pgxc_ctl.conf>
```

4. 记录当前拓扑：

```bash
pgxc_ctl status -c <config.ini>
pgxc_ctl --home <pgxc_home> -c <pgxc_ctl.conf> monitor all
PGCONNECT_TIMEOUT=5 psql -X -h <cn_host> -p <cn_port> -U <db_user> -d <database> \
  -F '|' -Atqc \
  'SELECT node_name,node_type,node_host,node_port FROM pgxc_node ORDER BY node_name;'
```

5. 检查新节点或待删除节点的基础条件：

```bash
hostname
ip addr
df -h
free -h
ss -lnt
```

## 扩容计划必须说明

- 新增的是 CN 还是 DN。
- 新节点主机、IP、端口、数据目录、安装目录和运行用户。
- 是否已有 OpenTenBase 二进制和相同版本。
- 是否需要修改 `pgxc_ctl` 或 `pgxc_ctl` 配置。
- 是否需要 schema 同步、`CREATE NODE`、`pgxc_pool_reload()`。
- DN 扩容是否需要对分布表做数据重分布。
- 备份、回滚方案和维护窗口。

## 缩容计划必须说明

- 删除的是 CN 还是 DN。
- 节点是否仍有业务连接、数据或主从关系。
- DN 缩容前数据如何迁移或重分布。
- 是否需要 `DROP NODE`、连接池刷新和配置清理。
- 删除数据目录、安装目录或配置前是否已有备份。
- 失败时如何恢复节点和元数据。

## 禁止自动执行

未获得用户明确确认前，不执行：

```text
pgxc_ctl expand
pgxc_ctl shrink
pgxc_ctl add
pgxc_ctl remove
CREATE NODE
ALTER NODE
DROP NODE
ALTER TABLE ... ADD NODE
init all
clean all
kill all
failover
删除数据目录或安装目录
```

## 回复模板

```text
扩缩容结论：可规划 / 信息不足 / 不建议执行
当前管理工具：pgxc_ctl / pgxc_ctl / 不确定
当前拓扑：CN=<n>, DN=<n>, GTM=<n>
目标变更：新增/删除 <CN/DN> <node_name>
已确认条件：<简述>
缺失信息：<简述>
主要风险：<数据重分布、元数据不一致、端口冲突、回滚困难等>
下一步：只读补充信息 / 用户确认维护窗口 / 准备备份和执行计划
```
