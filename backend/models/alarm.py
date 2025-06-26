from backend.extensions import db
from datetime import datetime

class Alarm(db.Model):
    __tablename__ = 'alarms'
    
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False)
    alarm_type = db.Column(db.String(50), nullable=False)
    threshold_value = db.Column(db.Float)
    actual_value = db.Column(db.Float)
    severity = db.Column(db.String(20), default='medium')  # low/medium/high
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active/resolved
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    sensor = db.relationship('Sensor', backref=db.backref('alarms', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'sensor_id': self.sensor_id,
            'alarm_type': self.alarm_type,
            'threshold_value': self.threshold_value,
            'actual_value': self.actual_value,
            'severity': self.severity,
            'message': self.message,
            'status': self.status,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def create_alarm(cls, sensor_id, alarm_type, actual_value, threshold_value, message):
        """创建告警"""
        alarm = cls(
            sensor_id=sensor_id,
            alarm_type=alarm_type,
            actual_value=actual_value,
            threshold_value=threshold_value,
            message=message
        )
        db.session.add(alarm)
        return alarm
    
    def resolve(self, resolved_by=None):
        """解决告警"""
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()
        if resolved_by:
            self.resolved_by = resolved_by
        return self
