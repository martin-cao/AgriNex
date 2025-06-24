from datetime import datetime
from extensions import db

class Reading(db.Model):
    __tablename__ = 'readings'

    id = db.Column(db.BigInteger, primary_key=True)  # 读数的唯一标识
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False)  # 关联的传感器ID
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 读数的时间戳
    temperature = db.Column(db.Float)  # 温度数据
    humidity = db.Column(db.Float)  # 湿度数据
    light = db.Column(db.Float)  # 光照数据

    # 反向关系，获取这个读数所属的传感器
    sensor = db.relationship('Sensor', backref=db.backref('readings', lazy=True))

    def __repr__(self):
        return f"<Reading(sensor_id={self.sensor_id}, temperature={self.temperature}, humidity={self.humidity})>"
