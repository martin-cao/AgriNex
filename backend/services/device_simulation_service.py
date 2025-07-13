"""
设备模拟管理服务
负责管理动态设备模拟，通过MQTT命令控制sensor-simulator
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from services.mqtt_service import mqtt_service
from models.device import Device
from models.sensor import Sensor
from extensions import db

logger = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    """模拟配置"""
    device_id: str
    device_type: str
    location: str
    interval: int = 30
    sensor_types: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.sensor_types is None:
            # 根据设备类型设置默认传感器
            if self.device_type == 'soil_monitor':
                self.sensor_types = ['temperature', 'humidity', 'ph']
            elif self.device_type == 'weather_station':
                self.sensor_types = ['temperature', 'humidity', 'light_intensity', 'wind_speed']
            elif self.device_type == 'irrigation_controller':
                self.sensor_types = ['flow_rate', 'pressure', 'valve_status']
            else:
                self.sensor_types = ['temperature', 'humidity']


class DeviceSimulationService:
    """设备模拟管理服务"""
    
    def __init__(self):
        self.active_simulations: Dict[str, SimulationConfig] = {}
        self.command_topic = "simulation/control"
        self.status_topic = "simulation/status"
        
    def get_active_simulations(self) -> List[Dict[str, Any]]:
        """获取活跃的模拟设备列表"""
        result = []
        for device_id, config in self.active_simulations.items():
            result.append({
                'device_id': device_id,
                'device_type': config.device_type,
                'location': config.location,
                'interval': config.interval,
                'sensor_types': config.sensor_types,
                'status': 'active'
            })
        return result
    
    def start_device_simulation(self, config: SimulationConfig) -> bool:
        """启动设备模拟（同步版本）"""
        try:
            # 检查设备是否已在模拟中
            if config.device_id in self.active_simulations:
                logger.warning("设备 %s 已在模拟中", config.device_id)
                return False
            
            # 在数据库中创建设备和传感器记录
            device = self._create_device_in_db(config)
            if not device:
                logger.error("创建设备记录失败: %s", config.device_id)
                return False
            
            # 发送启动命令到sensor-simulator
            command = {
                'action': 'start_device',
                'device_id': config.device_id,
                'config': {
                    'device_type': config.device_type,
                    'location': config.location,
                    'interval': config.interval,
                    'sensor_types': config.sensor_types
                },
                'timestamp': datetime.now().isoformat()
            }
            
            success = self._send_mqtt_command_sync(command)
            if success:
                self.active_simulations[config.device_id] = config
                logger.info("设备模拟启动成功: %s", config.device_id)
                return True
            else:
                # 如果MQTT命令发送失败，清理数据库记录
                self._cleanup_device_in_db(config.device_id)
                logger.error("设备模拟启动失败: %s", config.device_id)
                return False
                
        except Exception as e:
            logger.error("启动设备模拟时发生错误: %s", e)
            return False
    
    def stop_device_simulation(self, device_id: str) -> bool:
        """停止设备模拟（同步版本）"""
        try:
            if device_id not in self.active_simulations:
                logger.warning("设备 %s 不在模拟中", device_id)
                return False
            
            # 发送停止命令到sensor-simulator
            command = {
                'action': 'stop_device',
                'device_id': device_id,
                'timestamp': datetime.now().isoformat()
            }
            
            success = self._send_mqtt_command_sync(command)
            if success:
                # 从活跃列表中移除
                del self.active_simulations[device_id]
                
                # 标记设备为非活跃状态（不删除历史数据）
                self._deactivate_device_in_db(device_id)
                
                logger.info("设备模拟停止成功: %s", device_id)
                return True
            else:
                logger.error("设备模拟停止失败: %s", device_id)
                return False
                
        except Exception as e:
            logger.error("停止设备模拟时发生错误: %s", e)
            return False
    
    def restart_device_simulation(self, device_id: str) -> bool:
        """重启设备模拟（同步版本）"""
        if device_id not in self.active_simulations:
            return False
        
        config = self.active_simulations[device_id]
        
        # 先停止，再启动
        stop_success = self.stop_device_simulation(device_id)
        if stop_success:
            return self.start_device_simulation(config)
        return False
    
    def update_device_config(self, device_id: str, new_config: Dict[str, Any]) -> bool:
        """更新设备配置（同步版本）"""
        try:
            if device_id not in self.active_simulations:
                logger.warning("设备 %s 不在模拟中", device_id)
                return False
            
            # 更新配置
            config = self.active_simulations[device_id]
            if 'interval' in new_config:
                config.interval = new_config['interval']
            if 'location' in new_config:
                config.location = new_config['location']
            
            # 发送更新配置命令
            command = {
                'action': 'update_config',
                'device_id': device_id,
                'config': new_config,
                'timestamp': datetime.now().isoformat()
            }
            
            success = self._send_mqtt_command_sync(command)
            if success:
                logger.info("设备配置更新成功: %s", device_id)
                return True
            else:
                logger.error("设备配置更新失败: %s", device_id)
                return False
                
        except Exception as e:
            logger.error("更新设备配置时发生错误: %s", e)
            return False
    
    def _create_device_in_db(self, config: SimulationConfig) -> Optional[Device]:
        """在数据库中创建设备和传感器记录"""
        try:
            # 创建设备记录
            device = Device.create(
                name=f"Simulated {config.device_type}",
                location=config.location,
                device_type=config.device_type,
                status='active'
            )
            db.session.flush()  # 获取device.id
            
            # 创建传感器记录
            sensor_types = config.sensor_types or []
            for sensor_type in sensor_types:
                sensor = Sensor.create(
                    device_id=device.id,
                    sensor_type=sensor_type,
                    name=f"{sensor_type.replace('_', ' ').title()} Sensor",
                    unit=self._get_sensor_unit(sensor_type),
                    status='active'
                )
            
            db.session.commit()
            logger.info(f"设备数据库记录创建成功: {config.device_id}")
            return device
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建设备数据库记录失败: {e}")
            return None
    
    def _cleanup_device_in_db(self, device_id: str):
        """清理数据库中的设备记录"""
        try:
            device = Device.query.filter_by(device_id=device_id).first()
            if device:
                # 删除相关传感器
                Sensor.query.filter_by(device_id=device.id).delete()
                # 删除设备
                db.session.delete(device)
                db.session.commit()
                logger.info(f"设备数据库记录清理成功: {device_id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"清理设备数据库记录失败: {e}")
    
    def _deactivate_device_in_db(self, device_id: str):
        """在数据库中停用设备"""
        try:
            device = Device.query.filter_by(device_id=device_id).first()
            if device:
                device.is_active = False
                
                # 停用相关传感器
                sensors = Sensor.query.filter_by(device_id=device.id).all()
                for sensor in sensors:
                    sensor.is_active = False
                
                db.session.commit()
                logger.info(f"设备已停用: {device_id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"停用设备失败: {e}")
    
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
            'valve_status': 'status'
        }
        return unit_map.get(sensor_type, 'unit')
    
    async def _send_mqtt_command(self, command: Dict[str, Any]) -> bool:
        """发送MQTT命令到sensor-simulator（异步版本）"""
        try:
            if not mqtt_service.is_connected:
                logger.error("MQTT未连接，无法发送命令")
                return False
            
            result = mqtt_service.publish(self.command_topic, command, qos=1)
            
            if result:
                logger.debug("MQTT命令发送成功: %s", command['action'])
                return True
            else:
                logger.error("MQTT命令发送失败")
                return False
                
        except Exception as e:
            logger.error("发送MQTT命令时发生错误: %s", e)
            return False
    
    def _send_mqtt_command_sync(self, command: Dict[str, Any]) -> bool:
        """发送MQTT命令到sensor-simulator（同步版本）"""
        try:
            if not mqtt_service.is_connected:
                logger.error("MQTT未连接，无法发送命令")
                return False
            
            result = mqtt_service.publish(self.command_topic, command, qos=1)
            
            if result:
                logger.debug("MQTT命令发送成功: %s", command['action'])
                return True
            else:
                logger.error("MQTT命令发送失败")
                return False
                
        except Exception as e:
            logger.error("发送MQTT命令时发生错误: %s", e)
            return False


# 全局服务实例
device_simulation_service = DeviceSimulationService()
