# backend/services/ingestion_service.py
from backend.models.reading import Reading
from backend.extensions import db

class IngestionService:
    @staticmethod
    def ingest_reading(device_id, temperature, humidity, light, timestamp=None):
        reading = Reading(
            device_id=device_id,
            temperature=temperature,
            humidity=humidity,
            light=light,
            timestamp=timestamp
        )
        db.session.add(reading)
        db.session.commit()
        return reading

    @staticmethod
    def get_latest_reading(device_id):
        return Reading.query.filter_by(device_id=device_id).order_by(Reading.timestamp.desc()).first()