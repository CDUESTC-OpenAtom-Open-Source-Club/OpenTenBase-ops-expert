# 内存自动调优

## 调优规则

| 内存范围 | shared_buffers | work_mem | max_connections |
|----------|----------------|----------|-----------------|
| 1-2 GB | 64MB | 4MB | 20 |
| 2-4 GB | 128MB | 8MB | 50 |
| 4-8 GB | 256MB | 16MB | 100 |
| 8-16 GB | 512MB | 32MB | 200 |
| >16 GB | 1GB | 64MB | 300 |

## 一键脚本自动调优

```bash
# 默认启用
sudo bash opentenbase.sh --yes

# 禁用
sudo bash opentenbase.sh --yes --no-auto-tune-mem
```

## tune 子命令

```bash
# 自动调优
opentenbase.sh tune --auto --reload

# 自定义参数
opentenbase.sh tune --custom --params 'shared_buffers=1GB work_mem=32MB' --restart
```

## 参数说明

| 参数 | 作用 |
|------|------|
| shared_buffers | 共享内存缓冲区 |
| work_mem | 单操作内存限制 |
| max_connections | 最大连接数 |

## 生效方式

- reload: work_mem 等立即生效
- restart: shared_buffers 需重启