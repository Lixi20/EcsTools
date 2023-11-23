# ECSTools

## 使用

### 配置文件

根据所需平台复制`configs`目录下的配置文件`sample`

例如：腾讯云配置文件

```bash
cp configs/common.ini.sample configs/common.tx.ini
```

### 创建ECS

参数`-p`可选择对应ECS平台，可选值：al、hw、tx

例如：创建腾讯云ECS

```bash
python main.py -p tx -r
```

### 删除ECS

参数`-p`可选择对应ECS平台，可选值：al、hw、tx

例如：删除腾讯云`id`为xxx的ECS

```bash
python main.py -p tx -d xxx
```

### 启动ECS

参数`-p`可选择对应ECS平台，可选值：al、hw、tx

例如：启动腾讯云`id`为xxx的ECS

```bash
python main.py -p tx -s start xxx
```

### 关闭ECS

参数`-p`可选择对应ECS平台，可选值：al、hw、tx

例如：关闭腾讯云`id`为xxx的ECS

```bash
python main.py -p tx -s stop xxx
```

### 重启ECS

参数`-p`可选择对应ECS平台，可选值：al、hw、tx

例如：重启腾讯云`id`为xxx的ECS

```bash
python main.py -p tx -s restart xxx
```

## 腾讯云

### 获取访问密钥

https://console.cloud.tencent.com/cam/capi

点击左边导航栏的访问密钥->API密钥管理->获取之后对应配置文件中(SecretId/SecretKey)

```
access_key_id=AKIDCF5cFgXxxxxmhPt8A2g6HNHxSlpeFbje
access_key_secret=lHhfT5VKvHQKxxxxxxQ0PccR2QcgcJm4
```

### 资源区域

https://cloud.tencent.com/document/api/213/15692#.E5.9C.B0.E5.9F.9F.E5.88.97.E8.A1.A8

```
# 资源区域
region_id=ap-chengdu
```

### 实例区域

https://cloud.tencent.com/document/api/213/15753#ZoneInfo

根据资源区域选择实例区域

```
# 实例区域
zone_id=ap-chengdu-2
```

### 系统镜像

https://console.cloud.tencent.com/cvm/image/index?rid=1&tab=PRIVATE_IMAGE&imageType=PUBLIC_IMAGE

公共镜像、自定义镜像、共享镜像的镜像ID可通过登录控制台查询；服务镜像市场的镜像ID可通过云市场查询。

点击上方镜像下拉菜单->选择对应的地区->选择镜像ID

```
# 系统镜像
image_id=img-25szkc8t
```

### 安全组

https://console.cloud.tencent.com/vpc/security-group?rid=16&rid=16

```
# 安全组
security_group_id=sg-sxxxxx
```

### 网络计费、公网出带宽上限、是否分配公网IP

https://cloud.tencent.com/document/api/213/15753#InternetAccessible

```
# 网络计费
internet_charge_type=TRAFFIC_POSTPAID_BY_HOUR
# 最大出网带宽，单位为Mbit/s
internet_max_bandwidth_out=20
# 分配公网IP
public_ip_assigned=True
```

### 实例规格

https://cloud.tencent.com/document/product/213/11518

```
# 实例规格
instance_type=SA2.MEDIUM2
```

### 系统盘

https://cloud.tencent.com/document/api/213/15753#SystemDisk

```
# 系统盘大小
system_disk_size=20
# 系统盘类型
system_disk_type=CLOUD_BSSD
```

### 实例计费

* `PREPAID`：预付费，即包年包月
* `POSTPAID_BY_HOUR`：按小时后付费
* `CDHPAID`：独享子机（基于专用宿主机创建，宿主机部分的资源不收费）
* `SPOTPAID`：竞价付费
* `CDCPAID`：专用集群付费

默认值：POSTPAID_BY_HOUR。

```
# 实例计费
instance_charge_type=POSTPAID_BY_HOUR
```

### 专有网络交换机、私有网络子网ID、是否用作公网网关

https://cloud.tencent.com/document/api/213/15753#VirtualPrivateCloud

```
# 专有网络交换机
vswitch_id=DEFAULT
# 私有网络子网ID
subnet_id=DEFAULT
# 是否用作公网网关
as_vpc_gateway=False
```

