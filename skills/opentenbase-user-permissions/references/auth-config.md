# 认证配置

本文件用于排查“用户能否连上数据库”，重点是 `pg_hba.conf` 和 `pg_ident.conf`。默认只读审计，不自动修改。

## 常见文件

每个 CN/DN 数据目录可能有：

```text
pg_hba.conf
pg_ident.conf
```

应用通常连接 CN，认证问题优先检查目标 CN 的配置。不要把 DN 当普通业务登录入口。

## 只读检查

确认目标连接：

```text
client_ip
cn_host
cn_port
database
user
error message
```

读取配置：

```bash
su - <opentenbase_user>
sed -n '1,220p' <pg_hba.conf>
sed -n '1,220p' <pg_ident.conf>
```

连接测试：

```bash
PGCONNECT_TIMEOUT=5 psql -X -h <cn_host> -p <cn_port> \
  -U <user> -d <database> -c 'SELECT 1;'
```

## 判断重点

- 是否有匹配的 host/local 规则；
- database、user、address 是否匹配；
- 认证方式是否符合预期；
- `reject` 或更靠前规则是否拦截；
- 多 CN 环境是否只改了一个 CN；
- 报错是认证失败、无权限、数据库不存在，还是网络不可达。

## 修改前必须确认

修改前展示：

```text
目标 CN
配置文件路径
新增或修改的规则
规则顺序
影响的用户和来源网段
回滚方式
是否需要 reload
```

先备份：

```bash
cp -a <pg_hba.conf> <pg_hba.conf>.bak.$(date +%Y%m%d%H%M%S)
```

## 禁止自动执行

未经用户确认，不执行：

```text
编辑 pg_hba.conf
编辑 pg_ident.conf
reload/restart
放开 0.0.0.0/0 trust
授予 SUPERUSER
```

## 修改后验证

用户确认并完成修改后，验证：

```bash
psql -h <cn_host> -p <cn_port> -U <user> -d <database> -c 'SELECT current_user, current_database();'
```

失败时保留原始错误，不要把认证失败误判为权限不足。
