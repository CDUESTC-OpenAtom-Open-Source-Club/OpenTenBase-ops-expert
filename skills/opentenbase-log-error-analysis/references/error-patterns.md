# 常见错误模式

以下是排查方向，不是最终结论。必须结合状态、进程、端口和相关节点日志验证。

## 管理工具

`opentenbase_ctl: error while loading shared libraries: libpqxx.so`

- 方向：运行用户环境缺少 `LD_LIBRARY_PATH`，或二进制依赖库不在可搜索路径。
- 检查：

```bash
ldd <opentenbase_ctl> | grep 'not found' || true
echo "$LD_LIBRARY_PATH"
```

`sh: sshpass: command not found`

- 方向：`opentenbase_ctl` 远程 SSH 能力依赖缺失，或当前工具链包装不完整。
- 检查：

```bash
command -v ssh sshpass || true
```

`pgxc_ctl` 显示 `Not running: ...`

- 方向：节点未运行，或配置中的主机名、目录、端口与实际不一致。
- 继续检查进程、端口和对应节点数据目录日志。

## 连接与端口

`Connection refused`

- 方向：目标端口未监听、节点已停止、主机/端口填错、防火墙或转发端口不可达。
- 检查：

```bash
ss -lntp 2>/dev/null || ss -lnt 2>/dev/null
PGCONNECT_TIMEOUT=5 psql -X -h <host> -p <port> -U <user> -d <db> -Atqc 'SELECT 1;'
```

`could not connect to node`

- 方向：节点间通信失败。优先核对 `pgxc_node`、主机名解析、forward/pooler 端口和对端进程。

## 节点间通信

`could not recv status from node conn_node=...`

- 方向：对端节点停止、forward 端口不可达、节点元数据不一致，或网络连接被关闭。
- 检查两端日志，不只看报错所在节点。

`invalid client addr <ip> expect addr <hostname>`

- 方向：主机名解析与实际 IP 不一致，常见于克隆虚拟机、改 IP 后未同步 `/etc/hosts` 或配置文件。
- 检查：

```bash
hostname
getent hosts <hostname>
grep -n '<hostname>' /etc/hosts 2>/dev/null
```

## 启停过程

`FATAL: terminating connection due to administrator command`

- 方向：停止或重启时可能是预期现象。若非维护窗口出现，才继续判断为异常。

`No such file or directory`

- 方向：不能单独判断。可能是日志中的网络读写错误文本，也可能是真的文件缺失。
- 必须结合完整上下文和前后日志。

## GTM

`gtm recovery finished, but due to lack of xlog`

- 方向：GTM 恢复过程中的 WAL/xlog 校验不完整提示。
- 若集群最终能启动并通过 CN 查询，通常先标记为 warning；若伴随 GTM 启动失败，再深入排查 GTM 数据目录和启动日志。

## 报告原则

- 先定位“哪个节点、哪个端口、哪个工具、什么时间”。
- 把 `ERROR/FATAL/WARNING` 分开解释。
- 区分“停止过程产生的正常噪声”和“导致失败的根因”。
- 结论不够时输出“需要补充证据”，不要强行给修复命令。
