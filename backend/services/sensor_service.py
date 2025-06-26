# backend/services/sensor_service.py
from typing import List, Optional, Dict, Any
from backend.models.sensor import Sensor
from backend.models.reading import Reading
from backend.extensions import db
import logging

class SensorService:
    """传感器业务逻辑服务"""
    
    @staticmethod
    def get_sensor_by_id(sensor_id: int) -> Optional[Sensor]:
        """根据ID获取传感器"""
        return Sensor.query.get(sensor_id)
    
    @staticmethod
    def get_sensors_by_device(device_id: int) -> List[Sensor]:
        """获取设备下的所有传感器"""
        return Sensor.query.filter_by(device_id=device_id).all()
    
    @staticmethod
    def get_sensors_by_type(data_type: str, device_id: Optional[int] = None) -> List[Sensor]:
        """根据数据类型获取传感器"""
        query = Sensor.query.filter_by(data_type=data_type)
        if device_id:
            query = query.filter_by(device_id=device_id)
        return query.all()
    
    @staticmethod
    def get_active_sensors(device_id: Optional[int] = None) -> List[Sensor]:
        """获取活跃的传感器"""
        query = Sensor.query.filter_by(status='active')
        if device_id:
            query = query.filter_by(device_id=device_id)
        return query.all()
    
    @staticmethod
    def create_sensor(device_id: int, name: str, sensor_type: str, data_type: str, 
                     unit: Optional[str] = None, description: Optional[str] = None,
                     config: Optional[Dict[str, Any]] = None) -> Sensor:
        """创建新传感器"""
        try:
            sensor = Sensor(
                device_id=device_id,
                name=name,
                sensor_type=sensor_type,
                data_type=data_type,
                unit=unit,
                description=description,
                config=config or {},
                status='active'
            )
            db.session.add(sensor)
            db.session.commit()
            logging.info(f"Created sensor {sensor.id} for device {device_id}")
            return sensor
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to create sensor: {e}")
            raise
    
    @staticmethod
    def update_sensor(sensor_id: int, **kwargs) -> Optional[Sensor]:
        """更新传感器信息"""
        try:
            sensor = Sensor.query.get(sensor_id)
            if not sensor:
                return None
            
            for key, value in kwargs.items():
                if hasattr(sensor, key):
                    setattr(sensor, key, value)
            
            db.session.commit()
            logging.info(f"Updated sensor {sensor_id}")
            return sensor
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to update sensor {sensor_id}: {e}")
            raise
    
    @staticmethod
    def delete_sensor(sensor_id: int) -> bool:
        """删除传感器（软删除）"""
        try:
            sensor = Sensor.query.get(sensor_id)
            if not sensor:
                return False
            
            sensor.status = 'deleted'
            db.session.commit()
            logging.info(f"Deleted sensor {sensor_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to delete sensor {sensor_id}: {e}")
            raise
    
    @staticmethod
    def get_sensor_statistics(sensor_id: int, limit: int = 100) -> Dict[str, Any]:
        """获取传感器统计信息"""
        try:
            sensor = Sensor.query.get(sensor_id)
            if not sensor:
                return {}
            
            # 获取最近的读数
            recent_readings = Reading.query.filter_by(
                sensor_id=sensor_id
            ).order_by(Reading.timestamp.desc()).limit(limit).all()
            
            total_readings = Reading.query.filter_by(sensor_id=sensor_id).count()
            
            # 计算数值型传感器的统计数据
            stats = {
                'sensor_id': sensor_id,
                'sensor_name': sensor.name,
                'sensor_type': sensor.sensor_type,
                'data_type': sensor.data_type,
                'total_readings': total_readings,
                'recent_readings_count': len(recent_readings)
            }
            
            if sensor.is_numeric_sensor() and recent_readings:
                numeric_values = [r.numeric_value for r in recent_readings if r.numeric_value is not None]
                if numeric_values:
                    stats.update({
                        'min_value': min(numeric_values),
                        'max_value': max(numeric_values),
                        'avg_value': sum(numeric_values) / len(numeric_values),
                        'latest_value': numeric_values[0] if numeric_values else None
                    })
            
            if sensor.is_multimedia_sensor():
                # 统计多媒体文件
                image_count = len([r for r in recent_readings if r.data_type == 'image'])
                video_count = len([r for r in recent_readings if r.data_type == 'video'])
                stats.update({
                    'image_count': image_count,
                    'video_count': video_count
                })
            
            return stats
            
        except Exception as e:
            logging.error(f"Failed to get sensor statistics for {sensor_id}: {e}")
            return {}
    
    @staticmethod
    def get_numeric_sensors(device_id: Optional[int] = None) -> List[Sensor]:
        """获取数值型传感器"""
        sensors = SensorService.get_active_sensors(device_id)
        return [s for s in sensors if s.is_numeric_sensor]
    
    @staticmethod
    def get_multimedia_sensors(device_id: Optional[int] = None) -> List[Sensor]:
        """获取多媒体传感器"""
        sensors = SensorService.get_active_sensors(device_id)
        return [s for s in sensors if s.is_multimedia_sensor]
