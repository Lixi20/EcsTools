#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import PurePath
from time import sleep

from happy_python import get_exit_code_of_cmd, HappyConfigParser
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkecs.v2 import *
from huaweicloudsdkecs.v2.region.ecs_region import EcsRegion
from huaweicloudsdkcore.exceptions import exceptions
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.cvm.v20170312 import cvm_client, models
from alibabacloud_ecs20140526.client import Client as Ecs20140526Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ecs20140526 import models as ecs_20140526_models
from alibabacloud_tea_util import models as util_models

from common import hlog, CONFIG_DIR
from config import PlatformConfig, Config

ECS_INFO_FILENAME = 'last_ecs_info.json'
ECS_INFO_FILE = str(PurePath(__file__).parent / ECS_INFO_FILENAME)
ecs_client = None
runtime = util_models.RuntimeOptions()


class Father(object):

    def __init__(self):
        pass

    def get_client(self):
        pass

    def create(self, arg):
        pass

    def delete(self, instance_id):
        pass

    def start(self, instance_id):
        pass

    def stop(self, instance_id):
        pass

    def restart(self, instance_id):
        pass


def upload_sh(ip):
    sh_file = PurePath(__file__).parent / 'tesh.sh'
    result = get_exit_code_of_cmd('scp -o StrictHostKeyChecking=no %s root@%s:/root/tesh.sh' % (sh_file, ip),
                                  is_raise_exception=True,
                                  is_show_error=False)

    if result == 0:
        hlog.info('上传SS安装文件成功')
    else:
        hlog.error('上传SS安装文件失败')


def switch_case(case):
    if case == 'hw':
        return '华为云'
    elif case == 'al':
        return '阿里云'
    elif case == "tx":
        return '腾讯云'


@dataclass
class EcsInfo:
    instance_id: str
    ip: str
    ss_port: int
    naive_release_time: str
    utc_release_time: str


class EcsInfoManager:
    @staticmethod
    def load():
        try:
            with open(ECS_INFO_FILE, 'r') as f:
                info = json.load(f)
                return EcsInfo(instance_id=info['instance_id'],
                               ip=info['ip'],
                               ss_port=info['ss_port'],
                               naive_release_time=info['naive_release_time'],
                               utc_release_time=info['utc_release_time'])
        except FileNotFoundError:
            hlog.error('%s 文件不存在' % ECS_INFO_FILENAME)

    @staticmethod
    def save(instance_id, ip, ss_port, naive_release_time=None, utc_release_time=None):
        with open(ECS_INFO_FILE, 'w') as f:
            f.write(json.dumps({'instance_id': instance_id,
                                'ip': ip,
                                'ss_port': ss_port,
                                'naive_release_time': naive_release_time,
                                'utc_release_time': utc_release_time}, indent=2))
            return EcsInfo(instance_id=instance_id,
                           ip=ip,
                           ss_port=ss_port,
                           naive_release_time=naive_release_time,
                           utc_release_time=utc_release_time)


