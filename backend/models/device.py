from extensions import db
from datetime import datetime

class Device(db.Model):
    __tablename__ = 'devices'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    type = db.Column(db.String(50))
    status = db.Column(db.String(50), default='active')
    # 新增字段：设备IP地址和端口
    ip_address = db.Column(db.String(45))  # 支持IPv4和IPv6
    port = db.Column(db.Integer)
    # 新增字段：设备是否启用（用于开启/关闭设备）
    is_active = db.Column(db.Boolean, default=True)
    # 新增字段：设备client_id（用于MQTT主题匹配）
    client_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    sensors = db.relationship('Sensor', backref='device', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        # 计算活跃传感器数量
        active_sensors = [s for s in self.sensors if s.status == 'active']
        
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'device_type': self.type,  # 修复：前端期望的字段名是device_type
            'status': self.status,
            'ip_address': self.ip_address,
            'port': self.port,
            'is_active': self.is_active,
            'client_id': self.client_id,
            'sensor_count': len(active_sensors),  # 添加传感器数量
            'last_seen': self.updated_at.isoformat() if self.updated_at else None,  # 使用更新时间作为最后在线时间
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create(cls, name, location=None, device_type=None, status='active', 
               ip_address=None, port=None, is_active=True, client_id=None):
        device = cls(
            name=name,
            location=location,
            type=device_type,
            status=status,
            ip_address=ip_address,
            port=port,
            is_active=is_active,
            client_id=client_id
        )
        db.session.add(device)
        return device
    
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        return self
    
    def delete(self):
        self.status = 'deleted'
        return self
    
    def __repr__(self):
        return f"<Device(id={self.id}, name='{self.name}', status='{self.status}')>"
