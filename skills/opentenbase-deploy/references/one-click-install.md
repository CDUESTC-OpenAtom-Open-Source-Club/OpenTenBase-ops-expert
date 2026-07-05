# 一键安装

## 基础命令

```bash
# 交互式
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/opentenbase.sh | sudo bash

# 非交互式
curl -sSL https://raw.githubusercontent.com/CDUESTC-OpenAtom-Open-Source-Club/OpenTenBase-Packages/main/scripts/opentenbase.sh | sudo bash -s -- --yes
```

## 参数说明

```bash
--yes              # 非交互式
--version VER      # 版本（5.0/2.6.0/2.5.0）
--cluster-name     # 集群名
--gtm-ip           # GTM IP
--cn-ip            # CN IP
--dn-ip            # DN IP
--ssh-password     # SSH 密码
--deploy-mode      # single/single-multi/multi
--cn-count         # CN 数量
--dn-count         # DN 数量
--auto-tune-mem    # 内存调优（默认开启）
--clean            # 清理旧数据
```

## 自动处理

脚本自动处理：
- 系统检测
- 仓库配置
- 依赖冲突
- 2核 CPU 问题（noaffinity.so 四级下载策略 + ELF 验证）
- libpq 版本冲突（LD_LIBRARY_PATH 隔离）
- 内存调优

### libpq 版本警告

```
libpq.so.5: no version information available (required by libpqxx-7.9.so)
```

此警告不影响功能。OpenTenBase 运行时通过 `LD_LIBRARY_PATH` 正确链接自带 libpq.so.5.10，而非系统 libpq.so.5.15。