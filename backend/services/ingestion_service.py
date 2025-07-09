# backend/services/ingestion_service.py
import json
import logging
import base64
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from models.reading import Reading
from models.sensor import Sensor
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
            # 解析主题获取传感器信息
            sensor_info = self._parse_topic(topic)
            if not sensor_info:
                logger.error(f"无效的主题格式: {topic}")
                return None
            
            # 获取或创建传感器
            sensor = self._get_or_create_sensor(sensor_info)
            if not sensor:
                logger.error(f"传感器创建失败: {sensor_info}")
                return None
            
            # 根据数据类型处理
            data_type = payload.get('type')
            if data_type == 'numeric':
                return self._process_numeric_data(sensor, payload)
            elif data_type == 'image':
                return self._process_image_data(sensor, payload)
            elif data_type == 'video':
                return self._process_video_data(sensor, payload)
            else:
                logger.error(f"未知的数据类型: {data_type}")
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
        """获取或创建传感器"""
        try:
            client_id = sensor_info['client_id']
            data_type = sensor_info['data_type']
            
            # 尝试查找现有传感器
            sensor = Sensor.query.filter_by(
                name=f"{client_id}_{data_type}"
            ).first()
            
            if not sensor:
                # 首先确保有默认设备
                from models.device import Device
                default_device = Device.query.filter_by(name="默认设备").first()
                if not default_device:
                    default_device = Device.create(
                        name="默认设备",
                        location="AgriNex系统",
                        device_type="sensor_station",
                        status="active"
                    )
                    db.session.add(default_device)
                    db.session.commit()
                    logger.info("创建默认设备")
                
                # 创建新传感器
                sensor = Sensor.create(
                    device_id=default_device.id,
                    sensor_type=data_type,
                    name=f"{client_id}_{data_type}",
                    unit=self._get_unit_for_type(data_type),
                    status="active"
                )
                db.session.add(sensor)
                db.session.commit()
                logger.info(f"创建新传感器: {sensor.name}")
            
            return sensor
            
        except Exception as e:
            logger.error(f"传感器获取/创建失败: {e}")
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