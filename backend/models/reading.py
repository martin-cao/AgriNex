from datetime import datetime
from extensions import db

class Reading(db.Model):
    __tablename__ = 'readings'

    id = db.Column(db.BigInteger, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    value = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'sensor_id': self.sensor_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'value': self.value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create(cls, sensor_id, value, timestamp=None):
        reading = cls(
            sensor_id=sensor_id,
            value=value,
            timestamp=timestamp or datetime.utcnow()
        )
        db.session.add(reading)
        return reading
    
    def __repr__(self):
        return f"<Reading(id={self.id}, sensor_id={self.sensor_id}, value={self.value})>"
