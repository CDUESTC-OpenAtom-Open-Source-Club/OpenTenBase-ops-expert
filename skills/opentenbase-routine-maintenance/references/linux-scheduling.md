# Linux 定时任务设计

先人工跑通巡检脚本，再放入定时任务。

## 选择 cron 还是 systemd timer

cron：

- 简单；
- 适合每日固定时间运行；
- 容易部署；
- 状态和日志追踪较弱。

systemd timer：

- 更规范；
- 可以查看 timer/service 状态；
- 日志进入 journald；
- 配置略复杂。

## cron 示例

不要直接写入。先展示给用户确认。

```cron
# 每天 08:30 执行 OpenTenBase 巡检
30 8 * * * /bin/bash /data/opentenbase/ops/daily_check.sh >> /data/opentenbase/ops/logs/daily_check.log 2>&1
```

写入前确认：

```bash
crontab -l
ls -l /data/opentenbase/ops/daily_check.sh
bash -n /data/opentenbase/ops/daily_check.sh
```

写入后验证：

```bash
crontab -l
```

## systemd timer 示例

仅作为模板，不自动写入。

`/etc/systemd/system/opentenbase-daily-check.service`：

```ini
[Unit]
Description=OpenTenBase daily check

[Service]
Type=oneshot
User=<opentenbase_user>
ExecStart=/bin/bash /data/opentenbase/ops/daily_check.sh
```

`/etc/systemd/system/opentenbase-daily-check.timer`：

```ini
[Unit]
Description=Run OpenTenBase daily check

[Timer]
OnCalendar=*-*-* 08:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

启用前必须确认：

```bash
systemctl daemon-reload
systemctl enable --now opentenbase-daily-check.timer
systemctl list-timers --all | grep opentenbase-daily-check
```

这些命令会修改系统状态，必须等待用户确认。

## 脚本要求

巡检脚本应满足：

- 只读；
- 使用绝对路径；
- 明确 `PATH` 和 `LD_LIBRARY_PATH`；
- 输出时间、主机、结果；
- 失败时返回非零退出码；
- 不包含密码明文；
- 不执行清理、重启或写 SQL。

