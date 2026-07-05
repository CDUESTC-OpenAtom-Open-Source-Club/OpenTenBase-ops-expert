# 配置文件参考

## opentenbase_config.ini（v5.0）

```ini
[instance]
name=mycluster
type=distributed
package=/tmp/opentenbase-5.0.tar.gz

[gtm]
master=127.0.0.1

[coordinators]
master=127.0.0.1
nodes-per-server=1

[datanodes]
master=127.0.0.1
nodes-per-server=1

[server]
ssh-user=opentenbase
ssh-password=mypassword
ssh-port=22
```

## pgxc_ctl.conf（v2.x）

```bash
gtmMasterServer=127.0.0.1
gtmMasterPort=6666

coordNames=(cn001)
coordPorts=(5432)
coordMasterServers=(127.0.0.1)

datanodeNames=(dn001)
datanodePorts=(15432)
datanodeMasterServers=(127.0.0.1)
```

## 默认端口

| 角色 | v5.0 | v2.x |
|------|------|------|
| GTM | 6666 | 6666 |
| CN | 11003 | 5432 |
| DN | 15432 | 15432 |