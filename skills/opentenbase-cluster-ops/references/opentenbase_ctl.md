# opentenbase_ctl

默认使用本工具管理集群。

先切换到 OpenTenBase 运行用户：

```bash
su - <opentenbase_user>
```

不要在 root 下直接用 `command -v opentenbase_ctl` 判断工具不存在。

## 查找程序和配置

```bash
command -v opentenbase_ctl psql 2>/dev/null || true
type -a opentenbase_ctl psql 2>/dev/null || true
```

找不到时有限搜索：

```bash
find /data /opt /usr/local /home /root -maxdepth 6 \
  \( -type f -o -type l \) \
  \( -name opentenbase_ctl -o -name psql \
     -o -name opentenbase_config.ini -o -name config.ini \) \
  -print 2>/dev/null
```

禁止无边界执行 `find /`。

多个候选配置时，列出路径、所有者和修改时间，让用户选择：

```bash
ls -l --time-style=long-iso <candidate-files>
```

## 查看帮助

```bash
<opentenbase_ctl> -h
<opentenbase_ctl> --version
<opentenbase_ctl> status -h
<opentenbase_ctl> start -h
<opentenbase_ctl> stop -h
```

本机帮助与下列示例不同时，以本机帮助为准。

## 状态

```bash
<opentenbase_ctl> status -c <config.ini>
```

## 启动

```bash
<opentenbase_ctl> start -c <config.ini>
```

## 停止

```bash
<opentenbase_ctl> stop -c <config.ini>
```

## 可用性检查

```bash
ls -l <opentenbase_ctl> <config.ini>
ldd <opentenbase_ctl> 2>/dev/null | grep 'not found' || true
```

程序不存在、无法执行、缺少动态库或配置无法读取时，报告原因。
