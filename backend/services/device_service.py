# backend/services/device_service.py
from typing import List, Optional, Dict, Any
from models.device import Device
from models.sensor import Sensor
from models.reading import Reading
from extensions import db
from services.sensor_service import SensorService
from services.reading_service import ReadingService
import logging

class DeviceService:
    """设备业务逻辑服务"""
    
    @staticmethod
    def get_device_by_id(device_id: int) -> Optional[Device]:
        """根据ID获取设备"""
        return Device.query.get(device_id)
    
    @staticmethod
    def get_all_devices(status: Optional[str] = None) -> List[Device]:
        """获取所有设备"""
        query = Device.query
        if status:
            query = query.filter_by(status=status)
        return query.all()
    
    @staticmethod
    def get_devices_by_type(device_type: str) -> List[Device]:
        """根据类型获取设备"""
        return Device.query.filter_by(device_type=device_type).all()
    
    @staticmethod
    def get_online_devices() -> List[Device]:
        """获取在线设备"""
        return Device.query.filter_by(status='online').all()
    
    @staticmethod
    def create_device(name: str, device_type: str, location: str,
                     description: Optional[str] = None,
                     config: Optional[Dict[str, Any]] = None) -> Device:
        """创建新设备"""
        try:
            device = Device(
                name=name,
                device_type=device_type,
                location=location,
                description=description,
                config=config or {},
                status='offline'
            )
            db.session.add(device)
            db.session.commit()
            logging.info(f"Created device {device.id}: {name}")
            return device
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to create device: {e}")
            raise
    
    @staticmethod
    def update_device(device_id: int, **kwargs) -> Optional[Device]:
        """更新设备信息"""
        try:
            device = Device.query.get(device_id)
            if not device:
                return None
            
            for key, value in kwargs.items():
                if hasattr(device, key):
                    setattr(device, key, value)
            
            db.session.commit()
            logging.info(f"Updated device {device_id}")
            return device
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to update device {device_id}: {e}")
            raise
    
    @staticmethod
    def delete_device(device_id: int) -> bool:
        """删除设备（软删除）"""
        try:
            device = Device.query.get(device_id)
            if not device:
                return False
            
            device.status = 'deleted'
            db.session.commit()
            logging.info(f"Deleted device {device_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to delete device {device_id}: {e}")
            return False
    
    @staticmethod
    def set_device_status(device_id: int, status: str) -> bool:
        """设置设备状态"""
        try:
            device = Device.query.get(device_id)
            if not device:
                return False
            
            device.status = status
            device.last_seen = None  # 可以在这里设置最后见到时间
            db.session.commit()
            logging.info(f"Set device {device_id} status to {status}")
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to set device {device_id} status: {e}")
            return False
    
    @staticmethod
    def get_device_overview(device_id: int) -> Dict[str, Any]:
        """获取设备概览信息"""
        try:
            device = Device.query.get(device_id)
            if not device:
                return {}
            
            # 获取设备的传感器
            sensors = SensorService.get_sensors_by_device(device_id)
            
            # 获取最新读数
            latest_readings = ReadingService.get_latest_readings_by_device(device_id)
            
            # 统计信息
            total_readings = Reading.query.filter_by(device_id=device_id).count()
            
            overview = {
                'device': device.to_dict(),
                'sensors': [sensor.to_dict() for sensor in sensors],
                'latest_readings': [reading.to_dict() for reading in latest_readings],
                'statistics': {
                    'total_sensors': len(sensors),
                    'active_sensors': len([s for s in sensors if s.status == 'active']),
                    'total_readings': total_readings,
                    'numeric_sensors': len([s for s in sensors if s.is_numeric_sensor]),
                    'multimedia_sensors': len([s for s in sensors if s.is_multimedia_sensor])
                }
            }
            
            return overview
            
        except Exception as e:
            logging.error(f"Failed to get device overview for {device_id}: {e}")
            return {}
    
    @staticmethod
    def get_device_sensors_by_type(device_id: int, data_type: str) -> List[Sensor]:
        """获取设备指定类型的传感器"""
        return Sensor.query.filter_by(
            device_id=device_id, 
            data_type=data_type,
            status='active'
        ).all()
    
    @staticmethod
    def get_device_readings_summary(device_id: int, days: int = 7) -> Dict[str, Any]:
        """获取设备读数汇总"""
        try:
            # 获取统计信息
            stats = ReadingService.get_reading_statistics(
                device_id=device_id,
                days=days
            )
            
            # 获取传感器信息
            sensors = SensorService.get_sensors_by_device(device_id)
            sensor_info = {}
            for sensor in sensors:
                sensor_stats = SensorService.get_sensor_statistics(sensor.id)
                sensor_info[sensor.id] = {
                    'sensor': sensor.to_dict(),
                    'statistics': sensor_stats
                }
            
            return {
                'device_id': device_id,
                'readings_summary': stats,
                'sensors_info': sensor_info,
                'summary_period_days': days
            }
            
        except Exception as e:
            logging.error(f"Failed to get device readings summary for {device_id}: {e}")
            return {}
    
    @staticmethod
    def batch_update_device_status(device_ids: List[int], status: str) -> Dict[str, Any]:
        """批量更新设备状态"""
        try:
            updated_count = 0
            failed_count = 0
            
            for device_id in device_ids:
                if DeviceService.set_device_status(device_id, status):
                    updated_count += 1
                else:
                    failed_count += 1
            
            return {
                'success': True,
                'updated_count': updated_count,
                'failed_count': failed_count,
                'total_count': len(device_ids)
            }
            
        except Exception as e:
            logging.error(f"Failed to batch update device status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def search_devices(query: str, device_type: Optional[str] = None,
                      status: Optional[str] = None) -> List[Device]:
        """搜索设备"""
        try:
            db_query = Device.query
            
            # 名称或位置匹配
            if query:
                db_query = db_query.filter(
                    db.or_(
                        Device.name.contains(query),
                        Device.location.contains(query),
                        Device.description.contains(query)
                    )
                )
            
            if device_type:
                db_query = db_query.filter_by(device_type=device_type)
            
            if status:
                db_query = db_query.filter_by(status=status)
            
            return db_query.all()
            
        except Exception as e:
            logging.error(f"Failed to search devices: {e}")
            return []
    
    @staticmethod
    def get_device_health_status(device_id: int) -> Dict[str, Any]:
        """获取设备健康状态"""
        try:
            device = Device.query.get(device_id)
            if not device:
                return {'status': 'unknown', 'message': 'Device not found'}
            
            # 检查设备基本状态
            if device.status == 'offline':
                return {'status': 'offline', 'message': 'Device is offline'}
            
            # 检查传感器状态
            sensors = SensorService.get_active_sensors(device_id)
            if not sensors:
                return {'status': 'warning', 'message': 'No active sensors'}
            
            # 检查最近是否有数据上报
            from datetime import datetime, timedelta
            recent_threshold = datetime.utcnow() - timedelta(minutes=30)
            recent_readings = Reading.query.filter(
                Reading.device_id == device_id,
                Reading.timestamp >= recent_threshold
            ).count()
            
            if recent_readings == 0:
                return {'status': 'warning', 'message': 'No recent data'}
            
            return {'status': 'healthy', 'message': 'Device is operating normally'}
            
        except Exception as e:
            logging.error(f"Failed to get device health status for {device_id}: {e}")
            return {'status': 'error', 'message': str(e)}
