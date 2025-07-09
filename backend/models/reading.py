from datetime import datetime
from extensions import db
import json

class Reading(db.Model):
    __tablename__ = 'readings'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.BigInteger, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 数据类型标识
    data_type = db.Column(db.String(20), nullable=False, default='numeric')  # 'numeric', 'image', 'video'
    
    # 数值型数据（温度、湿度、光照）
    numeric_value = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(10), nullable=True)  # 单位，如 °C, %, lux
    
    # 文件型数据（图片、视频）
    file_path = db.Column(db.String(512), nullable=True)  # 本地文件存储路径（备份）
    file_size = db.Column(db.BigInteger, nullable=True)   # 文件大小(字节)
    file_format = db.Column(db.String(10), nullable=True) # 文件格式，如 jpg, mp4
    
    # 对象存储相关字段
    storage_backend = db.Column(db.String(20), default='minio')  # 'local', 'minio', 'dual'
    bucket_name = db.Column(db.String(100), nullable=True)       # MinIO存储桶名称
    object_key = db.Column(db.String(500), nullable=True)        # 对象存储的key路径
    object_url = db.Column(db.String(1000), nullable=True)       # 对象访问URL
    object_etag = db.Column(db.String(100), nullable=True)       # 对象ETag（用于完整性校验）
    
    # 额外元数据
    meta_info = db.Column(db.Text, nullable=True)  # JSON格式的额外信息
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        result = {
            'id': self.id,
            'sensor_id': self.sensor_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'data_type': self.data_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        # 根据数据类型返回相应字段
        if self.data_type == 'numeric':
            result.update({
                'value': self.numeric_value,
                'unit': self.unit
            })
        elif self.data_type in ['image', 'video']:
            result.update({
                'file_path': self.file_path,
                'file_size': self.file_size,
                'file_format': self.file_format,
                'storage_backend': self.storage_backend,
                'bucket_name': self.bucket_name,
                'object_key': self.object_key,
                'object_url': self.object_url,
                'object_etag': self.object_etag
            })
        
        # 附加元信息
        if self.meta_info:
            try:
                result['metadata'] = json.loads(self.meta_info)
            except (json.JSONDecodeError, TypeError):
                result['metadata'] = self.meta_info
        
        return result

    @classmethod
    def create_numeric(cls, sensor_id, value, unit=None, timestamp=None, metadata=None):
        """创建数值型读数"""
        return cls(
            sensor_id=sensor_id,
            data_type='numeric',
            numeric_value=value,
            unit=unit,
            timestamp=timestamp or datetime.utcnow(),
            meta_info=json.dumps(metadata) if metadata else None
        )

    @classmethod  
    def create_file(cls, sensor_id, data_type, file_path=None, file_size=None,
                   file_format=None, bucket_name=None, object_key=None,
                   object_url=None, object_etag=None, storage_backend='minio',
                   timestamp=None, metadata=None):
        """创建文件型读数（图片/视频）"""
        return cls(
            sensor_id=sensor_id,
            data_type=data_type,
            file_path=file_path,
            file_size=file_size,
            file_format=file_format,
            storage_backend=storage_backend,
            bucket_name=bucket_name,
            object_key=object_key,
            object_url=object_url,
            object_etag=object_etag,
            timestamp=timestamp or datetime.utcnow(),
            meta_info=json.dumps(metadata) if metadata else None
        )

    def is_numeric(self):
        """是否为数值型读数"""
        return self.data_type == 'numeric'
    
    def is_file(self):
        """是否为文件型读数"""
        return self.data_type in ['image', 'video']

    def get_metadata(self):
        """获取元数据"""
        if not self.meta_info:
            return {}
        try:
            return json.loads(self.meta_info)
        except (json.JSONDecodeError, TypeError):
            return {'raw': self.meta_info}

    def set_metadata(self, metadata_dict):
        """设置元数据"""
        self.meta_info = json.dumps(metadata_dict) if metadata_dict else None

    def __repr__(self):
        return f'<Reading {self.id}: {self.data_type} for sensor {self.sensor_id}>'