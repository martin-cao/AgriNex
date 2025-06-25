# backend/services/sensor_service.py
from backend.models.sensor import Sensor
from backend.extensions import db

class SensorService:
    @staticmethod
    def get_sensor_by_id(sensor_id):
        return Sensor.query.get(sensor_id)

    @staticmethod
    def get_sensors_by_device(device_id):
        return Sensor.query.filter_by(device_id=device_id).all()

    @staticmethod
    def add_sensor(**kwargs):
        sensor = Sensor(**kwargs)
        db.session.add(sensor)
        db.session.commit()
        return sensor
