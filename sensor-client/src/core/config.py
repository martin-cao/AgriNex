"""
Configuration management for the sensor client.
"""

import os
import json
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional, List
from pathlib import Path


@dataclass
class MQTTConfig:
    """MQTT connection configuration."""
    host: str = "localhost"
    port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    keepalive: int = 60
    qos: int = 1
    retain: bool = False
    
    
@dataclass
class SerialConfig:
    """Serial port configuration."""
    ports: Optional[List[str]] = None
    baudrate: int = 9600
    timeout: float = 1.0
    auto_detect: bool = True
    simulation_mode: bool = True
    
    def __post_init__(self):
        if self.ports is None:
            # Default ports based on platform
            import platform
            if platform.system() == "Windows":
                self.ports = [f"COM{i}" for i in range(1, 6)]
            else:
                self.ports = [f"/dev/ttyS{i}" for i in range(0, 5)]


@dataclass 
class SensorConfig:
    """Sensor data collection configuration."""
    collection_interval: float = 5.0
    data_format: str = "json"  # json, csv, binary
    include_metadata: bool = True
    quality_checks: bool = True
    mock_data_generation: bool = True
    

@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class Config:
    """Main configuration container."""
    client_id: str = "sensor_client_001"
    mqtt: MQTTConfig = field(default_factory=MQTTConfig)
    serial: SerialConfig = field(default_factory=SerialConfig)
    sensor: SensorConfig = field(default_factory=SensorConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    debug: bool = False
    
    @classmethod
    def from_file(cls, config_path: str) -> 'Config':
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except FileNotFoundError:
            print(f"Config file {config_path} not found, using defaults")
            return cls()
        except json.JSONDecodeError as e:
            print(f"Error parsing config file {config_path}: {e}")
            return cls()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create configuration from dictionary."""
        config = cls()
        
        # Update main config fields
        for key, value in data.items():
            if key in ('mqtt', 'serial', 'sensor', 'logging'):
                continue
            if hasattr(config, key):
                setattr(config, key, value)
        
        # Update nested configs
        if 'mqtt' in data:
            mqtt_data = data['mqtt']
            config.mqtt = MQTTConfig(**{k: v for k, v in mqtt_data.items() 
                                      if k in MQTTConfig.__dataclass_fields__})
        
        if 'serial' in data:
            serial_data = data['serial']
            config.serial = SerialConfig(**{k: v for k, v in serial_data.items() 
                                          if k in SerialConfig.__dataclass_fields__})
        
        if 'sensor' in data:
            sensor_data = data['sensor']
            config.sensor = SensorConfig(**{k: v for k, v in sensor_data.items() 
                                          if k in SensorConfig.__dataclass_fields__})
        
        if 'logging' in data:
            logging_data = data['logging']
            config.logging = LoggingConfig(**{k: v for k, v in logging_data.items() 
                                            if k in LoggingConfig.__dataclass_fields__})
        
        return config
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables."""
        config = cls()
        
        # Main config
        config.client_id = os.getenv('SENSOR_CLIENT_ID', config.client_id)
        config.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # MQTT config
        config.mqtt.host = os.getenv('MQTT_HOST', config.mqtt.host)
        config.mqtt.port = int(os.getenv('MQTT_PORT', str(config.mqtt.port)))
        config.mqtt.username = os.getenv('MQTT_USERNAME')
        config.mqtt.password = os.getenv('MQTT_PASSWORD')
        
        # Serial config
        config.serial.baudrate = int(os.getenv('SERIAL_BAUDRATE', str(config.serial.baudrate)))
        config.serial.simulation_mode = os.getenv('SERIAL_SIMULATION', 'true').lower() == 'true'
        
        # Sensor config
        config.sensor.collection_interval = float(os.getenv('COLLECTION_INTERVAL', 
                                                           str(config.sensor.collection_interval)))
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    def to_file(self, config_path: str) -> None:
        """Save configuration to JSON file."""
        config_dir = Path(config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def get_mqtt_topic(self, topic_type: str) -> str:
        """Get MQTT topic for different message types."""
        topics = {
            'sensor_data': f'sensors/{self.client_id}/data',
            'numeric': f'sensors/{self.client_id}/numeric',
            'status': f'sensors/{self.client_id}/status',
            'error': f'sensors/{self.client_id}/error'
        }
        return topics.get(topic_type, f'sensors/{self.client_id}/{topic_type}')