class hw(Father):
    def get_client(self):
        hlog.enter_func('hw-get_client')
        hlog.info('初始化华为云Client...')
        hlog.info('校验ID和Secret...')
        id_match = re.fullmatch(r'[0-9a-zA-Z]{20}', config.access_key_id)
        secret_match = re.fullmatch(r'[0-9a-zA-Z]{40}', config.access_key_secret)

        if not id_match:
            hlog.error('ID校验失败,请检查配置文件中是否正确')
            exit()
        elif not secret_match:
            hlog.error('Secret校验失败,请检查配置文件中是否正确')
            exit()
        try:
            credentials = BasicCredentials(config.access_key_id, config.access_key_secret)
            client = EcsClient.new_builder().with_credentials(credentials).with_region(
                EcsRegion.value_of(config.region_id)).build()
            hlog.exit_func('hw-get_client')
            return client
        except exceptions.ApiValueError:
            hlog.error('ID或Secret无效，请检查配置文件中是否正确')
            exit()
        except exceptions.ConnectionException:
            hlog.error('网络连接失败，请检查网络配置')
            exit()
        except KeyError:
            hlog.error('实例区域ID无效，请检查配置文件中是否正确')
            exit()

    def create(self, arg):
        hlog.enter_func('hw-create')

        hlog.info('开始创建带 DryRun 测试运行标记的华为云ECS实例' if arg.dry_run else '开始创建华为云ECS实例')

        if os.path.exists(ECS_INFO_FILE):
            hlog.info('在%s文件中发现已经创建过ECS实例，请删除实例后再试' % ECS_INFO_FILENAME)
            return

        if not platform_config.security_service == 'hss,hss-ent' and not platform_config.security_service == 'hss':
            hlog.error('企业主机安全(security_service)设置无效,参考值：“hss“(基础版)、“hss,hss-ent“(企业版)')
            exit()

        try:
            request = CreateServersRequest()
            request.body = CreateServersRequestBody(
                dry_run=arg.dry_run,
                server=PrePaidServer(
                    key_name=config.key_pair_name,
                    image_ref=config.image_id,
                    flavor_ref=config.instance_type,
                    name=config.instance_name,
                    vpcid=config.vswitch_id,
                    extendparam=PrePaidServerExtendParam(
                        is_auto_renew=config.auto_renew,
                        charging_mode=config.instance_charge_type,
                    ),
                    availability_zone=config.zone_id,
                    security_groups=[
                        PrePaidServerSecurityGroup(
                            id=config.security_group_id
                        )
                    ],
                    root_volume=PrePaidServerRootVolume(
                        volumetype=config.system_disk_type,
                        size=config.system_disk_size,
                        hwpassthrough=False
                    ),
                    nics=[
                        PrePaidServerNic(
                            subnet_id=config.subnet_id
                        )
                    ],
                    metadata={
                        "__support_agent_list": "ces,%s" % platform_config.security_service
                    },
                    publicip=PrePaidServerPublicip(
                        eip=PrePaidServerEip(
                            iptype="5_sbgp",
                            extendparam=PrePaidServerEipExtendParam(
                                charging_mode="postPaid"
                            ),
                            bandwidth=PrePaidServerEipBandwidth(
                                size=int(config.internet_max_bandwidth_out),
                                sharetype="PER",
                                chargemode=config.internet_charge_type
                            )
                        )
                    )
                )
            )
            hlog.debug('ECS配置: %s' % request.body.server)
            response = ecs_client.create_servers(request)
            if not arg.dry_run:
                instance_id = response.server_ids[0]
                hlog.info('ECS实例“%s”：创建成功' % instance_id)
                sleep(5)
                # 查询实例状态成功，确保已经创建完毕
                while True:
                    try:
                        request = ShowServerRequest()
                        request.server_id = instance_id
                        response = ecs_client.show_server(request)
                        hlog.info('等待“ACTIVE”状态。当前状态：%s' % response.server.status)

                        if response.server.status == 'ACTIVE':
                            break

                    except exceptions.ClientRequestException as e:
                        hlog.error(e.error_msg)
                    sleep(5)
                ip = ""
                sleep(8)

                while True:
                    request = ShowServerRequest()
                    request.server_id = instance_id
                    response = ecs_client.show_server(request)
                    addresses = response.server.addresses[config.vswitch_id]

                    for i in addresses:
                        json_object = json.loads(str(i))
                        if not str(json_object['addr']).startswith('192') and str(
                                json_object['OS-EXT-IPS:type']) == 'floating':
                            ip = json_object['addr']
                    if ip != '' and ip.startswith('1'):
                        hlog.info('ECS实例“%s”：添加公网IP成功' % instance_id)
                        break
                    else:
                        hlog.info('ECS实例“%s”：公网IP获取失败,3秒后重试' % instance_id)
                        sleep(3)
                EcsInfoManager.save(instance_id, ip, config.default_ss_server_port)
                sleep(5)

                while True:
                    hlog.info('ECS实例“%s”：PING测试...' % instance_id)

                    result = get_exit_code_of_cmd('ping -W 1 -c 10 %s' % ip, is_show_error=False)

                    if result == 0:
                        hlog.info('ECS实例“%s”：PING测试成功' % instance_id)
                        break
                    else:
                        hlog.info('ECS实例“%s”：PING测试失败，5秒后重试' % instance_id)
                        sleep(5)
                sleep(5)

                upload_sh(ip)
            else:
                hlog.info('带 DryRun 测试运行标记的华为云ECS实例创建成功')

            hlog.exit_func('hw-create')

        except exceptions.ClientRequestException as e:
            code = e.error_code
            msg = str(e.error_msg)

            if code == 'Ecs.0304':
                hlog.error('查询镜像失败,请确认镜像ID(image_id)是否正确，错误信息：%s' % msg)
            elif code == 'Ecs.0303':
                hlog.error('查询实例规格失败,请确认实例规格(instance_type)是否正确，错误信息：%s' % msg)
            elif code == 'Ecs.0314':
                hlog.error('查询密钥对失败,请确认密钥对(key_pair_name)是否正确，错误信息：%s' % msg)
            elif code == 'Ecs.0064':
                hlog.error('查询VPC ID失败,请求体中的vpcId与主网卡的vpcId不一致,错误信息：%s' % msg)
            elif code == 'Ecs.0067':
                hlog.error('账户余额不足,请充值,错误信息：%s' % msg)
            elif code == 'Ecs.0005':
                if msg.__contains__('Security group'):
                    hlog.error('安全组(security_group_id)设置无效，错误信息：%s' % msg)
                elif msg.__contains__('availability_zone'):
                    hlog.error('可用区域(zone_id)设置无效，错误信息：%s' % msg)
                elif msg.__contains__('chargingMode'):
                    hlog.error('实例计费(instance_charge_type)设置无效，错误信息：%s' % msg)
                elif msg.__contains__('eip charge mode'):
                    hlog.error('带宽按量付费(internet_charge_type)设置无效，错误信息：%s' % msg)
                elif msg.__contains__('rootVolume'):
                    hlog.error('系统盘类型(system_disk_type)设置无效，错误信息：%s' % msg)
            else:
                hlog.error('Code:%s,Meg:%s' % (code, msg))

    def delete(self, instance_id):
        hlog.enter_func('hw-delete')
        hlog.info('删除指定ECS:%s' % instance_id)
        id_match = re.fullmatch(r'[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}', instance_id)
        if not id_match:
            hlog.error('ECS ID校验失败,请检查是否输入正确')
            exit()

        try:
            request = DeleteServersRequest()
            request.body = DeleteServersRequestBody(
                servers=[
                    ServerId(
                        id=instance_id
                    )
                ],
                delete_volume=True,
                delete_publicip=True
            )
            ecs_client.delete_servers(request)

            if os.path.exists(ECS_INFO_FILE):
                os.unlink(ECS_INFO_FILE)

            hlog.info('ECS实例“%s”：删除成功' % instance_id)
            hlog.exit_func('hw-delete')
        except exceptions.ClientRequestException as e:
            hlog.error('ECS实例“%s”：删除失败,错误信息：%s' % (instance_id, e.error_msg))

    def start(self, instance_id):
        hlog.enter_func('hw-start')
        hlog.info('ECS实例“%s”：启动' % instance_id)
        try:
            request = BatchStartServersRequest()
            request.body = BatchStartServersRequestBody(
                os_start=BatchStartServersOption(
                    servers=[
                        ServerId(
                            id=instance_id
                        )
                    ]
                )
            )
            ecs_client.batch_start_servers(request)
            hlog.info('ECS实例“%s”：启动成功' % instance_id)
            hlog.exit_func('hw-start')
        except exceptions.ClientRequestException as e:
            hlog.info('ECS实例“%s”启动失败，错误信息：%s' % (instance_id, e.error_msg))

    def stop(self, instance_id):
        hlog.enter_func('hw-stop')
        hlog.info('ECS实例“%s”：关闭' % instance_id)
        try:
            request = BatchStopServersRequest()
            request.body = BatchStopServersRequestBody(
                os_stop=BatchStopServersOption(
                    servers=[
                        ServerId(
                            id=instance_id
                        )
                    ]
                )
            )
            ecs_client.batch_stop_servers(request)
            hlog.info('ECS实例“%s”：关闭成功' % instance_id)
            hlog.exit_func('hw-stop')
        except exceptions.ClientRequestException as e:
            hlog.info('ECS实例“%s”关闭失败，错误信息：%s' % (instance_id, e.error_msg))

    def restart(self, instance_id):
        hlog.enter_func('hw-restart')
        hlog.info('ECS实例“%s”：重启' % instance_id)
        try:
            request = ShowServerRequest()
            request.server_id = instance_id
            response = ecs_client.show_server(request)

            if response.server.status == 'SHUTOFF':
                hlog.error('ECS实例“%s”：正处于关闭状态,无法重启，请先开启ECS' % instance_id)
                exit()

            request = BatchRebootServersRequest()
            listServersReboot = [
                ServerId(
                    id=instance_id
                )
            ]
            request.body = BatchRebootServersRequestBody(
                reboot=BatchRebootSeversOption(
                    servers=listServersReboot,
                    # SOFT:普通重启 HARD: 强制重启。
                    type="SOFT"
                )
            )
            ecs_client.batch_reboot_servers(request)
            hlog.info('ECS实例“%s”：重启成功' % instance_id)
            hlog.exit_func('hw-restart')
        except exceptions.ClientRequestException as e:
            hlog.info('ECS实例“%s”重启失败，错误信息：%s' % (instance_id, e.error_msg))


