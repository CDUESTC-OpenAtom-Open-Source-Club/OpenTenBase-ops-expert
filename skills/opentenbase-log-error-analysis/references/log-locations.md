# 日志位置

路径会随安装方式变化。先从配置、状态输出和数据目录推导，再有限搜索。

## 已知的两种部署方式日志路径

### 方式 A：源码编译 + pgxc_ctl 部署

此时日志目录在配置的 `$DATA_DIR` 下：

```text
/data/opentenbase/logs/pgxc_ctl_*.log
/data/opentenbase/pgxc_ctl/pgxc_log/*_pgxc_ctl.log
/data/opentenbase/gtm*/gtm_log/gtm-*.log
/data/opentenbase/cn*/pg_log/postgresql-*.log
/data/opentenbase/dn*/pg_log/postgresql-*.log
```

### 方式 B：RPM/DEB 包安装（opentenbase-ctl）

```text
/var/lib/opentenbase/*/log/pgxc_ctl_*.log
/var/lib/opentenbase/*/data/gtm/gtm_log/gtm-*.log
/var/lib/opentenbase/*/data/coord_master/<cn>/pg_log/postgresql-*.log
/var/lib/opentenbase/*/data/dn_master/<dn>/pg_log/postgresql-*.log
```

其中 `*` 代表版本号，如 `5.0`。

## 自动定位命令（不限部署方式）

```bash
# 从进程获取数据目录
ps -ef | grep -E '[p]ostgres.*-D ' | grep -oP '\(s*-D\s*)\K[^ ]+' | head -1 2>/dev/null

# 找到 last 修改的 log 文件，按目录量级打印
for d in /data/opentenbase /var/lib/opentenbase /opt /usr/local; do
  [ -d "$d" ] || continue
  find "$d" -maxdepth 6 -type f \( -name '*.log' -o -name 'postgresql-*' \) 2>/dev/null | head -20
  break
done
```

## 有限搜索

```bash
find /data/opentenbase /var/lib/opentenbase /opt /usr/local /home -maxdepth 7 -type f \
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
