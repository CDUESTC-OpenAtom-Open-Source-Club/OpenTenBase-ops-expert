# 版本切换

## 查看已安装版本

```bash
opentenbase-switch-version
```

输出示例：
```
Installed OpenTenBase versions:
  5.0 (active)
  2.6.0
  2.5.0
```

## 切换版本

```bash
# 切换到 2.6.0
opentenbase-switch-version 2.6.0

# 切换到 5.0
opentenbase-switch-version 5.0
```

## 注意事项

- 切换前需停止当前版本的集群
- 切换后需重新初始化集群
- 支持版本：5.0 / 2.6.0 / 2.5.0

## 安装指定版本

```bash
# 安装 2.6.0
sudo bash opentenbase.sh --yes --version 2.6.0

# 安装 5.0
sudo bash opentenbase.sh --yes --version 5.0
```