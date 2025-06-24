from datetime import datetime
from extensions import db

class Sensor(db.Model):
    __tablename__ = 'sensors'

    id = db.Column(db.Integer, primary_key=True)  # 传感器ID
    name = db.Column(db.String(255), nullable=False)  # 传感器名称
    location = db.Column(db.String(255))  # 传感器位置
    unit = db.Column(db.String(50))  # 测量单位（如温度、湿度等）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间

    # 反向关系，表示每个传感器有多条读数记录
    readings = db.relationship('Reading', backref='sensor', lazy=True)

    def __repr__(self):
        return f"<Sensor(name={self.name}, location={self.location}, unit={self.unit})>"