class tx(Father):
    def get_client(self):
        cred = credential.Credential(secret_id=config.access_key_id,
                                     secret_key=config.access_key_secret)
        httpProfile = HttpProfile()
        httpProfile.endpoint = 'cvm.tencentcloudapi.com'

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        return cvm_client.CvmClient(cred, config.region_id, clientProfile)

    def create(self, arg):
        fn_name = '腾讯云平台'
        hlog.enter_func(fn_name)

        if os.path.exists(ECS_INFO_FILE):
            hlog.info('在%s文件中发现已经创建过腾讯云ECS实例，请删除实例后再试' % ECS_INFO_FILENAME)
            exit(1)

        try:
            hlog.info('开始创建带 DryRun 测试运行标记的腾讯云ECS实例' if arg.dry_run else '开始创建腾讯云ECS实例')

            run_instance_req = models.RunInstancesRequest()
            run_instance_params = {
                "DryRun": args.dry_run,
                "InstanceChargeType": config.instance_charge_type,
                "DisableApiTermination": platform_config.disable_api_termination,
                "Placement": {
                    "Zone": config.zone_id,
                },
                "VirtualPrivateCloud": {
                    "AsVpcGateway": platform_config.as_vpc_gateway,
                    "VpcId": config.vswitch_id,
                    "SubnetId": config.subnet_id
                },
                "InstanceType": config.instance_type,
                "ImageId": config.image_id,
                "SystemDisk": {
                    "DiskSize": config.system_disk_size,
                    "DiskType": config.system_disk_type
                },
                "InternetAccessible": {
                    "InternetMaxBandwidthOut": config.internet_max_bandwidth_out,
                    "PublicIpAssigned": platform_config.public_ip_assigned,
                    "InternetChargeType": config.internet_charge_type
                },
                "InstanceName": config.instance_name,
                "LoginSettings": {
                    "KeyIds": [config.key_pair_name]
                },
                "SecurityGroupIds": [config.security_group_id],
                "EnhancedService": {
                    "SecurityService": {
                        "Enabled": platform_config.security_service
                    },
                    "MonitorService": {
                        "Enabled": platform_config.monitor_service
                    },
                    "AutomationService": {
                        "Enabled": platform_config.automation_service
                    }
                },
                "HostName": config.host_name
            }
            hlog.var('run_instance_params', run_instance_params)
            run_instance_req.from_json_string(json.dumps(run_instance_params))

            run_instance_resp = ecs_client.RunInstances(run_instance_req)
            hlog.var('run_instance_resp', run_instance_resp)

            if run_instance_resp.InstanceIdSet:
                instance_id = run_instance_resp.InstanceIdSet[0]

                hlog.info('腾讯云ECS实例“%s”：创建成功' % instance_id)

                # 查询实例状态成功，确保已经创建完毕
                is_created = False

                hlog.info('腾讯云ECS实例“%s”：查看状态' % instance_id)

                while True:
                    try:
                        describe_instances_status_req = models.DescribeInstancesStatusRequest()
                        describe_instances_status_params = {
                            "InstanceIds": [instance_id]
                        }
                        hlog.var('describe_instances_status_params', describe_instances_status_params)
                        describe_instances_status_req.from_json_string(json.dumps(describe_instances_status_params))

                        describe_instances_status_resp = ecs_client.DescribeInstancesStatus(
                            describe_instances_status_req)

                        hlog.var('describe_instances_status_resp', describe_instances_status_resp)

                        InstanceStateInfo = describe_instances_status_resp.InstanceStatusSet[0]
                        hlog.info('等待“RUNNING”状态。当前状态：%s' % InstanceStateInfo.InstanceState)

                        if InstanceStateInfo.InstanceId == instance_id and InstanceStateInfo.InstanceState == 'RUNNING':
                            is_created = True

                        if is_created:
                            break

                    except Exception as e:
                        hlog.error(e)

                    sleep(5)

                hlog.info('腾讯云ECS实例“%s”：获取公网IP' % instance_id)

                describe_instances_req = models.DescribeInstancesRequest()
                describe_instances_params = {
                    "InstanceIds": [instance_id]
                }
                hlog.var('describe_instances_params', describe_instances_params)
                describe_instances_req.from_json_string(json.dumps(describe_instances_params))

                describe_instances_resp = ecs_client.DescribeInstances(describe_instances_req)
                hlog.var('describe_instances_resp', describe_instances_resp)

                ip = describe_instances_resp.InstanceSet[0].PublicIpAddresses[0]

                hlog.info('腾讯云ECS实例“%s”：公网IP获取成功' % instance_id)

                EcsInfoManager.save(instance_id, ip, config.default_ss_server_port)
                hlog.info('腾讯云ECS实例“%s”：信息已保存 “%s”' % (instance_id, ECS_INFO_FILE))

                hlog.info('腾讯云ECS实例“%s”：PING测试...' % instance_id)
                while True:
                    result = get_exit_code_of_cmd('ping -W 1 -c 10 %s' % ip, is_show_error=False)

                    if result == 0:
                        hlog.info('腾讯云ECS实例“%s”：PING测试成功' % instance_id)
                        break
                    else:
                        hlog.info('腾讯云ECS实例“%s”：PING测试失败，5秒后重试' % instance_id)
                        sleep(5)

                upload_sh(ip)

            else:
                hlog.debug('params: %s' % str(run_instance_params))
                hlog.debug('run_instance_resp: %s' % str(run_instance_resp))

                hlog.info('带 DryRun 测试运行标记的腾讯云ECS实例创建成功')

        except TencentCloudSDKException as err:
            if str(err).find('请求签名验证失败，请检查您的签名计算是否正确') != -1:
                hlog.error('创建腾讯云ECS实例失败')
                hlog.error('SecretKey不正确，请输入正确的密钥')
                exit(1)
            else:
                hlog.error('创建腾讯云ECS实例失败')
                hlog.error(err)
                exit(1)

        hlog.exit_func(fn_name)

    def delete(self, instance_id):
        fn_name = '腾讯云平台'
        hlog.enter_func(fn_name)

        hlog.info('开始删除腾讯云ECS实例“%s”' % instance_id)

        try:
            terminate_instances_req = models.TerminateInstancesRequest()
            terminate_instances_params = {
                "InstanceIds": [instance_id]
            }
            hlog.var('terminate_instances_params', terminate_instances_params)
            terminate_instances_req.from_json_string(json.dumps(terminate_instances_params))

            terminate_instances_resp = ecs_client.TerminateInstances(terminate_instances_req)
            hlog.var('terminate_instances_resp', terminate_instances_resp)

            if os.path.exists(ECS_INFO_FILE):
                os.unlink(ECS_INFO_FILE)

        except TencentCloudSDKException as err:
            hlog.error('腾讯云ECS实例“%s”：删除失败' % instance_id)
            hlog.error(err)
            exit(1)

        hlog.info('腾讯云ECS实例“%s”：删除成功' % instance_id)

        hlog.exit_func(fn_name)

    def start(self, instance_id):
        fn_name = '腾讯云平台'
        hlog.enter_func(fn_name)

        hlog.info('开始启动腾讯云ECS实例“%s”' % instance_id)

        try:
            start_instances_req = models.StartInstancesRequest()
            start_instances_params = {
                "InstanceIds": [instance_id]
            }
            hlog.var('start_instances_params', start_instances_params)
            start_instances_req.from_json_string(json.dumps(start_instances_params))

            start_instances_resp = ecs_client.StartInstances(start_instances_req)
            hlog.var('start_instances_resp', start_instances_resp)

        except TencentCloudSDKException as err:
            hlog.error('腾讯云ECS实例“%s”：启动失败' % instance_id)
            hlog.error(err)
            exit(1)

        hlog.info('腾讯云ECS实例“%s”：启动成功' % instance_id)

        hlog.exit_func(fn_name)

    def stop(self, instance_id):
        fn_name = '腾讯云平台'
        hlog.enter_func(fn_name)

        hlog.info('开始关闭腾讯云ECS实例“%s”' % instance_id)

        try:
            stop_instances_req = models.StopInstancesRequest()
            stop_instances_params = {
                "InstanceIds": [instance_id],
                "StopType": platform_config.stop_type,
                "StoppedMode": platform_config.stopped_mode
            }
            hlog.var('stop_instances_params', stop_instances_params)
            stop_instances_req.from_json_string(json.dumps(stop_instances_params))

            stop_instances_resp = ecs_client.StopInstances(stop_instances_req)
            hlog.var('stop_instances_resp', stop_instances_resp)

        except TencentCloudSDKException as err:
            hlog.error('腾讯云ECS实例“%s”：关闭失败' % instance_id)
            hlog.error(err)
            exit(1)

        hlog.info('腾讯云ECS实例“%s”：关闭成功' % instance_id)

        hlog.exit_func(fn_name)

    def restart(self, instance_id):
        """
       只有状态为RUNNING的实例才可以进行此操作。
       文档： https://cloud.tencent.com/document/api/213/15742
       """
        fn_name = '腾讯云平台'
        hlog.enter_func(fn_name)

        hlog.info('开始重启腾讯云ECS实例“%s”' % instance_id)

        try:
            reboot_instances_req = models.RebootInstancesRequest()
            reboot_instances_params = {
                "InstanceIds": [instance_id],
                "StopType": platform_config.stop_type
            }
            hlog.var('reboot_instances_params', reboot_instances_params)
            reboot_instances_req.from_json_string(json.dumps(reboot_instances_params))

            reboot_instances_resp = ecs_client.RebootInstances(reboot_instances_req)
            hlog.var('reboot_instances_resp', reboot_instances_resp)

        except TencentCloudSDKException as err:
            hlog.error('腾讯云ECS实例“%s”：重启失败' % instance_id)
            hlog.error(err)
            exit(1)

        hlog.info('腾讯云ECS实例“%s”：重启成功' % instance_id)

        hlog.exit_func(fn_name)


