# backend/services/device_validation_service.py
"""
设备验证服务 - 处理手动添加设备的验证逻辑
"""
import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any, Tuple
import requests
from datetime import datetime

from services.mqtt_service import mqtt_service

logger = logging.getLogger(__name__)


class MQTTDataListener:
    """MQTT数据监听器 - 等待指定设备的数据"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.received_data = None
        self.waiting = False
        self.handler_registered = False
        
    async def wait_for_data(self, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """等待指定设备的MQTT数据"""
        logger.info(f"开始监听设备 {self.device_id} 的MQTT数据，超时: {timeout}秒")
        
        self.waiting = True
        self.received_data = None
        
        # 注册临时消息处理器
        topic = f"sensors/{self.device_id}/numeric"
        mqtt_service.register_message_handler(topic, self._on_data_received)
        self.handler_registered = True
        
        try:
            # 异步等待数据
            start_time = time.time()
            while self.waiting and (time.time() - start_time) < timeout:
                await asyncio.sleep(0.5)
                if self.received_data:
                    logger.info(f"收到设备 {self.device_id} 的数据")
                    break
            
            if not self.received_data:
                logger.warning(f"设备 {self.device_id} 在 {timeout} 秒内未发送数据")
            
            return self.received_data
            
        finally:
            # 清理资源
            self._cleanup()
    
    def _on_data_received(self, topic: str, payload: Dict[str, Any]):
        """接收到数据的回调"""
        logger.info(f"MQTT监听器收到数据: topic={topic}, payload={payload}")
        self.received_data = payload
        self.waiting = False
    
    def _cleanup(self):
        """清理资源"""
        if self.handler_registered:
            topic = f"sensors/{self.device_id}/numeric"
            mqtt_service.unregister_message_handler(topic)
            self.handler_registered = False


class DeviceValidationService:
    """设备验证服务"""
    
    @staticmethod
    def check_device_health(address: str, timeout: int = 5) -> Tuple[bool, str]:
        """检查设备HTTP接口健康状态"""
        try:
            # 尝试连接设备的健康检查接口
            url = f"http://{address}/health"
            logger.info(f"检查设备健康状态: {url}")
            
            response = requests.get(url, timeout=timeout)
            
            if response.status_code == 200:
                logger.info(f"设备 {address} HTTP健康检查通过")
                return True, "设备HTTP接口正常"
            else:
                logger.warning(f"设备 {address} HTTP返回状态码: {response.status_code}")
                return False, f"设备HTTP返回状态码: {response.status_code}"
                
        except requests.exceptions.Timeout:
            logger.error(f"设备 {address} HTTP连接超时")
            return False, "设备连接超时"
        except requests.exceptions.ConnectionError:
            logger.error(f"设备 {address} HTTP连接被拒绝")
            return False, "无法连接到设备"
        except Exception as e:
            logger.error(f"设备 {address} HTTP检查异常: {e}")
            return False, f"连接异常: {str(e)}"
    
    @staticmethod
    def validate_data_format(data: Dict[str, Any]) -> Tuple[bool, str]:
        """验证接收到的数据格式"""
        try:
            # 检查必需的字段
            required_fields = ['sensor_id', 'timestamp', 'data_type']
            
            for field in required_fields:
                if field not in data:
                    return False, f"缺少必需字段: {field}"
            
            # 检查数据类型
            if data['data_type'] == 'numeric':
                if 'value' not in data:
                    return False, "数值型数据缺少value字段"
                
                # 验证数值
                try:
                    float(data['value'])
                except (ValueError, TypeError):
                    return False, "value字段不是有效数值"
            
            # 检查时间戳格式
            try:
                if isinstance(data['timestamp'], str):
                    datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                elif isinstance(data['timestamp'], (int, float)):
                    datetime.fromtimestamp(data['timestamp'])
            except Exception:
                return False, "时间戳格式无效"
            
            logger.info("数据格式验证通过")
            return True, "数据格式正确"
            
        except Exception as e:
            logger.error(f"数据格式验证异常: {e}")
            return False, f"验证异常: {str(e)}"
    
    @staticmethod
    async def validate_device(device_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """完整的设备验证流程"""
        device_id = device_data.get('device_id')
        address = device_data.get('address')
        
        # 参数验证
        if not device_id:
            return False, "设备ID不能为空", None
        if not address:
            return False, "设备地址不能为空", None
        
        logger.info(f"开始验证设备: {device_id} @ {address}")
        
        # 阶段1: HTTP健康检查
        http_ok, http_msg = DeviceValidationService.check_device_health(address)
        if not http_ok:
            return False, f"HTTP检查失败: {http_msg}", None
        
        # 阶段2: MQTT数据监听
        mqtt_listener = MQTTDataListener(device_id)
        mqtt_data = await mqtt_listener.wait_for_data(timeout=30)
        
        if not mqtt_data:
            return False, "未收到设备MQTT数据，请检查设备配置和网络连接", None
        
        # 阶段3: 数据格式验证
        format_ok, format_msg = DeviceValidationService.validate_data_format(mqtt_data)
        if not format_ok:
            return False, f"数据格式验证失败: {format_msg}", mqtt_data
        
        logger.info(f"设备 {device_id} 验证成功")
        return True, "设备验证成功", mqtt_data


# 全局服务实例
device_validation_service = DeviceValidationService()
