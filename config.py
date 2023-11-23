#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from enum import Enum

from happy_python import HappyConfigBase


class InternetChargeType(Enum):
    """
    网络计费类型
    """
    pay_by_traffic = 'PayByTraffic'  # 按使用流量计费
    pay_by_bandwidth = 'PayByBandwidth'  # 按固定带宽计费


class IoOptimized(Enum):
    """
    是否为I/O优化实例
    """
    optimized = 'optimized'  # I/O优化
    none = 'none'  # 非I/O优化


class InstanceChargeType(Enum):
    """
    实例的付费方式
    """
    post_paid = 'PostPaid'  # 按量付费
    pre_paid = 'PrePaid'  # 包年包月。选择该类付费方式时，您必须确认自己的账号支持余额支付/信用支付，否则将返回 InvalidPayMethod的错误提示。


class SecurityEnhancementStrategy(Enum):
    """
    是否开启安全加固
    """
    active = 'Active'  # 启用安全加固，只对系统镜像生效。
    deactive = 'Deactive'  # 不启用安全加固，对所有镜像类型生效。


class PlatformConfig(HappyConfigBase):
    def __init__(self, platform):
        super().__init__()
        if str(platform).__eq__("tx"):
            self.section = 'tx'

            self.public_ip_assigned = True
            self.disable_api_termination = False
            self.as_vpc_gateway = False
            self.security_service = True
            self.monitor_service = True
            self.automation_service = True
            self.stop_type = ''
            self.stopped_mode = ''
        elif str(platform).__eq__("al"):
            self.section = 'al'

            self.internet_max_bandwidth_in = ''
            self.security_enhancement_strategy = ''
            self.io_optimized = ''
            self.platform = ''
        elif str(platform).__eq__("hw"):
            self.section = 'hw'

            self.security_service = ''


class Config(HappyConfigBase):
    """
    配置文件模板
    """

    def __init__(self):
        super().__init__()

        self.section = 'main'

        self.subnet_id = ''
        self.system_disk_size = 20
        self.system_disk_type = ''
        self.instance_charge_type = ''
        self.access_key_id = ''
        self.access_key_secret = ''
        self.region_id = ''
        self.zone_id = ''
        self.image_id = ''
        self.security_group_id = ''
        self.instance_name = ''
        self.host_name = ''
        self.internet_charge_type = ''
        self.auto_renew = False
        self.internet_max_bandwidth_out = 5
        self.instance_type = ''
        self.key_pair_name = ''
        self.vswitch_id = ''
        self.default_ss_server_port = 0
        self.release_time = ''
