# backend/services/lim_service.py
from backend.models.device import Device
from backend.extensions import db

class LimService:
    @staticmethod
    def set_device_limit(device_id, limit_type, value):
        device = Device.query.get(device_id)
        if not device:
            return None
        setattr(device, limit_type, value)
        db.session.commit()
        return device

    @staticmethod
    def get_device_limit(device_id, limit_type):
        device = Device.query.get(device_id)
        if not device:
            return None
        return getattr(device, limit_type, None)