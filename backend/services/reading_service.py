# backend/services/reading_service.py
from typing import List, Optional, Dict, Any, BinaryIO
from datetime import datetime, timedelta
from models.reading import Reading
from models.sensor import Sensor
from extensions import db
from services.storage_service import storage_service
import logging
import json

class ReadingService:
    """传感器读数业务逻辑服务"""
    
    @staticmethod
    def create_numeric_reading(sensor_id: int, value: float, 
                             timestamp: Optional[datetime] = None,
                             metadata: Optional[Dict[str, Any]] = None) -> Reading:
        """创建数值型读数"""
        try:
            sensor = Sensor.query.get(sensor_id)
            if not sensor:
                raise ValueError(f"Sensor {sensor_id} not found")
            
            if not sensor.is_numeric_sensor:
                raise ValueError(f"Sensor {sensor_id} is not a numeric sensor")
            
            reading = Reading(
                sensor_id=sensor_id,
                device_id=sensor.device_id,
                data_type='numeric',
                numeric_value=value,
                timestamp=timestamp or datetime.utcnow(),
                metadata=metadata or {}
            )
            
            db.session.add(reading)
            db.session.commit()
            logging.info(f"Created numeric reading for sensor {sensor_id}")
            return reading
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to create numeric reading: {e}")
            raise
    
    @staticmethod
    def create_multimedia_reading(sensor_id: int, file_data: BinaryIO,
                                data_type: str, file_format: str,
                                timestamp: Optional[datetime] = None,
                                metadata: Optional[Dict[str, Any]] = None) -> Reading:
        """创建多媒体读数（图片/视频）"""
        try:
            sensor = Sensor.query.get(sensor_id)
            if not sensor:
                raise ValueError(f"Sensor {sensor_id} not found")
            
            if not sensor.is_multimedia_sensor:
                raise ValueError(f"Sensor {sensor_id} is not a multimedia sensor")
            
            if data_type not in ['image', 'video']:
                raise ValueError(f"Invalid data type: {data_type}")
            
            # 上传文件到存储服务
            bucket_name = f"device-{sensor.device_id}"
            upload_result = storage_service.upload_file(
                file_data=file_data,
                bucket_name=bucket_name,
                data_type=data_type,
                device_id=str(sensor.device_id),
                sensor_id=str(sensor_id),
                file_format=file_format,
                metadata=metadata
            )
            
            if not upload_result.get('success'):
                raise Exception(f"Failed to upload file: {upload_result.get('error')}")
            
            # 创建读数记录
            reading = Reading(
                sensor_id=sensor_id,
                device_id=sensor.device_id,
                data_type=data_type,
                file_path=upload_result.get('file_path'),
                file_format=file_format,
                file_size=upload_result.get('file_size'),
                storage_backend=upload_result.get('storage_backend', 'local'),
                bucket_name=upload_result.get('bucket_name'),
                object_key=upload_result.get('object_key'),
                object_url=upload_result.get('object_url'),
                object_etag=upload_result.get('object_etag'),
                timestamp=timestamp or datetime.utcnow(),
                metadata=upload_result.get('metadata', {})
            )
            
            db.session.add(reading)
            db.session.commit()
            logging.info(f"Created {data_type} reading for sensor {sensor_id}")
            return reading
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to create multimedia reading: {e}")
            raise
    
    @staticmethod
    def get_reading_by_id(reading_id: int) -> Optional[Reading]:
        """根据ID获取读数"""
        return Reading.query.get(reading_id)
    
    @staticmethod
    def get_readings_by_sensor(sensor_id: int, limit: int = 100, 
                              offset: int = 0) -> List[Reading]:
        """获取传感器的读数"""
        return Reading.query.filter_by(
            sensor_id=sensor_id
        ).order_by(Reading.timestamp.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_readings_by_device(device_id: int, limit: int = 100,
                              offset: int = 0) -> List[Reading]:
        """获取设备的所有读数"""
        return Reading.query.filter_by(
            device_id=device_id
        ).order_by(Reading.timestamp.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_readings_by_type(data_type: str, device_id: Optional[int] = None,
                           limit: int = 100, offset: int = 0) -> List[Reading]:
        """根据数据类型获取读数"""
        query = Reading.query.filter_by(data_type=data_type)
        if device_id:
            query = query.filter_by(device_id=device_id)
        return query.order_by(Reading.timestamp.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_readings_in_timerange(sensor_id: Optional[int] = None,
                                device_id: Optional[int] = None,
                                start_time: Optional[datetime] = None,
                                end_time: Optional[datetime] = None,
                                limit: int = 1000) -> List[Reading]:
        """获取时间范围内的读数"""
        query = Reading.query
        
        if sensor_id:
            query = query.filter_by(sensor_id=sensor_id)
        elif device_id:
            query = query.filter_by(device_id=device_id)
        
        if start_time:
            query = query.filter(Reading.timestamp >= start_time)
        if end_time:
            query = query.filter(Reading.timestamp <= end_time)
        
        return query.order_by(Reading.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def get_latest_reading(sensor_id: int) -> Optional[Reading]:
        """获取传感器的最新读数"""
        return Reading.query.filter_by(
            sensor_id=sensor_id
        ).order_by(Reading.timestamp.desc()).first()
    
    @staticmethod
    def get_latest_readings_by_device(device_id: int) -> List[Reading]:
        """获取设备每个传感器的最新读数"""
        # 获取设备的所有传感器
        sensors = Sensor.query.filter_by(device_id=device_id, status='active').all()
        latest_readings = []
        
        for sensor in sensors:
            latest = ReadingService.get_latest_reading(sensor.id)
            if latest:
                latest_readings.append(latest)
        
        return latest_readings
    
    @staticmethod
    def delete_reading(reading_id: int) -> bool:
        """删除读数（同时删除相关文件）"""
        try:
            reading = Reading.query.get(reading_id)
            if not reading:
                return False
            
            # 如果是多媒体文件，删除存储的文件
            if reading.is_multimedia and reading.bucket_name and reading.object_key:
                storage_service.delete_file(
                    bucket_name=reading.bucket_name,
                    object_key=reading.object_key,
                    local_path=reading.file_path
                )
            
            db.session.delete(reading)
            db.session.commit()
            logging.info(f"Deleted reading {reading_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to delete reading {reading_id}: {e}")
            return False
    
    @staticmethod
    def batch_create_numeric_readings(readings_data: List[Dict[str, Any]]) -> List[Reading]:
        """批量创建数值型读数"""
        readings = []
        try:
            for data in readings_data:
                reading = Reading(
                    sensor_id=data['sensor_id'],
                    device_id=data['device_id'],
                    data_type='numeric',
                    numeric_value=data['value'],
                    timestamp=data.get('timestamp', datetime.utcnow()),
                    metadata=data.get('metadata', {})
                )
                readings.append(reading)
                db.session.add(reading)
            
            db.session.commit()
            logging.info(f"Created {len(readings)} numeric readings in batch")
            return readings
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to create batch numeric readings: {e}")
            raise
    
    @staticmethod
    def get_reading_statistics(sensor_id: Optional[int] = None,
                             device_id: Optional[int] = None,
                             data_type: Optional[str] = None,
                             days: int = 7) -> Dict[str, Any]:
        """获取读数统计信息"""
        try:
            # 计算时间范围
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            query = Reading.query.filter(
                Reading.timestamp >= start_time,
                Reading.timestamp <= end_time
            )
            
            if sensor_id:
                query = query.filter_by(sensor_id=sensor_id)
            elif device_id:
                query = query.filter_by(device_id=device_id)
            
            if data_type:
                query = query.filter_by(data_type=data_type)
            
            readings = query.all()
            
            stats = {
                'total_count': len(readings),
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'days': days
                }
            }
            
            # 按数据类型分组
            type_stats = {}
            for reading in readings:
                dtype = reading.data_type
                if dtype not in type_stats:
                    type_stats[dtype] = {'count': 0, 'size_total': 0}
                
                type_stats[dtype]['count'] += 1
                if reading.file_size:
                    type_stats[dtype]['size_total'] += reading.file_size
            
            stats['by_type'] = type_stats
            
            # 如果是数值型数据，计算统计值
            numeric_readings = [r for r in readings if r.data_type == 'numeric' and r.numeric_value is not None]
            if numeric_readings:
                values = [r.numeric_value for r in numeric_readings]
                stats['numeric_stats'] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'latest': values[0] if values else None
                }
            
            return stats
            
        except Exception as e:
            logging.error(f"Failed to get reading statistics: {e}")
            return {}
    
    @staticmethod
    def export_readings_csv(sensor_id: Optional[int] = None,
                           device_id: Optional[int] = None,
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None) -> str:
        """导出读数为CSV格式"""
        try:
            readings = ReadingService.get_readings_in_timerange(
                sensor_id=sensor_id,
                device_id=device_id,
                start_time=start_time,
                end_time=end_time
            )
            
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            headers = ['id', 'sensor_id', 'device_id', 'data_type', 'timestamp', 
                      'numeric_value', 'file_path', 'file_format', 'file_size', 'metadata']
            writer.writerow(headers)
            
            # 写入数据
            for reading in readings:
                row = [
                    reading.id,
                    reading.sensor_id,
                    reading.device_id,
                    reading.data_type,
                    reading.timestamp.isoformat(),
                    reading.numeric_value,
                    reading.file_path,
                    reading.file_format,
                    reading.file_size,
                    json.dumps(reading.metadata) if reading.metadata else ''
                ]
                writer.writerow(row)
            
            return output.getvalue()
            
        except Exception as e:
            logging.error(f"Failed to export readings to CSV: {e}")
            return ""
