"""
Core sensor data models and types.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
import json


@dataclass
class SensorReading:
    """Represents a single sensor reading."""
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime
    quality: Optional[str] = "good"
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'sensor_type': self.sensor_type,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat(),
            'quality': self.quality,
            'metadata': self.metadata or {}
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class SensorData:
    """Collection of sensor readings with metadata."""
    client_id: str
    readings: list[SensorReading]
    location: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'client_id': self.client_id,
            'readings': [reading.to_dict() for reading in self.readings],
            'location': self.location,
            'device_info': self.device_info or {},
            'timestamp': self.timestamp.isoformat() if self.timestamp else datetime.now().isoformat()
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    def to_mqtt_payload(self) -> Dict[str, Any]:
        """Convert to MQTT payload format compatible with AgriNex backend."""
        # Transform to the format expected by the backend
        payload = {
            'client_id': self.client_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else datetime.now().isoformat(),
            'data': {}
        }
        
        # Group readings by sensor type
        for reading in self.readings:
            payload['data'][reading.sensor_type] = {
                'value': reading.value,
                'unit': reading.unit,
                'quality': reading.quality,
                'timestamp': reading.timestamp.isoformat()
            }
            
        return payload

    def get_numeric_values(self) -> Dict[str, float]:
        """Get numeric values only for simple transmission."""
        return {reading.sensor_type: reading.value for reading in self.readings}