### 密钥对

https://console.cloud.tencent.com/cvm/sshkey/index?rid=16&pid=-1

```
# 密钥对
key_pair_name=skey-sxxxxx
```

### 增强服务

https://cloud.tencent.com/document/api/213/15753#EnhancedService

```
# 开启云安全服务
security_service=True
# 开启云监控服
monitor_service=True
# 开启云自动化助手服务
automation_service=True
```

### Boolean	实例销毁保护标志

* `TRUE`：表示开启实例保护，不允许通过api接口删除实例

* `FALSE`：表示关闭实例保护，允许通过api接口删除实例

```
# 实例销毁保护标志
disable_api_termination=False
```

### 实例的关闭模式

https://cloud.tencent.com/document/api/213/15743

* `SOFT_FIRST`：表示在正常关闭失败后进行强制关闭

* `HARD`：直接强制关闭

* `SOFT`：仅软关机

```
# 实例的关闭模式
stop_type=SOFT
```

### 按量计费实例关机收费模式

https://cloud.tencent.com/document/api/213/15743

按量计费实例关机不收费说明: https://cloud.tencent.com/document/product/213/19918

* `KEEP_CHARGING`：关机继续收费

* `STOP_CHARGING`：关机停止收费

```
# 按量计费实例关机收费模式
stopped_mode=STOP_CHARGING
```

## 阿里云

### 获取访问密钥

https://www.alibabacloud.com/help/zh/doc-detail/107708.htm

操作步骤：
1. 以主账号登录阿里云管理控制台。
2. 将鼠标置于页面右上方的账号图标，单击AccessKey管理。
3. 在安全提示页面，选择获取主账号还是子账号的AccessKey。

```
access_key_id=AKIDCF5cFgXxxxxmhPt8A2g6HNHxSlpeFbje
access_key_secret=lHhfT5VKvHQKxxxxxxQ0PccR2QcgcJm4
```

### 资源区域

https://help.aliyun.com/zh/dts/developer-reference/supported-regions?spm=5176.21213303.J_7341193060.1.2cc22f3dwo6mX1&scm=20140722.S_help@@%E6%96%87%E6%A1%A3@@141033._.ID_help@@%E6%96%87%E6%A1%A3@@141033-RL_%E5%9C%B0%E5%9F%9F%E5%88%97%E8%A1%A8-LOC_llm-OR_ser-V_3-RK_rerank-P0_0

```
# 资源区域
region_id=cn-chengdu
```

### 实例区域

根据资源区域选择实例区域

```
# 实例区域
zone_id=cn-chengdu-a
```

### 系统镜像

https://help.aliyun.com/zh/ecs/user-guide/release-notes-for-2023?spm=a2c4g.11186623.0.0.1c571461RhPnFO#CentOS

```
# 系统镜像
image_id=centos_7_9_uefi_x64_20G_alibase_20230816.vhd
```

### 安全组

https://ecs.console.aliyun.com/?spm=5176.ecsnewbuy.0.0.61453675uuPy6w#/securityGroup/region/cn-chengdu

```
# 安全组
security_group_id=sg-bp1fg655nh68xyz9****
```

### 网络计费

* `PayByBandwidth`：按固定带宽计费
* `PayByTraffic`（默认）：按使用流量计费

```
# 网络计费
internet_charge_type=PayByTraffic
```

### 公网出/入带宽最大值

* 当所购出网带宽小于等于10 Mbit/s时：1~10。默认值为10
* 当所购出网带宽大于10 Mbit/s时：1~`InternetMaxBandwidthOut`的取值，默认为`InternetMaxBandwidthOut`的取值

```
# 最大出网带宽，单位为Mbit/s
internet_max_bandwidth_out=5
# 最大入网带宽，单位为Mbit/s
internet_max_bandwidth_in=50
```

### 实例规格

https://help.aliyun.com/zh/ecs/user-guide/overview-of-instance-families

```
# 实例规格
instance_type=ecs.t5-lc2m1.nano
```

### 实例计费

https://help.aliyun.com/zh/ecs/user-guide/overview-of-instance-families

