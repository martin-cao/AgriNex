# backend/services/ingestion_service.py
import json
import logging
import base64
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from models.reading import Reading
from models.sensor import Sensor
from models.device_template import DeviceTemplate
from extensions import db
from services.storage_service import StorageService

logger = logging.getLogger(__name__)


class IngestionService:
    """数据摄取服务 - 处理MQTT消息并存储到数据库"""
    
    def __init__(self):
        self.storage_service = StorageService()
    
    @staticmethod
    def ingest_reading(device_id, temperature, humidity, light, timestamp=None):
        """向后兼容的数值数据摄取方法"""
        reading = Reading(
            device_id=device_id,
            temperature=temperature,
            humidity=humidity,
            light=light,
            timestamp=timestamp
        )
        db.session.add(reading)
        db.session.commit()
        return reading
    
    def ingest_mqtt_message(self, topic: str, payload: Dict[str, Any]) -> Optional[Reading]:
        """处理MQTT消息并存储数据"""
        try:
            # 解析主题获取基本信息
            topic_info = self._parse_topic(topic)
            logger.info(f"解析主题: {topic} -> {topic_info}")
            if not topic_info:
                logger.error(f"无效的主题格式: {topic}")
                return None
            
            client_id = topic_info['client_id']
            data_type = topic_info['data_type']  # numeric, image, video
            
            # 从payload中获取具体的传感器类型
            sensor_type = payload.get('sensor_type')
            if not sensor_type:
                logger.error(f"payload中缺少sensor_type字段: {payload}")
                return None
            
            # 查找对应的设备
            from models.device import Device
            device = Device.query.filter_by(
                client_id=client_id,
                is_active=True
            ).first()
            
            if not device:
                logger.warning("未找到启用的设备: client_id=%s", client_id)
                return None
            
            # 查找对应的传感器
            sensor = Sensor.query.filter_by(
                device_id=device.id,
                type=sensor_type
            ).first()
            
            if not sensor:
                logger.warning("未找到传感器: device_id=%s, sensor_type=%s", device.id, sensor_type)
                return None
            
            # 根据数据类型处理
            if data_type == 'numeric':
                return self._process_single_sensor_data(sensor, payload)
            elif data_type == 'image':
                return self._process_image_data(sensor, payload)
            elif data_type == 'video':
                return self._process_video_data(sensor, payload)
            else:
                logger.error(f"不支持的数据类型: {data_type}")
                return None
                
        except Exception as e:
            logger.error(f"MQTT消息处理失败: {e}")
            return None
    
    def _parse_topic(self, topic: str) -> Optional[Dict[str, str]]:
        """解析MQTT主题"""
        try:
            # 主题格式: sensors/{client_id}/{data_type}
            parts = topic.split('/')
            if len(parts) >= 3 and parts[0] == 'sensors':
                return {
                    'client_id': parts[1],
                    'data_type': parts[2]
                }
            return None
        except Exception as e:
            logger.error(f"主题解析失败: {e}")
            return None
    
    def _get_or_create_sensor(self, sensor_info: Dict[str, str]) -> Optional[Sensor]:
        """获取或创建传感器 - 只为已注册的设备创建符合模板的传感器"""
        try:
            client_id = sensor_info['client_id']
            data_type = sensor_info['data_type']
            
            # 查找对应的设备（基于client_id）
            from models.device import Device
            device = Device.query.filter_by(
                client_id=client_id,
                is_active=True  # 只有启用的设备才能接收数据
            ).first()
            
            if not device:
                logger.warning("未找到启用的设备: client_id=%s", client_id)
                return None
            
            # 获取设备模板以验证传感器类型
            device_template = DeviceTemplate.get_by_device_type(device.type)
            if not device_template:
                logger.warning("设备类型 %s 没有对应的模板", device.type)
                return None
            
            # 验证传感器类型是否在设备模板中定义
            if not device_template.validate_sensor_type(data_type):
                allowed_types = [config['type'] for config in device_template.get_sensor_configs()]
                logger.warning("传感器类型 %s 不在设备 %s 的模板中，允许的类型: %s", 
                             data_type, device.type, allowed_types)
                return None
            
            # 尝试查找现有传感器
            sensor = Sensor.query.filter_by(
                device_id=device.id,
                type=data_type
            ).first()
            
            if not sensor:
                # 从设备模板获取传感器配置
                sensor_configs = device_template.get_sensor_configs()
                sensor_template = next((config for config in sensor_configs 
                                      if config['type'] == data_type), None)
                
                if sensor_template:
                    # 使用模板配置创建传感器
                    sensor = Sensor.create(
                        device_id=device.id,
                        sensor_type=data_type,
                        name=sensor_template['name'],
                        unit=sensor_template['unit'],
                        status="active"
                    )
                else:
                    # 使用默认配置创建传感器
                    sensor = Sensor.create(
                        device_id=device.id,
                        sensor_type=data_type,
                        name=f"{client_id}_{data_type}",
                        unit=self._get_unit_for_type(data_type),
                        status="active"
                    )
                
                db.session.add(sensor)
                db.session.commit()
                logger.info("为设备 %s 创建新传感器: %s", device.name, sensor.name)
            
            return sensor
            
        except Exception as e:
            import traceback
            logger.error("传感器获取/创建失败: %s", e)
            logger.error("完整错误信息: %s", traceback.format_exc())
            return None
    
    def _get_unit_for_type(self, data_type: str) -> str:
        """根据数据类型获取单位"""
        unit_map = {
            'numeric': 'mixed',
            'image': 'file',
            'video': 'file'
        }
        return unit_map.get(data_type, 'unknown')
    
    def _process_numeric_data(self, sensor: Sensor, payload: Dict[str, Any]) -> Optional[Reading]:
        """处理数值型数据"""
        try:
            # 处理直接发送的数值数据或包装在data字段中的数据
            data = payload.get('data', payload) if 'data' in payload else payload
            timestamp_str = payload.get('timestamp')
            
            # 解析时间戳
            timestamp = None
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()
            
            created_readings = []
            
            # 处理温度数据
            if 'temperature' in data:
                temp_reading = Reading.create_numeric(
                    sensor_id=sensor.id,
                    value=data['temperature'],
                    unit=data.get('temperature_unit', '°C'),
                    timestamp=timestamp,
                    metadata={
                        'client_id': payload.get('client_id'),
                        'data_type': 'temperature'
                    }
                )
                db.session.add(temp_reading)
                created_readings.append(temp_reading)
            
            # 处理湿度数据
            if 'humidity' in data:
                humidity_reading = Reading.create_numeric(
                    sensor_id=sensor.id,
                    value=data['humidity'],
                    unit=data.get('humidity_unit', '%'),
                    timestamp=timestamp,
                    metadata={
                        'client_id': payload.get('client_id'),
                        'data_type': 'humidity'
                    }
                )
                db.session.add(humidity_reading)
                created_readings.append(humidity_reading)
            
            # 处理光照数据
            if 'light' in data:
                light_reading = Reading.create_numeric(
                    sensor_id=sensor.id,
                    value=data['light'],
                    unit=data.get('light_unit', 'lux'),
                    timestamp=timestamp,
                    metadata={
                        'client_id': payload.get('client_id'),
                        'data_type': 'light'
                    }
                )
                db.session.add(light_reading)
                created_readings.append(light_reading)
            
            # 处理PH值数据
            if 'ph' in data:
                ph_reading = Reading.create_numeric(
                    sensor_id=sensor.id,
                    value=data['ph'],
                    unit=data.get('ph_unit', 'pH'),
                    timestamp=timestamp,
                    metadata={
                        'client_id': payload.get('client_id'),
                        'data_type': 'ph'
                    }
                )
                db.session.add(ph_reading)
                created_readings.append(ph_reading)
            
            # 处理土壤湿度数据
            if 'moisture' in data:
                moisture_reading = Reading.create_numeric(
                    sensor_id=sensor.id,
                    value=data['moisture'],
                    unit=data.get('moisture_unit', '%'),
                    timestamp=timestamp,
                    metadata={
                        'client_id': payload.get('client_id'),
                        'data_type': 'moisture'
                    }
                )
                db.session.add(moisture_reading)
                created_readings.append(moisture_reading)
            
            db.session.commit()
            logger.info(f"数值数据存储成功: 传感器ID={sensor.id}, 记录数={len(created_readings)}")
            
            # 返回第一个读数
            return created_readings[0] if created_readings else None
            
        except Exception as e:
            logger.error(f"数值数据处理失败: {e}")
            db.session.rollback()
            return None
    
    def _process_image_data(self, sensor: Sensor, payload: Dict[str, Any]) -> Optional[Reading]:
        """处理图像数据"""
        try:
            data = payload.get('data', {})
            timestamp_str = payload.get('timestamp')
            
            # 解析时间戳
            timestamp = None
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()
            
            # 解码base64数据
            image_data = base64.b64decode(data.get('data', ''))
            file_format = data.get('format', 'jpg')
            file_size = data.get('size', len(image_data))
            file_hash = data.get('hash', hashlib.md5(image_data).hexdigest())
            
            # 生成文件名
            filename = f"image_{sensor.id}_{int(timestamp.timestamp())}.{file_format}"
            
            # 存储文件
            storage_result = self.storage_service.store_file(
                filename=filename,
                file_data=image_data,
                content_type=f"image/{file_format}",
                metadata={
                    'sensor_id': sensor.id,
                    'timestamp': timestamp.isoformat(),
                    'hash': file_hash,
                    'client_id': payload.get('client_id')
                }
            )
            
            if not storage_result:
                logger.error("图像文件存储失败")
                return None
            
            # 创建读数记录
            reading = Reading.create_file(
                sensor_id=sensor.id,
                data_type='image',
                file_path=storage_result.get('local_path'),
                file_size=file_size,
                file_format=file_format,
                bucket_name=storage_result.get('bucket_name'),
                object_key=storage_result.get('object_key'),
                object_url=storage_result.get('object_url'),
                object_etag=storage_result.get('etag'),
                storage_backend=storage_result.get('backend', 'minio'),
                timestamp=timestamp,
                metadata={
                    'client_id': payload.get('client_id'),
                    'hash': file_hash,
                    'encoding': data.get('encoding', 'base64')
                }
            )
            
            db.session.add(reading)
            db.session.commit()
            
            logger.info(f"图像数据存储成功: 传感器ID={sensor.id}, 文件={filename}")
            return reading
            
        except Exception as e:
            logger.error(f"图像数据处理失败: {e}")
            db.session.rollback()
            return None
    
    def _process_video_data(self, sensor: Sensor, payload: Dict[str, Any]) -> Optional[Reading]:
        """处理视频数据"""
        try:
            data = payload.get('data', {})
            timestamp_str = payload.get('timestamp')
            
            # 解析时间戳
            timestamp = None
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()
            
            # 解码base64数据
            video_data = base64.b64decode(data.get('data', ''))
            file_format = data.get('format', 'mp4')
            file_size = data.get('size', len(video_data))
            file_hash = data.get('hash', hashlib.md5(video_data).hexdigest())
            
            # 生成文件名
            filename = f"video_{sensor.id}_{int(timestamp.timestamp())}.{file_format}"
            
            # 存储文件
            storage_result = self.storage_service.store_file(
                filename=filename,
                file_data=video_data,
                content_type=f"video/{file_format}",
                metadata={
                    'sensor_id': sensor.id,
                    'timestamp': timestamp.isoformat(),
                    'hash': file_hash,
                    'client_id': payload.get('client_id')
                }
            )
            
            if not storage_result:
                logger.error("视频文件存储失败")
                return None
            
            # 创建读数记录
            reading = Reading.create_file(
                sensor_id=sensor.id,
                data_type='video',
                file_path=storage_result.get('local_path'),
                file_size=file_size,
                file_format=file_format,
                bucket_name=storage_result.get('bucket_name'),
                object_key=storage_result.get('object_key'),
                object_url=storage_result.get('object_url'),
                object_etag=storage_result.get('etag'),
                storage_backend=storage_result.get('backend', 'minio'),
                timestamp=timestamp,
                metadata={
                    'client_id': payload.get('client_id'),
                    'hash': file_hash,
                    'encoding': data.get('encoding', 'base64')
                }
            )
            
            db.session.add(reading)
            db.session.commit()
            
            logger.info(f"视频数据存储成功: 传感器ID={sensor.id}, 文件={filename}")
            return reading
            
        except Exception as e:
            logger.error(f"视频数据处理失败: {e}")
            db.session.rollback()
            return None
    
    def _process_single_sensor_data(self, sensor: Sensor, payload: Dict[str, Any]) -> Optional[Reading]:
        """处理单个传感器的数值数据"""
        try:
            # 获取传感器值
            value = payload.get('value')
            if value is None:
                logger.error("payload中缺少value字段: %s", payload)
                return None
            
            # 获取单位
            unit = payload.get('unit', sensor.unit or '')
            
            # 解析时间戳
            timestamp_str = payload.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()
            
            # 创建读数记录
            reading = Reading.create_numeric(
                sensor_id=sensor.id,
                value=float(value),
                unit=unit,
                timestamp=timestamp,
                metadata={
                    'client_id': payload.get('client_id'),
                    'sensor_type': payload.get('sensor_type'),
                    'sensor_name': payload.get('sensor_name')
                }
            )
            
            db.session.add(reading)
            db.session.commit()
            
            logger.info("传感器数据存储成功: sensor_id=%s, value=%s%s", 
                       sensor.id, value, unit)
            return reading
            
        except Exception as e:
            logger.error("单传感器数据处理失败: %s", e)
            db.session.rollback()
            return None
    
    def ingest_aggregated_mqtt_message(self, topic: str, payload: Dict[str, Any]) -> List[Reading]:
        """处理包含多个传感器数据的MQTT消息"""
        readings = []
        try:
            # 解析主题获取基本信息
            topic_info = self._parse_topic(topic)
            logger.info(f"解析聚合数据主题: {topic} -> {topic_info}")
            if not topic_info:
                logger.error(f"无效的主题格式: {topic}")
                return readings
            
            client_id = topic_info['client_id']
            data_type = topic_info['data_type']  # 应该是 'numeric'
            
            # 查找对应的设备
            from models.device import Device
            device = Device.query.filter_by(
                client_id=client_id,
                is_active=True
            ).first()
            
            if not device:
                logger.warning("未找到启用的设备: client_id=%s", client_id)
                return readings
            
            # 定义传感器类型映射（从payload字段名到传感器类型）
            sensor_type_mapping = {
                'temperature': 'temperature',
                'humidity': 'humidity', 
                'light': 'light',
                'ph': 'soil_ph',
                'moisture': 'soil_moisture',
                'pressure': 'pressure',
                'wind_speed': 'wind_speed'
            }
            
            # 为每个传感器数据创建读数
            for field_name, value in payload.items():
                if field_name in sensor_type_mapping and isinstance(value, (int, float)):
                    sensor_type = sensor_type_mapping[field_name]
                    
                    # 查找对应的传感器
                    sensor = Sensor.query.filter_by(
                        device_id=device.id,
                        type=sensor_type
                    ).first()
                    
                    if sensor:
                        # 创建读数
                        reading_payload = {
                            'value': value,
                            'timestamp': payload.get('timestamp')
                        }
                        reading = self._process_single_sensor_data(sensor, reading_payload)
                        if reading:
                            readings.append(reading)
                            logger.info("创建传感器读数: %s = %s %s", sensor.name, value, sensor.unit)
                    else:
                        logger.warning("未找到传感器: device_id=%s, sensor_type=%s", device.id, sensor_type)
            
            if readings:
                db.session.commit()
                logger.info("聚合数据处理完成: %d 条读数", len(readings))
            
            return readings
                
        except Exception as e:
            db.session.rollback()
            import traceback
            logger.error("聚合MQTT消息处理失败: %s", str(e))
            logger.error("完整错误信息: %s", traceback.format_exc())
            return readings
    
    @staticmethod
    def get_latest_reading(device_id):
        """获取最新读数（向后兼容）"""
        return Reading.query.filter_by(device_id=device_id).order_by(Reading.timestamp.desc()).first()
    
    @staticmethod
    def get_latest_readings_by_type(sensor_id: int, data_type: str, limit: int = 10):
        """根据类型获取最新读数"""
        return Reading.query.filter_by(
            sensor_id=sensor_id,
            data_type=data_type
        ).order_by(Reading.timestamp.desc()).limit(limit).all()