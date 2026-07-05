# 集群管理

## opentenbase_ctl（v5.0）

```bash
opentenbase_ctl status              # 查看状态
opentenbase_ctl start               # 启动集群
opentenbase_ctl stop                # 停止集群
opentenbase_ctl expand -c config.ini  # 扩容节点
opentenbase_ctl shrink -c config.ini # 缩容节点
opentenbase_ctl delete -c config.ini # 删除集群
```

## pgxc_ctl（v2.x）

```bash
export PATH=/usr/lib/opentenbase/2.6/bin:$PATH
pgxc_ctl monitor all    # 查看状态
pgxc_ctl start all      # 启动
pgxc_ctl stop all       # 停止
```

## 连接数据库

```bash
# v5.0
psql -h 127.0.0.1 -p 11003 -U opentenbase -d postgres

# v2.x
psql -h 127.0.0.1 -p 5432 -U opentenbase -d postgres
```

## 常用 SQL

```sql
SELECT version();
SELECT * FROM pgxc_node;
SELECT pgxc_pool_reload();
CREATE TABLE t(id int) DISTRIBUTE BY SHARD(id);
```