* `PrePaid`：包年包月。选择该类付费方式时，您必须确认自己的账号支持余额支付/信用支付，否则将返回 InvalidPayMethod的错误提示
* `PostPaid`（默认）：按量付费

```
# 实例计费
instance_charge_type=PostPaid
```

### 专有网络交换机

https://vpc.console.aliyun.com/vpc/cn-chengdu/switches

```
# 专有网络交换机
vswitch_id=vsw-2vcdfx3klznbzv2yp7eup
```

### 系统盘大小

系统盘大小，单位为GiB

* 普通云盘：20~500
* 其他类型云盘：20~2048

```
# 系统盘大小
system_disk_size=20
```

### 系统盘类型

系统盘的云盘种类

* `cloud_essd`：ESSD云盘
* `cloud_efficiency`：高效云盘
* `cloud_ssd`：SSD云盘
* `cloud`：普通云盘

```
# 系统盘类型
system_disk_type=cloud_efficiency
```

### 密钥对

https://ecs.console.aliyun.com/?spm=5176.ecsnewbuy.0.0.61453675uuPy6w#/keyPair/region/cn-chengdu

```
# 密钥对
key_pair_name=geek
```

## 华为云

### 获取访问密钥（AK/SK，Access Key ID/Secret Access Key）

https://support.huaweicloud.com/usermanual-ca/ca_01_0003.html

每个访问密钥仅能下载一次，请妥善保管

获取之后对应配置文件中

```
access_key_id=
access_key_secret=
```

### 实例与可用区域 

https://developer.huaweicloud.com/endpoint?all

获取之后对应配置文件中

```
# 实例区域
region_id=
# 可用区域
zone_id=
```

### 系统镜像

https://console.huaweicloud.com/ecm/?agencyId=065a8d8ad90010a01f3fc00824adf351&region=cn-southwest-2&locale=zh-cn#/ims/manager/imageList/publicImage

获取之后对应配置文件中

```
# 系统镜像
image_id=
```

### 安全组

https://console.huaweicloud.com/ecm/?agencyId=&locale=zh-cn&region=cn-southwest-2#/vpc/secGroups

复制安全组ID之后对应配置文件中

```
# 安全组
security_group_id=
```

### 实例规格

https://support.huaweicloud.com/productdesc-ecs/zh-cn_topic_0159822360.html

对应配置文件中

```
# 实例规格
instance_type=
```

### 实例计费

* `postPaid`:按需付费

* `prePaid`:包年包月付费

```
# 实例计费
instance_charge_type=
```

### 带宽按量付费

字段值为空,表示按带宽计费

字段值为`traffic`表示按流量计费

字段为其它值,会导致创建云服务器失败

对应配置文件中

```
# 带宽按量付费
internet_charge_type=
```

### 自动续费

* `true`:自动续订

* `false`:不自动续订

对应配置文件中

```
# 带宽按量付费
auto_renew=
```

### 密钥对

https://console.huaweicloud.com/console/?region=cn-southwest-2&locale=zh-cn#/dew/kps/kpsList/privateKey

复制密钥对ID之后对应配置文件中

```
# 密钥对
key_pair_name=
```

### 专有网络交换机(VPC)

https://console.huaweicloud.com/vpc/?region=cn-southwest-2&locale=zh-cn#/vpc/vpcs/list

复制VPCID之后对应配置文件中

```
# 专有网络交换机
vswitch_id=
```

#### 子网ID

https://console.huaweicloud.com/vpc/?region=cn-southwest-2&locale=zh-cn#/vpc/subnets

复制子网ID之后对应配置文件中

```
# 子网id
subnet_id=
```

### 系统盘

#### 系统盘大小

更据所选的镜像填写

```
# 系统盘大小
system_disk_size=
```

#### 系统盘类型

* `SATA`：普通IO磁盘类型
* `SAS`：高IO磁盘类型
* `SSD`：超高IO磁盘类型
* `GPSSD`：通用型SSD磁盘类型
* `co-p1`：高IO (性能优化I型)
* `uh-l1`：超高IO (时延优化)
* `ESSD`：极速IO磁盘类型
* `GPSSD2`：通用型SSD V2磁盘类型
* `ESSD2`：极速型SSD V2磁盘类型

```
# 系统盘类型
system_disk_type=
```