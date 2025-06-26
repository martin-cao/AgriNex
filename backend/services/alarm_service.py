# backend/services/alarm_service.py
from backend.models.alarm import Alarm
from backend.extensions import db

class AlarmService:
    @staticmethod
    def create_alarm(device_id, alarm_type, message, timestamp=None):
        alarm = Alarm(
            device_id=device_id,
            alarm_type=alarm_type,
            message=message,
            timestamp=timestamp
        )
        db.session.add(alarm)
        db.session.commit()
        return alarm

    @staticmethod
    def get_alarms(device_id=None):
        query = Alarm.query
        if device_id:
            query = query.filter_by(device_id=device_id)
        return query.order_by(Alarm.timestamp.desc()).all()