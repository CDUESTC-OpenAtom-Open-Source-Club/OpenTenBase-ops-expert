# OpenTenBase 部署故障排查

## 1. 2.5 / 2.6 直接 `initdb` 失败

**现象**：报错 `create gtm node (null)`。

**根因**：这两个版本的 `initdb` 不会自己携带 GTM 参数，必须由 `pgxc_ctl` 注入环境变量。

**处理**：统一改成 `pgxc_ctl deploy -c pgxc_ctl.conf` 或 `pgxc_ctl init all -c pgxc_ctl.conf`，不要手工直调 `initdb`。

## 2. 单容器 Docker 路线卡在节点注册

**现象**：`pgxc_ctl` 卡在 `CREATE NODE`、`EXECUTE DIRECT`，或者后续出现 GTM 时间戳错误。

**根因**：容器内虽然可以单进程启动 GTM/CN/DN，但 `pgxc_ctl` 仍依赖 SSH、节点互注册和审计日志目录，单容器伪多节点很容易把这些前置条件打断。

**处理建议**：
- Docker 场景改为 **多容器、独立 IP** 的 Compose 架构。
- 不把单容器伪多节点当成正式交付路径。
- 容器内仍需预装 `openssh-server`、`openssh-clients`、`sudo`、`libatomic`。

## 3. `invalid global timestamp` / `ResetGTMConnection`

**现象**：执行查询时出现 GTM 时间戳错误。

**根因**：大多不是 SQL 本身问题，而是 GTM、CN、DN 没有完成一致的节点注册，或者某个节点启动失败后仍被继续访问。

**处理**：
- 先检查 `pgxc_ctl monitor` 或 `opentenbase_ctl status`。
- 确认 `pgxc_node` 节点信息完整。
- 对 2.5 / 2.6 不要依赖“后台 init 一会儿再强杀”的伪完成链路，把正式路径固定为 `pgxc_ctl deploy`。

## 4. 审计日志目录缺失导致 CN / DN 启动失败

**现象**：报错 `could not open audit log file`。

**根因**：某些手工重启或异常恢复场景下，`coord/log/audit`、`dn1/log/audit` 未提前创建。

**处理**：部署脚本在生成数据目录时预建以下目录：
- `coord/log/audit`
- `dn1/log/audit`

## 5. 5.0 在 2 核机器上 GTM 启动失败

**现象**：`binding threads failed`，或 GTM 进程直接退出。

**根因**：线程绑核逻辑在低核数机器上生成非法 cpuset。

**处理**：编译 `noaffinity.so`，**必须**通过 `/etc/ld.so.preload` 全局注入；建议同时叠加 `LD_PRELOAD` 双保险。

> **为什么必须全局注入**：`opentenbase_ctl` 通过 SSH 把 GTM 拉起为独立进程，`LD_PRELOAD` **不会传播到 SSH 子进程**（v5.0-p32 commit `70166917` 实测确认）。只有写进 `/etc/ld.so.preload` 才能让所有进程（含 GTM）加载 stub。一键脚本两者都做（ld.so.preload 为主 + LD_PRELOAD 为辅），单独靠 LD_PRELOAD 无效。

## 6. 5.0 `opntenbase_ctl` 报 `Failed to extract version from package name`

**现象**：执行 `install` / `delete` / `expand` / `shrink` 时报错。

**根因**：这几条命令漏掉了 `-c config.ini`。

**处理**：`install` / `delete` / `expand` / `shrink` 必须带 `-c config.ini`；`start` / `stop` / `status` 不需要 `-c`（install 后集群状态已持久化）。

## 7. Docker Compose 的正确定位

**结论**：
- 单机多节点裸机部署：**不支持**，因为 `6669/6670` 端口冲突。
- Docker Compose：**支持**，前提是每个节点各自一个容器，并拥有独立 IP。
- 因此，Compose 是实现“单机多节点体验”的正式路径，不是单容器伪装单节点。
