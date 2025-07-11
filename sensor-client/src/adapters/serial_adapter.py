"""
Serial port adapter for sensor data collection.
"""

import asyncio
import logging
import platform
import random
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
import serial
import serial.tools.list_ports
from ..core.config import Config
from ..core.sensor_data import SensorData, SensorReading


class SerialAdapter:
    """Serial communication adapter with simulation capabilities."""
    
    def __init__(self, config: Config):
        self.config = config
        self.serial_config = config.serial
        self.logger = logging.getLogger(__name__)
        
        # Serial connection
        self.serial_connection: Optional[serial.Serial] = None
        self.active_port: Optional[str] = None
        self.connected = False
        
        # Data collection
        self.data_callbacks: List[Callable[[SensorData], None]] = []
        self.error_callbacks: List[Callable[[str, Exception], None]] = []
        
        # Simulation state
        self.simulation_active = False
        self.simulation_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.readings_collected = 0
        self.errors_count = 0
        self.last_reading_time: Optional[datetime] = None
        
        # Mock sensor state for simulation
        self.mock_sensors = {
            'temperature': {'value': 22.0, 'trend': 0.1, 'unit': '°C'},
            'humidity': {'value': 45.0, 'trend': 0.2, 'unit': '%'},
            'light': {'value': 800.0, 'trend': 5.0, 'unit': 'lux'},
            'ph': {'value': 6.8, 'trend': 0.05, 'unit': 'pH'},
            'moisture': {'value': 35.0, 'trend': 0.3, 'unit': '%'}
        }
    
    def add_data_callback(self, callback: Callable[[SensorData], None]) -> None:
        """Add callback for collected sensor data."""
        self.data_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str, Exception], None]) -> None:
        """Add callback for errors."""
        self.error_callbacks.append(callback)
    
    def _notify_data(self, sensor_data: SensorData) -> None:
        """Notify data callbacks."""
        for callback in self.data_callbacks:
            try:
                callback(sensor_data)
            except Exception as e:
                self.logger.error(f"Error in data callback: {e}")
    
    def _notify_error(self, context: str, error: Exception) -> None:
        """Notify error callbacks."""
        for callback in self.error_callbacks:
            try:
                callback(context, error)
            except Exception as e:
                self.logger.error(f"Error in error callback: {e}")
    
    def _detect_serial_ports(self) -> List[str]:
        """Detect available serial ports."""
        try:
            ports = serial.tools.list_ports.comports()
            available_ports = [port.device for port in ports]
            self.logger.info(f"Detected serial ports: {available_ports}")
            return available_ports
        except Exception as e:
            self.logger.error(f"Error detecting serial ports: {e}")
            return []
    
    def _get_platform_ports(self) -> List[str]:
        """Get platform-specific default ports."""
        system = platform.system()
        if system == "Windows":
            return [f"COM{i}" for i in range(1, 11)]
        elif system == "Darwin":  # macOS
            return [f"/dev/tty.usbserial-{i}" for i in range(10)] + [f"/dev/ttyS{i}" for i in range(5)]
        else:  # Linux
            return [f"/dev/ttyS{i}" for i in range(10)] + [f"/dev/ttyUSB{i}" for i in range(5)]
    
    async def connect(self) -> bool:
        """Connect to serial port."""
        if self.connected:
            return True
        
        try:
            # Try to connect to real serial ports
            if self.serial_config.auto_detect:
                available_ports = self._detect_serial_ports()
            else:
                available_ports = self.serial_config.ports or []
            
            # Add platform-specific ports if none detected
            if not available_ports:
                available_ports = self._get_platform_ports()
            
            # Try each port
            for port in available_ports:
                try:
                    self.logger.info(f"Attempting to connect to {port}")
                    self.serial_connection = serial.Serial(
                        port=port,
                        baudrate=self.serial_config.baudrate,
                        timeout=self.serial_config.timeout
                    )
                    
                    # Test the connection
                    await asyncio.sleep(0.1)
                    if self.serial_connection.is_open:
                        self.active_port = port
                        self.connected = True
                        self.logger.info(f"Connected to serial port: {port}")
                        return True
                        
                except (serial.SerialException, OSError) as e:
                    self.logger.debug(f"Failed to connect to {port}: {e}")
                    if self.serial_connection:
                        self.serial_connection.close()
                        self.serial_connection = None
            
            # If no real ports available, check if simulation is enabled
            if self.serial_config.simulation_mode:
                self.logger.info("No serial ports available, switching to simulation mode")
                self.connected = True
                self.simulation_active = True
                return True
            else:
                self.logger.error("No serial ports available and simulation disabled")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to serial port: {e}")
            self._notify_error("serial_connect", e)
            return False
    
    def disconnect(self) -> None:
        """Disconnect from serial port."""
        try:
            if self.simulation_task:
                self.simulation_task.cancel()
                self.simulation_task = None
            
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                self.logger.info(f"Disconnected from serial port: {self.active_port}")
            
            self.connected = False
            self.simulation_active = False
            self.active_port = None
            self.serial_connection = None
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from serial port: {e}")
    
    def _parse_serial_data(self, line: str) -> Optional[List[SensorReading]]:
        """Parse serial data line into sensor readings."""
        try:
            # Expected format: "temp:22.5,humidity:45.2,light:800"
            # or JSON format: {"temperature": 22.5, "humidity": 45.2}
            
            readings = []
            
            if line.strip().startswith('{'):
                # JSON format
                import json
                data = json.loads(line.strip())
                for key, value in data.items():
                    reading = SensorReading(
                        sensor_type=key,
                        value=float(value),
                        unit=self._get_unit_for_sensor(key),
                        timestamp=datetime.now()
                    )
                    readings.append(reading)
            else:
                # CSV format
                parts = line.strip().split(',')
                for part in parts:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        reading = SensorReading(
                            sensor_type=key.strip(),
                            value=float(value.strip()),
                            unit=self._get_unit_for_sensor(key.strip()),
                            timestamp=datetime.now()
                        )
                        readings.append(reading)
            
            return readings if readings else None
            
        except Exception as e:
            self.logger.error(f"Error parsing serial data '{line}': {e}")
            return None
    
    def _get_unit_for_sensor(self, sensor_type: str) -> str:
        """Get appropriate unit for sensor type."""
        units = {
            'temperature': '°C',
            'humidity': '%',
            'light': 'lux',
            'ph': 'pH',
            'moisture': '%',
            'pressure': 'hPa',
            'co2': 'ppm'
        }
        return units.get(sensor_type.lower(), '')
    
    def _generate_mock_readings(self) -> List[SensorReading]:
        """Generate mock sensor readings for simulation."""
        readings = []
        
        for sensor_type, state in self.mock_sensors.items():
            # Apply random variation
            trend = state['trend']
            variation = random.uniform(-trend, trend)
            state['value'] += variation
            
            # Apply realistic bounds
            if sensor_type == 'temperature':
                state['value'] = max(-10, min(50, state['value']))
            elif sensor_type == 'humidity':
                state['value'] = max(0, min(100, state['value']))
            elif sensor_type == 'light':
                state['value'] = max(0, min(2000, state['value']))
            elif sensor_type == 'ph':
                state['value'] = max(0, min(14, state['value']))
            elif sensor_type == 'moisture':
                state['value'] = max(0, min(100, state['value']))
            
            reading = SensorReading(
                sensor_type=sensor_type,
                value=round(state['value'], 2),
                unit=state['unit'],
                timestamp=datetime.now(),
                quality='simulated'
            )
            readings.append(reading)
        
        return readings
    
    async def start_data_collection(self) -> None:
        """Start collecting sensor data."""
        if not self.connected:
            await self.connect()
        
        if not self.connected:
            raise RuntimeError("Not connected to any data source")
        
        self.logger.info("Starting sensor data collection")
        
        if self.simulation_active:
            # Start simulation task
            self.simulation_task = asyncio.create_task(self._simulation_loop())
        else:
            # Start real serial reading task
            asyncio.create_task(self._serial_read_loop())
    
    async def _serial_read_loop(self) -> None:
        """Read data from serial port continuously."""
        while self.connected and self.serial_connection:
            try:
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode().strip()
                    if line:
                        readings = self._parse_serial_data(line)
                        if readings:
                            sensor_data = SensorData(
                                client_id=self.config.client_id,
                                readings=readings,
                                device_info={'port': self.active_port}
                            )
                            self.readings_collected += len(readings)
                            self.last_reading_time = datetime.now()
                            self._notify_data(sensor_data)
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy loop
                
            except Exception as e:
                self.errors_count += 1
                self.logger.error(f"Error reading from serial port: {e}")
                self._notify_error("serial_read", e)
                await asyncio.sleep(1)  # Wait before retrying
    
    async def _simulation_loop(self) -> None:
        """Generate simulated sensor data continuously."""
        while self.connected and self.simulation_active:
            try:
                readings = self._generate_mock_readings()
                sensor_data = SensorData(
                    client_id=self.config.client_id,
                    readings=readings,
                    device_info={'mode': 'simulation', 'platform': platform.system()}
                )
                
                self.readings_collected += len(readings)
                self.last_reading_time = datetime.now()
                self._notify_data(sensor_data)
                
                # Wait for next collection interval
                await asyncio.sleep(self.config.sensor.collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.errors_count += 1
                self.logger.error(f"Error in simulation loop: {e}")
                self._notify_error("simulation", e)
                await asyncio.sleep(1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            'connected': self.connected,
            'active_port': self.active_port,
            'simulation_active': self.simulation_active,
            'readings_collected': self.readings_collected,
            'errors_count': self.errors_count,
            'last_reading_time': self.last_reading_time.isoformat() if self.last_reading_time else None
        }
