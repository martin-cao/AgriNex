from backend.extensions import db
from datetime import datetime

class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    type = db.Column(db.String(50))
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    sensors = db.relationship('Sensor', backref='device', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'type': self.type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create(cls, name, location=None, device_type=None, status='active'):
        device = cls(
            name=name,
            location=location,
            type=device_type,
            status=status
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
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    def __repr__(self):
        return f"<Device(id={self.id}, name='{self.name}', status='{self.status}')>"