class al(Father):
    def get_client(self) -> Ecs20140526Client:
        cred = open_api_models.Config(
            access_key_id=config.access_key_id,
            access_key_secret=config.access_key_secret
        )
        cred.endpoint = 'ecs.%s.aliyuncs.com' % config.region_id

        return Ecs20140526Client(cred)

    def create(self, arg):
        fn_name = '阿里云平台'
        hlog.enter_func(fn_name)

        if os.path.exists(ECS_INFO_FILE):
            hlog.info('在%s文件中发现已经创建过阿里云ECS实例，请删除实例后再试' % ECS_INFO_FILENAME)
            exit(1)

        try:
            hlog.info('开始创建带 DryRun 测试运行标记的阿里云ECS实例' if arg.dry_run else '开始创建阿里云ECS实例')

            create_instance_req = ecs_20140526_models.CreateInstanceRequest(
                dry_run=args.dry_run,
                region_id=config.region_id,
                image_id=config.image_id,
                instance_type=config.instance_type,
                security_group_id=config.security_group_id,
                instance_name=config.instance_name,
                internet_charge_type=config.internet_charge_type,
                auto_renew=config.auto_renew,
                internet_max_bandwidth_in=platform_config.internet_max_bandwidth_in,
                internet_max_bandwidth_out=config.internet_max_bandwidth_out,
                host_name=config.host_name,
                zone_id=config.zone_id,
                system_disk=ecs_20140526_models.CreateInstanceRequestSystemDisk(
                    size=config.system_disk_size,
                    category=config.system_disk_type
                ),
                v_switch_id=config.vswitch_id,
                io_optimized=platform_config.io_optimized,
                instance_charge_type=config.instance_charge_type,
                key_pair_name=config.key_pair_name,
                security_enhancement_strategy=platform_config.security_enhancement_strategy,
            )
            hlog.var('create_instance_req', create_instance_req)
            hlog.debug('create_instance_req：%s' % create_instance_req)

            create_instance_resp = ecs_client.create_instance_with_options(create_instance_req, runtime)
            hlog.var('create_instance_resp', create_instance_resp)
            hlog.debug('create_instance_resp：%s' % create_instance_resp)

            instance_id = create_instance_resp.body.instance_id
            hlog.info('阿里云ECS实例“%s”：创建成功' % instance_id)

            is_created = False

            hlog.info('阿里云ECS实例“%s”：查看状态' % instance_id)

            while True:
                try:
                    describe_instance_status_req = ecs_20140526_models.DescribeInstanceStatusRequest(
                        region_id=config.region_id,
                        instance_id=[
                            instance_id
                        ],
                        zone_id=config.zone_id
                    )
                    hlog.var('describe_instance_status_req', describe_instance_status_req)

                    describe_instance_status_resp = ecs_client.describe_instance_status_with_options(
                        describe_instance_status_req, runtime)
                    hlog.var('describe_instance_status_resp', describe_instance_status_resp)
                    hlog.debug('describe_instance_status_resp：%s' % describe_instance_status_resp)

                    instance_status = describe_instance_status_resp.body.instance_statuses.instance_status[0]
                    hlog.var('instance_status', instance_status)
                    hlog.debug('instance_status：%s' % instance_status)

                    hlog.info('等待 “Stopped”状态。当前状态：%s' % instance_status.status)

                    if instance_status.instance_id == instance_id and instance_status.status == 'Stopped':
                        is_created = True

                    if is_created:
                        break

                except Exception as error:
                    hlog.error(error.message)

                sleep(5)

            hlog.info('阿里云ECS实例“%s”：添加公网IP' % instance_id)

            allocate_public_ip_address_req = ecs_20140526_models.AllocatePublicIpAddressRequest(instance_id=instance_id)
            hlog.var('allocate_public_ip_address_req', allocate_public_ip_address_req)
            hlog.debug('allocate_public_ip_address_req：%s' % allocate_public_ip_address_req)

            allocate_public_ip_address_resp = ecs_client.allocate_public_ip_address_with_options(
                allocate_public_ip_address_req, runtime)
            hlog.var('allocate_public_ip_address_resp', allocate_public_ip_address_resp)
            hlog.debug('allocate_public_ip_address_resp：%s' % allocate_public_ip_address_resp)

            ip = allocate_public_ip_address_resp.body.ip_address

            hlog.info('阿里云ECS实例“%s”：公网IP添加成功' % instance_id)

            hlog.info('阿里云ECS实例“%s”：启动实例' % instance_id)

            start_instances_req = ecs_20140526_models.StartInstanceRequest(instance_id=instance_id)
            hlog.var('start_instances_req', start_instances_req)
            hlog.debug('start_instances_req：%s' % start_instances_req)

            start_instances_resp = ecs_client.start_instance_with_options(start_instances_req, runtime)
            hlog.var('start_instances_resp', start_instances_resp)
            hlog.debug('start_instances_resp：%s' % start_instances_resp)

            hlog.info('阿里云ECS实例“%s”：启动实例成功' % instance_id)

            EcsInfoManager.save(instance_id, ip, config.default_ss_server_port)
            hlog.info('阿里云ECS实例“%s”：信息已保存 “%s”' % (instance_id, ECS_INFO_FILE))

            hlog.info('阿里云ECS实例“%s”：PING测试...' % instance_id)
            while True:
                result = get_exit_code_of_cmd('ping -W 1 -c 10 %s' % ip, is_show_error=False)

                if result == 0:
                    hlog.info('阿里云ECS实例“%s”：PING测试成功' % instance_id)
                    break
                else:
                    hlog.info('阿里云ECS实例“%s”：PING测试失败，5秒后重试' % instance_id)
                    sleep(5)

            upload_sh(ip)

        except Exception as error:
            if str(error).find('DryRun') != -1:
                hlog.info('带 DryRun 测试运行标记的阿里云ECS实例创建成功')
            else:
                hlog.error('创建阿里云ECS实例失败')
                hlog.error(error.message)
                exit(1)

        hlog.exit_func(fn_name)

    def delete(self, instance_id):
        fn_name = '阿里云平台'
        hlog.enter_func(fn_name)

        hlog.info('开始释放阿里云ECS实例“%s”' % instance_id)

        try:
            delete_instance_req = ecs_20140526_models.DeleteInstanceRequest(instance_id=instance_id)
            hlog.var('delete_instance_req', delete_instance_req)
            hlog.debug('delete_instance_req：%s' % delete_instance_req)

            delete_instance_resp = ecs_client.delete_instance_with_options(delete_instance_req, runtime)
            hlog.var('delete_instance_resp', delete_instance_resp)
            hlog.debug('delete_instance_resp：%s' % delete_instance_resp)

            if os.path.exists(ECS_INFO_FILE):
                os.unlink(ECS_INFO_FILE)

        except Exception as error:
            hlog.error('阿里云ECS实例“%s”：释放失败' % instance_id)
            hlog.error(error.message)
            exit(1)

        hlog.info('阿里云ECS实例“%s”：释放成功' % instance_id)

        hlog.exit_func(fn_name)

    def start(self, instance_id):
        fn_name = '阿里云平台'
        hlog.enter_func(fn_name)

        hlog.info('开始启动阿里云ECS实例“%s”' % instance_id)

        try:
            start_instance_req = ecs_20140526_models.StartInstanceRequest(instance_id=instance_id)
            hlog.var('start_instance_req', start_instance_req)
            hlog.debug('start_instance_req：%s' % start_instance_req)

            start_instance_resp = ecs_client.start_instance_with_options(start_instance_req, runtime)
            hlog.var('start_instance_resp', start_instance_resp)
            hlog.debug('start_instance_resp：%s' % start_instance_resp)

        except Exception as error:
            hlog.error('阿里云ECS实例“%s”：启动失败' % instance_id)
            hlog.error(error.message)
            exit(1)

        hlog.info('阿里云ECS实例“%s”：启动成功' % instance_id)

        hlog.exit_func(fn_name)

    def stop(self, instance_id):
        fn_name = '阿里云平台'
        hlog.enter_func(fn_name)

        hlog.info('开始关闭阿里云ECS实例“%s”' % instance_id)

        try:
            stop_instance_req = ecs_20140526_models.StopInstanceRequest(instance_id=instance_id)
            hlog.var('stop_instance_req', stop_instance_req)
            hlog.debug('stop_instance_req：%s' % stop_instance_req)

            stop_instance_resp = ecs_client.stop_instance_with_options(stop_instance_req, runtime)
            hlog.var('stop_instance_resp', stop_instance_resp)
            hlog.debug('stop_instance_resp：%s' % stop_instance_resp)

        except Exception as error:
            hlog.error('阿里云ECS实例“%s”：关闭失败' % instance_id)
            hlog.error(error.message)
            exit(1)

        hlog.info('阿里云ECS实例“%s”：关闭成功' % instance_id)

        hlog.exit_func(fn_name)

    def restart(self, instance_id):
        fn_name = '阿里云平台'
        hlog.enter_func(fn_name)

        hlog.info('开始重启阿里云ECS实例“%s”' % instance_id)

        try:
            reboot_instance_req = ecs_20140526_models.RebootInstanceRequest(instance_id=instance_id)
            hlog.var('reboot_instance_req', reboot_instance_req)
            hlog.debug('reboot_instance_req：%s' % reboot_instance_req)

            reboot_instance_resp = ecs_client.reboot_instance_with_options(reboot_instance_req, runtime)
            hlog.var('reboot_instance_resp', reboot_instance_resp)
            hlog.debug('reboot_instance_resp：%s' % reboot_instance_resp)

        except Exception as error:
            hlog.error('阿里云ECS实例“%s”：重启失败' % instance_id)
            hlog.error(error.message)
            exit(1)

        hlog.info('阿里云ECS实例“%s”：重启成功' % instance_id)

        hlog.exit_func(fn_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='ecstools',
                                     description='ECS管理工具',
                                     usage='%(prog)s -nrdlctsv')
    parser.add_argument('-n',
                        '--dry-run',
                        help='模拟创建ECS运行，测试配置参数',
                        required=False,
                        action='store_true',
                        dest='dry_run')
    group = parser.add_mutually_exclusive_group()

    parser.add_argument('-p',
                        '--platform',
                        type=str,
                        choices=['al', 'hw', 'tx'],
                        required=True,
                        help='只能选择三个指定的值')

    group.add_argument('-r',
                       '--run',
                       help='创建并运行ECS实例',
                       action='store_true',
                       dest='run')

    group.add_argument('-d',
                       '--delete',
                       help='删除指定的实例',
                       action='store',
                       type=str,
                       dest='delete_id')

    parser.add_argument('-v',
                        '--version',
                        help='显示版本信息',
                        action='version',
                        version='%(prog)s v1.0.0')

    parser.add_argument('-s',
                        '--signal',
                        dest='signal',
                        nargs='+',
                        help='向ECS发送信号： start, stop, restart')

    group = parser.add_mutually_exclusive_group()

    args = parser.parse_args()

    class_name = args.platform

    hlog.info('开始配置%sECS' % switch_case(class_name))

    specific_env_var = os.getenv('ECS_TOOLS_CONF_PATH')
    if specific_env_var is None:
        hlog.info('未检测到“ECS_TOOLS_CONF_PATH“环境变量,从默认路径“%s”中查找配置文件' % CONFIG_DIR)
        specific_env_var = CONFIG_DIR
    else:
        hlog.info('从环境变量“%s”中查询配置文件' % specific_env_var)

    file_names = os.listdir(specific_env_var)

    config_path = ''

    for file_name in file_names:
        if file_name.__contains__('%s.ini' % class_name):
            config_path = str(CONFIG_DIR / 'common.%s.ini') % class_name
            hlog.info('%s配置文件 “%s” 加载成功' % (switch_case(class_name), config_path))

    if config_path == '' and file_names.__contains__('common.ini'):
        config_path = str(CONFIG_DIR / 'common.ini')
        hlog.info('配置文件 “%s” 加载成功' % config_path)

    if config_path == '':
        hlog.error('配置文件未找到，请检查路径下是否存在正确的文件')
        exit()

    config = Config()
    platform_config = PlatformConfig(class_name)

    HappyConfigParser.load(config_path, config)
    HappyConfigParser.load(config_path, platform_config)

    if class_name in globals():
        selected_class = globals()[class_name]()
    else:
        exit()

    ecs_client = selected_class.get_client()

    if args.run:
        selected_class.create(args)
    elif args.delete_id:
        selected_class.delete(args.delete_id)
    elif args.signal:
        signal_name = args.signal[0]
        ecs_id = args.signal[1]

        if signal_name == 'start':
            selected_class.start(ecs_id)
        elif signal_name == 'stop':
            selected_class.stop(ecs_id)
        elif signal_name == 'restart':
            selected_class.restart(ecs_id)
