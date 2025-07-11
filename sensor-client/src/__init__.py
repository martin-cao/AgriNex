"""
AgriNex Sensor Client Package
============================

A modular sensor data collection and transmission system for agricultural monitoring.

Architecture:
- core: Core business logic and domain models
- adapters: External interface adapters (MQTT, Serial, etc.)
- services: Application services and orchestration
- utils: Utility functions and helpers
"""

__version__ = "2.0.0"
__author__ = "AgriNex Team"

# Import main components
from .core.sensor_data import SensorData, SensorReading
from .core.config import Config
from .services.sensor_service import SensorService
from .adapters.mqtt_adapter import MQTTAdapter
from .adapters.serial_adapter import SerialAdapter

__all__ = [
    'SensorData',
    'SensorReading', 
    'Config',
    'SensorService',
    'MQTTAdapter',
    'SerialAdapter'
]
