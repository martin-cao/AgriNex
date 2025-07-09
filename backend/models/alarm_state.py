from extensions import db
from datetime import datetime

class AlarmState(db.Model):
    __tablename__ = 'alarm_states'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    alarm_rule_id = db.Column(db.Integer, db.ForeignKey('alarm_rules.id'), nullable=False)
    consecutive_count = db.Column(db.Integer, default=0)
    last_triggered_at = db.Column(db.DateTime)
    last_value = db.Column(db.Float)
    
    # 关系
    alarm_rule = db.relationship('AlarmRule', backref=db.backref('alarm_state', uselist=False))
    
    def to_dict(self):
        return {
            'id': self.id,
            'alarm_rule_id': self.alarm_rule_id,
            'consecutive_count': self.consecutive_count,
            'last_triggered_at': self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            'last_value': self.last_value
        }
