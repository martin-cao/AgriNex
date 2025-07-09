from extensions import db
from datetime import datetime

class AlarmRule(db.Model):
    __tablename__ = 'alarm_rules'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False)
    
    # 规则配置
    rule_type = db.Column(db.String(50), nullable=False)  # 'threshold', 'change_rate', 'pattern'
    condition = db.Column(db.String(20), nullable=False)  # '>', '<', '>=', '<=', '==', '!='
    threshold_value = db.Column(db.Float, nullable=False)
    consecutive_count = db.Column(db.Integer, default=1)  # 连续触发次数
    
    # 状态和优先级
    is_active = db.Column(db.Boolean, default=True)
    severity = db.Column(db.String(20), default='medium')  # low/medium/high
    
    # 通知设置
    email_enabled = db.Column(db.Boolean, default=False)
    webhook_enabled = db.Column(db.Boolean, default=False)
    webhook_url = db.Column(db.String(500))
    
    # 元数据
    created_by = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    sensor = db.relationship('Sensor', backref=db.backref('alarm_rules', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sensor_id': self.sensor_id,
            'rule_type': self.rule_type,
            'condition': self.condition,
            'threshold_value': self.threshold_value,
            'consecutive_count': self.consecutive_count,
            'is_active': self.is_active,
            'severity': self.severity,
            'email_enabled': self.email_enabled,
            'webhook_enabled': self.webhook_enabled,
            'webhook_url': self.webhook_url,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def evaluate_condition(self, value):
        """评估条件是否满足"""
        if self.condition == '>':
            return value > self.threshold_value
        elif self.condition == '<':
            return value < self.threshold_value
        elif self.condition == '>=':
            return value >= self.threshold_value
        elif self.condition == '<=':
            return value <= self.threshold_value
        elif self.condition == '==':
            return value == self.threshold_value
        elif self.condition == '!=':
            return value != self.threshold_value
        return False
