from extensions import db
from datetime import datetime

class Prediction(db.Model):
    __tablename__ = 'predictions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.BigInteger, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False)
    predict_ts = db.Column(db.DateTime, nullable=False)
    yhat = db.Column(db.Double)
    yhat_lower = db.Column(db.Double)
    yhat_upper = db.Column(db.Double)
    metric_type = db.Column(db.String(20))
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sensor_id': self.sensor_id,
            'predict_ts': self.predict_ts.isoformat() if self.predict_ts else None,
            'yhat': self.yhat,
            'yhat_lower': self.yhat_lower,
            'yhat_upper': self.yhat_upper,
            'metric_type': self.metric_type,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }
