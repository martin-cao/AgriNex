"""
Basic tests for AgriNex Sensor Client v2.0
"""

import pytest
import asyncio
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.config import Config, MQTTConfig, SerialConfig
from src.core.sensor_data import SensorData, SensorReading
from src.adapters.serial_adapter import SerialAdapter


class TestConfig:
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = Config()
        assert config.client_id == "sensor_client_001"
        assert config.mqtt.host == "localhost"
        assert config.mqtt.port == 1883
        assert config.serial.simulation_mode == True
    
    def test_config_from_dict(self):
        """Test configuration from dictionary."""
        data = {
            "client_id": "test_client",
            "mqtt": {
                "host": "test.mqtt.com",
                "port": 8883
            },
            "serial": {
                "simulation_mode": False
            }
        }
        
        config = Config.from_dict(data)
        assert config.client_id == "test_client"
        assert config.mqtt.host == "test.mqtt.com"
        assert config.mqtt.port == 8883
        assert config.serial.simulation_mode == False


class TestSensorData:
    """Test sensor data models."""
    
    def test_sensor_reading(self):
        """Test sensor reading creation."""
        reading = SensorReading(
            sensor_type="temperature",
            value=22.5,
            unit="°C",
            timestamp=datetime.now()
        )
        
        assert reading.sensor_type == "temperature"
        assert reading.value == 22.5
        assert reading.unit == "°C"
        
        # Test serialization
        data = reading.to_dict()
        assert data["sensor_type"] == "temperature"
        assert data["value"] == 22.5
    
    def test_sensor_data(self):
        """Test sensor data collection."""
        readings = [
            SensorReading("temperature", 22.5, "°C", datetime.now()),
            SensorReading("humidity", 65.0, "%", datetime.now())
        ]
        
        sensor_data = SensorData(
            client_id="test_client",
            readings=readings
        )
        
        assert sensor_data.client_id == "test_client"
        assert len(sensor_data.readings) == 2
        
        # Test numeric values extraction
        numeric = sensor_data.get_numeric_values()
        assert numeric["temperature"] == 22.5
        assert numeric["humidity"] == 65.0


class TestSerialAdapter:
    """Test serial adapter functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = Config()
        config.serial.simulation_mode = True
        config.sensor.collection_interval = 1.0
        return config
    
    def test_adapter_creation(self, config):
        """Test adapter creation."""
        adapter = SerialAdapter(config)
        assert adapter.config == config
        assert adapter.connected == False
        assert adapter.simulation_active == False
    
    @pytest.mark.asyncio
    async def test_simulation_connect(self, config):
        """Test simulation mode connection."""
        adapter = SerialAdapter(config)
        
        # Test connection in simulation mode
        connected = await adapter.connect()
        assert connected == True
        assert adapter.connected == True
        assert adapter.simulation_active == True
        
        # Cleanup
        adapter.disconnect()
        assert adapter.connected == False
    
    def test_mock_data_generation(self, config):
        """Test mock data generation."""
        adapter = SerialAdapter(config)
        
        # Generate mock readings
        readings = adapter._generate_mock_readings()
        assert len(readings) > 0
        
        # Check reading structure
        temp_reading = next((r for r in readings if r.sensor_type == "temperature"), None)
        assert temp_reading is not None
        assert temp_reading.unit == "°C"
        assert -10 <= temp_reading.value <= 50  # Realistic range


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
