# 多节点部署

## 单机多节点

```bash
sudo bash opentenbase.sh --yes \
    --deploy-mode single-multi \
    --cn-count 2 \
    --dn-count 3
```

节点分布：
- GTM: 1个，端口 6666
- CN: 2个，端口 11003, 11006
- DN: 3个，端口 15432, 15435, 15438

## 多机多节点

```bash
sudo bash opentenbase.sh --yes \
    --deploy-mode multi \
    --gtm-ip 192.168.1.10 \
    --cn-ip 192.168.1.11 \
    --dn-ip 192.168.1.12
```

注意：多机模式需预先配置 SSH 信任。

## 验证节点

```sql
SELECT node_name, node_type, node_host, node_port FROM pgxc_node;
```