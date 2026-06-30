# 日志位置

路径会随安装方式变化。先从配置、状态输出和数据目录推导，再有限搜索。

## 当前实验环境已验证

VERIFIED：

```text
/data/opentenbase/logs/opentenbase_ctl_*.log
/data/opentenbase/pgxc_ctl/pgxc_log/*_pgxc_ctl.log
/data/opentenbase/data/gtm/gtm_log/gtm-*.log
/data/opentenbase/data/coord_master/<cn>/pg_log/postgresql-*.log
/data/opentenbase/data/coord_master/<cn>/pg_ctl_start.log
/data/opentenbase/data/coord_master/<cn>/pg_ctl_stop.log
/data/opentenbase/data/dn_master/<dn>/pg_log/postgresql-*.log
/data/opentenbase/data/dn_master/<dn>/pg_ctl_start.log
/data/opentenbase/data/dn_master/<dn>/pg_ctl_stop.log
```

DOCUMENTED/常见：

- `opentenbase_ctl` 日志常在运行用户的 OpenTenBase 日志目录下。
- `pgxc_ctl` 日志常在控制目录的 `pgxc_log/` 下。
- CN/DN 日志通常在各自数据目录的 `pg_log/` 下。
- GTM 日志通常在 GTM 数据目录的 `gtm_log/` 下。

## 有限搜索

```bash
find /data/opentenbase /opt /usr/local /home -maxdepth 7 -type f \
  \( -name '*.log' -o -name '*.out' -o -name '*.err' -o -name '*.csv' -o -name 'postgresql-*' \) \
  -printf '%TY-%Tm-%Td %TH:%TM %s %p\n' 2>/dev/null | sort -r | head -n 80
```

禁止直接 `find /`。

## 读取方式

先看最近文件：

```bash
ls -lh --time-style=long-iso <log_dir> 2>/dev/null | tail -n 30
tail -n 100 <log_file>
```

按关键字提取：

```bash
grep -Ein 'ERROR|FATAL|PANIC|WARNING|could not|failed|invalid|permission denied|No such file|already in use|Connection refused|not found' <log_file> | tail -n 50
```

按时间窗口提取时，优先用日志自带时间戳；不要编辑日志文件。
