# 故障排查

## 问题 1：2核服务器 GTM 启动失败

### 症状

```
FATAL: binding threads failed for 22
```

或：

```
ERROR: (08006) GTM error, could not obtain global timestamp. Current XID = 0, Autovac = 0
```

### 根因

2核 CPU 机器上 GTM 的 `pthread_setaffinity_np` 调用失败导致进程崩溃。

### 解决方案（脚本 v5.2.2+ 自动处理）

脚本采用四级下载策略获取预构建 `noaffinity.so`：

1. **GitHub Raw（优先）**：`https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/assets/noaffinity-x64.so`
2. **CDN fallback**：`https://repo.blackevil217.com/assets/noaffinity-x64.so`
3. **本地编译 fallback**：如果系统有 gcc，则现场编译
4. **跳过**：以上都失败时输出明确警告

下载后的验证流程：
- `mkdir -p` 确保目标目录存在
- `file` 命令验证下载文件是 ELF 格式（防止 CDN 返回 HTML 404 页面）
- 非 ELF 文件自动 fallback 到下一个源

```bash
# 手动修复（如果脚本版本旧）
mkdir -p /usr/lib/opentenbase
curl -sSL -o /usr/lib/opentenbase/noaffinity.so \
  https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/assets/noaffinity-x64.so
file /usr/lib/opentenbase/noaffinity.so  # 确认输出含 "ELF"
echo '/usr/lib/opentenbase/noaffinity.so' >> /etc/ld.so.preload
```

### 历史修复记录

| 提交 | 内容 |
|------|------|
| 5d474bb | noaffinity.so 创建鲁棒性增强 |
| eebf718 | 下载前 mkdir -p 确保目录存在 |
| 51ab4e6 | 下载后 file 命令验证 ELF 格式 |
| 452d5a0 | GitHub raw URL 优先，CDN fallback |

## 问题 2：libpq.so.5 依赖缺失

```bash
# 错误信息
libpq.so.5(RHPG_10) is needed by opentenbase

# 解决方案（脚本自动处理）
rpm -ivh --nodeps opentenbase-*.rpm
# 包自带 libpq.so.5，运行时不需要系统的
```

### libpq 版本警告（非阻断）

```
libpq.so.5: no version information available (required by libpqxx-7.9.so)
```

此警告不影响功能。OpenTenBase 运行时通过 `LD_LIBRARY_PATH` 正确链接自带 libpq.so.5.10，而非系统 libpq.so.5.15。

## 问题 3：libpq-devel 冲突

```bash
# 错误信息
file /usr/bin/pg_config conflicts with libpq-devel

# 解决方案（脚本自动处理）
rpm -e --nodeps libpq-devel
rpm -ivh --nodeps --replacefiles opentenbase-*.rpm
```

## 问题 4：端口被占用

```bash
ss -tlnp | grep -E '(6666|11003|15432)'
kill -9 <PID>
```

## 问题 5：内存不足

```bash
free -h
# 需要 ≥ 3GB
```