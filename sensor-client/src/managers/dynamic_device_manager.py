"""
动态设备管理器
负责管理多个虚拟设备的创建、删除和控制
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.core.config import Config
from src.adapters.mqtt_adapter import MQTTAdapter


@dataclass
class VirtualDevice:
    """虚拟设备配置"""
    device_id: str
    device_type: str
    location: str
    sensor_types: List[str]
    interval: int
    task: Optional[asyncio.Task] = None
    created_at: Optional[datetime] = None
    is_active: bool = False


class DynamicDeviceManager:
    """动态设备管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.devices: Dict[str, VirtualDevice] = {}
        self.mqtt_adapter = MQTTAdapter(config)
        self.running = False
        
        # MQTT主题
        self.command_topic = "simulation/control"
        self.status_topic = "simulation/status"
        
    async def start(self):
        """启动设备管理器"""
        try:
            self.logger.info("启动动态设备管理器")
            self.running = True
            
            # 连接MQTT
            await self.mqtt_adapter.connect()
            
            # 订阅控制命令主题（通过回调方式）
            self.mqtt_adapter.add_message_callback(self._handle_mqtt_message)
            # 手动订阅主题
            self.mqtt_adapter.client.subscribe(self.command_topic, 1)
            
            # 启动默认设备（如果配置了）
            await self._start_default_devices()
            
            # 发送初始状态
            await self._send_status()
            
            self.logger.info("动态设备管理器启动成功")
            
        except Exception as e:
            self.logger.error(f"启动设备管理器失败: {e}")
            raise
    
    async def stop(self):
        """停止设备管理器"""
        try:
            self.logger.info("停止动态设备管理器")
            self.running = False
            
            # 停止所有设备
            for device_id in list(self.devices.keys()):
                await self.stop_device(device_id)
            
            # 断开MQTT连接
            self.mqtt_adapter.disconnect()
            
            self.logger.info("设备管理器已停止")
            
        except Exception as e:
            self.logger.error(f"停止设备管理器失败: {e}")
    
    async def _handle_mqtt_message(self, topic: str, payload: Dict[str, Any]):
        """处理MQTT消息"""
        if topic == self.command_topic:
            await self._handle_command(topic, payload)
    
    async def _publish_mqtt(self, topic: str, payload: Dict[str, Any]) -> bool:
        """发布MQTT消息"""
        try:
            if not self.mqtt_adapter.connected:
                self.logger.warning("MQTT未连接")
                return False
            
            import json
            result = self.mqtt_adapter.client.publish(
                topic, 
                json.dumps(payload, ensure_ascii=False), 
                qos=1
            )
            return result.rc == 0
        except Exception as e:
            self.logger.error(f"发布MQTT消息失败: {e}")
            return False
        """处理MQTT命令"""
        try:
            action = payload.get('action')
            device_id = payload.get('device_id')
            
            self.logger.info(f"收到命令: {action} for device {device_id}")
            
            if action == 'start_device':
                await self._start_device_from_command(payload)
            elif action == 'stop_device':
                await self.stop_device(device_id)
            elif action == 'update_config':
                await self._update_device_config(device_id, payload.get('config', {}))
            elif action == 'get_status':
                await self._send_status()
            else:
                self.logger.warning(f"未知命令: {action}")
                
        except Exception as e:
            self.logger.error(f"处理命令失败: {e}")
    
    async def _start_device_from_command(self, payload: Dict[str, Any]):
        """根据命令启动设备"""
        try:
            device_id = payload['device_id']
            config = payload.get('config', {})
            
            device = VirtualDevice(
                device_id=device_id,
                device_type=config.get('device_type', 'generic'),
                location=config.get('location', 'unknown'),
                sensor_types=config.get('sensor_types', ['temperature', 'humidity']),
                interval=config.get('interval', 30),
                created_at=datetime.now()
            )
            
            success = await self.start_device(device)
            
            # 发送响应
            response = {
                'action': 'device_started',
                'device_id': device_id,
                'success': success,
                'timestamp': datetime.now().isoformat()
            }
            await self.mqtt_adapter.publish(self.status_topic, response)
            
        except Exception as e:
            self.logger.error(f"启动设备失败: {e}")
    
    async def start_device(self, device: VirtualDevice) -> bool:
        """启动虚拟设备"""
        try:
            if device.device_id in self.devices:
                self.logger.warning(f"设备 {device.device_id} 已存在")
                return False
            
            # 创建设备模拟任务
            task = asyncio.create_task(self._simulate_device_data(device))
            device.task = task
            device.is_active = True
            
            # 添加到设备列表
            self.devices[device.device_id] = device
            
            self.logger.info(f"设备 {device.device_id} 启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动设备 {device.device_id} 失败: {e}")
            return False
    
    async def stop_device(self, device_id: str) -> bool:
        """停止虚拟设备"""
        try:
            if device_id not in self.devices:
                self.logger.warning(f"设备 {device_id} 不存在")
                return False
            
            device = self.devices[device_id]
            
            # 取消模拟任务
            if device.task and not device.task.done():
                device.task.cancel()
                try:
                    await device.task
                except asyncio.CancelledError:
                    pass
            
            device.is_active = False
            
            # 从设备列表中移除
            del self.devices[device_id]
            
            self.logger.info(f"设备 {device_id} 停止成功")
            
            # 发送响应
            response = {
                'action': 'device_stopped',
                'device_id': device_id,
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
            await self.mqtt_adapter.publish(self.status_topic, response)
            
            return True
            
        except Exception as e:
            self.logger.error(f"停止设备 {device_id} 失败: {e}")
            return False
    
    async def _update_device_config(self, device_id: str, new_config: Dict[str, Any]):
        """更新设备配置"""
        try:
            if device_id not in self.devices:
                self.logger.warning(f"设备 {device_id} 不存在")
                return
            
            device = self.devices[device_id]
            
            # 更新配置
            if 'interval' in new_config:
                device.interval = new_config['interval']
            if 'location' in new_config:
                device.location = new_config['location']
            
            self.logger.info(f"设备 {device_id} 配置已更新")
            
            # 发送响应
            response = {
                'action': 'config_updated',
                'device_id': device_id,
                'success': True,
                'new_config': new_config,
                'timestamp': datetime.now().isoformat()
            }
            await self.mqtt_adapter.publish(self.status_topic, response)
            
        except Exception as e:
            self.logger.error(f"更新设备 {device_id} 配置失败: {e}")
    
    async def _simulate_device_data(self, device: VirtualDevice):
        """模拟设备数据"""
        try:
            self.logger.info(f"开始模拟设备 {device.device_id} 数据")
            
            while device.is_active and self.running:
                # 为每个传感器类型生成数据
                for sensor_type in device.sensor_types:
                    sensor_data = self._generate_sensor_data(device, sensor_type)
                    
                    # 发送到MQTT
                    topic = f"sensors/{device.device_id}/{sensor_type}"
                    await self.mqtt_adapter.publish(topic, sensor_data)
                
                # 等待下一次发送
                await asyncio.sleep(device.interval)
                
        except asyncio.CancelledError:
            self.logger.info(f"设备 {device.device_id} 模拟任务已取消")
        except Exception as e:
            self.logger.error(f"设备 {device.device_id} 模拟失败: {e}")
    
    def _generate_sensor_data(self, device: VirtualDevice, sensor_type: str) -> Dict[str, Any]:
        """生成传感器数据"""
        import random
        import time
        
        # 根据传感器类型生成不同的数据
        data_generators = {
            'temperature': lambda: round(random.uniform(15.0, 35.0), 2),
            'humidity': lambda: round(random.uniform(30.0, 80.0), 2),
            'ph': lambda: round(random.uniform(6.0, 8.0), 2),
            'light_intensity': lambda: round(random.uniform(1000, 50000), 2),
            'wind_speed': lambda: round(random.uniform(0, 10.0), 2),
            'flow_rate': lambda: round(random.uniform(0, 50.0), 2),
            'pressure': lambda: round(random.uniform(100, 500), 2),
            'valve_status': lambda: random.choice([0, 1]),
            'co2_level': lambda: round(random.uniform(400, 1500), 2)
        }
        
        value = data_generators.get(sensor_type, lambda: random.uniform(0, 100))()
        
        return {
            'device_id': device.device_id,
            'sensor_type': sensor_type,
            'value': value,
            'unit': self._get_sensor_unit(sensor_type),
            'timestamp': datetime.now().isoformat(),
            'location': device.location,
            'device_type': device.device_type
        }
    
    def _get_sensor_unit(self, sensor_type: str) -> str:
        """获取传感器单位"""
        unit_map = {
            'temperature': '°C',
            'humidity': '%',
            'ph': 'pH',
            'light_intensity': 'lx',
            'wind_speed': 'm/s',
            'flow_rate': 'L/min',
            'pressure': 'kPa',
            'valve_status': 'status',
            'co2_level': 'ppm'
        }
        return unit_map.get(sensor_type, 'unit')
    
    async def _start_default_devices(self):
        """启动默认设备"""
        try:
            # 从环境变量获取默认设备数量
            import os
            device_count = int(os.getenv('DEVICE_COUNT', 3))
            
            for i in range(device_count):
                device_id = f"default_device_{i+1}"
                device = VirtualDevice(
                    device_id=device_id,
                    device_type='weather_station',
                    location=f'Field_{i+1}',
                    sensor_types=['temperature', 'humidity', 'light_intensity'],
                    interval=30,
                    created_at=datetime.now()
                )
                
                await self.start_device(device)
                
            self.logger.info(f"启动了 {device_count} 个默认设备")
            
        except Exception as e:
            self.logger.error(f"启动默认设备失败: {e}")
    
    async def _send_status(self):
        """发送状态信息"""
        try:
            devices_status = []
            for device_id, device in self.devices.items():
                devices_status.append({
                    'device_id': device_id,
                    'device_type': device.device_type,
                    'location': device.location,
                    'sensor_types': device.sensor_types,
                    'interval': device.interval,
                    'is_active': device.is_active,
                    'created_at': device.created_at.isoformat() if device.created_at else None
                })
            
            status = {
                'action': 'status_report',
                'timestamp': datetime.now().isoformat(),
                'total_devices': len(self.devices),
                'running': self.running,
                'devices': devices_status
            }
            
            await self.mqtt_adapter.publish(self.status_topic, status)
            
        except Exception as e:
            self.logger.error(f"发送状态失败: {e}")
    
    def get_device_list(self) -> List[Dict[str, Any]]:
        """获取设备列表"""
        devices = []
        for device_id, device in self.devices.items():
            devices.append({
                'device_id': device_id,
                'device_type': device.device_type,
                'location': device.location,
                'sensor_types': device.sensor_types,
                'interval': device.interval,
                'is_active': device.is_active,
                'created_at': device.created_at.isoformat() if device.created_at else None
            })
        return devices
