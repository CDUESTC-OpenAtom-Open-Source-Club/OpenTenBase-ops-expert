# 源码编译单节点部署

适用于无包管理器或需要自定义编译的环境。

## 编译依赖

```bash
# Debian/Ubuntu
apt-get install git gcc g++ make flex bison perl libreadline-dev zlib1g-dev libssl-dev

# RHEL/CentOS
dnf install git gcc gcc-c++ make flex bison perl readline-devel zlib-devel openssl-devel
```

## 编译安装

```bash
git clone https://github.com/OpenTenBase/OpenTenBase.git
cd OpenTenBase
./configure --prefix=/usr/lib/opentenbase/5.0
make -sj$(nproc)
make install
```

## 初始化集群

```bash
opentenbase_ctl install -c /tmp/opentenbase_config.ini
opentenbase_ctl start
```

## pgxc_ctl 方式（v2.x）

```bash
cd OpenTenBase
./configure --prefix=/data/opentenbase/install
make && make install

# 配置 pgxc_ctl.conf
pgxc_ctl init all
pgxc_ctl start all
```