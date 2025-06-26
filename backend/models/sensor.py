from backend.extensions import db
from datetime import datetime

class Sensor(db.Model):
    __tablename__ = 'sensors'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255))
    unit = db.Column(db.String(20))
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    readings = db.relationship('Reading', backref='sensor', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'type': self.type,
            'name': self.name,
            'unit': self.unit,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create(cls, device_id, sensor_type, name=None, unit=None, status='active'):
        sensor = cls(
            device_id=device_id,
            type=sensor_type,
            name=name,
            unit=unit,
            status=status
        )
        db.session.add(sensor)
        return sensor
    
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        return self
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def latest_reading(self):
        if self.readings:
            return sorted(self.readings, key=lambda r: r.timestamp, reverse=True)[0]
        return None
    
    @property
    def is_multimedia_sensor(self):
        """判断是否为多媒体传感器"""
        return self.type in ['camera', 'video_camera', 'surveillance_camera']
    
    @property
    def is_numeric_sensor(self):
        """判断是否为数值传感器"""
        return self.type in ['temperature', 'humidity', 'light', 'pressure', 'ph', 'soil_moisture']
    
    @property
    def supported_data_types(self):
        """获取支持的数据类型"""
        if self.is_numeric_sensor:
            return ['numeric']
        elif self.is_multimedia_sensor:
            return ['image', 'video']
        else:
            return ['numeric', 'image', 'video']  # 通用传感器支持所有类型
    
    def get_readings_by_type(self, data_type=None, limit=None):
        """根据数据类型获取读数"""
        from backend.models.reading import Reading
        query = Reading.query.filter_by(sensor_id=self.id)
        
        if data_type:
            query = query.filter_by(data_type=data_type)
            
        query = query.order_by(Reading.timestamp.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_latest_reading_by_type(self, data_type=None):
        """获取指定类型的最新读数"""
        readings = self.get_readings_by_type(data_type=data_type, limit=1)
        return readings[0] if readings else None
