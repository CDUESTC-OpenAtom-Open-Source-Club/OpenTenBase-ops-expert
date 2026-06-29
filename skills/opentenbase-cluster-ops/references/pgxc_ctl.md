# pgxc_ctl

仅在主 `SKILL.md` 允许并经用户确认后使用。

先切换到 OpenTenBase 运行用户：

```bash
su - <opentenbase_user>
```

不要在 root 下直接用 `command -v pgxc_ctl` 判断工具不存在。

## 查找程序、配置和工作目录

```bash
command -v pgxc_ctl psql 2>/dev/null || true
type -a pgxc_ctl psql 2>/dev/null || true
```

找不到时有限搜索：

```bash
find /data /opt /usr/local /home /root -maxdepth 6 \
  \( -type f -o -type l \) \
  \( -name pgxc_ctl -o -name pgxc_ctl.conf -o -name psql \) \
  -print 2>/dev/null
```

禁止无边界执行 `find /`。

多个候选配置时，列出路径、所有者和修改时间，让用户选择。使用已有工作目录，不创建新的控制目录。

## 查看帮助

```bash
<pgxc_ctl> --help
<pgxc_ctl> --version
```

本机帮助与下列示例不同时，以本机帮助为准。

## 状态

```bash
<pgxc_ctl> --home <control_home> -c <pgxc_ctl.conf> monitor all
```

## 启动

```bash
<pgxc_ctl> --home <control_home> -c <pgxc_ctl.conf> start all
```

## 停止

```bash
<pgxc_ctl> --home <control_home> -c <pgxc_ctl.conf> stop -m fast all
```
