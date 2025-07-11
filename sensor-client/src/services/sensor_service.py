"""
Main sensor service orchestrating data collection and transmission.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from ..core.config import Config
from ..core.sensor_data import SensorData
from ..adapters.mqtt_adapter import MQTTAdapter
from ..adapters.serial_adapter import SerialAdapter


class SensorService:
    """Main service for sensor data collection and transmission."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Adapters
        self.mqtt_adapter = MQTTAdapter(config)
        self.serial_adapter = SerialAdapter(config)
        
        # Service state
        self.running = False
        self.start_time: Optional[datetime] = None
        
        # Statistics
        self.total_readings = 0
        self.total_transmissions = 0
        self.error_count = 0
        
        # Setup callbacks
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Setup adapter callbacks."""
        # Serial data callback
        self.serial_adapter.add_data_callback(self._on_sensor_data)
        self.serial_adapter.add_error_callback(self._on_serial_error)
        
        # MQTT connection callback
        self.mqtt_adapter.add_connection_callback(self._on_mqtt_connection)
        self.mqtt_adapter.add_message_callback(self._on_mqtt_message)
    
    def _on_sensor_data(self, sensor_data: SensorData):
        """Handle new sensor data."""
        try:
            self.total_readings += len(sensor_data.readings)
            self.logger.debug(f"Received {len(sensor_data.readings)} sensor readings")
            
            # Send data via MQTT
            asyncio.create_task(self._send_data(sensor_data))
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Error handling sensor data: {e}")
    
    def _on_serial_error(self, context: str, error: Exception):
        """Handle serial adapter errors."""
        self.error_count += 1
        self.logger.error(f"Serial error in {context}: {error}")
        
        # Send error information via MQTT
        error_info = {
            'context': context,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        }
        asyncio.create_task(self.mqtt_adapter.send_error(error_info))
    
    def _on_mqtt_connection(self, connected: bool):
        """Handle MQTT connection state changes."""
        if connected:
            self.logger.info("MQTT connected - ready to transmit data")
        else:
            self.logger.warning("MQTT disconnected - data transmission paused")
    
    def _on_mqtt_message(self, topic: str, payload: Dict[str, Any]):
        """Handle incoming MQTT messages."""
        try:
            self.logger.info(f"Received command on {topic}: {payload}")
            
            # Handle control commands
            if topic.endswith('/control'):
                asyncio.create_task(self._handle_control_command(payload))
                
        except Exception as e:
            self.logger.error(f"Error handling MQTT message: {e}")
    
    async def _handle_control_command(self, command: Dict[str, Any]):
        """Handle control commands from MQTT."""
        try:
            cmd_type = command.get('type')
            
            if cmd_type == 'restart_collection':
                await self.restart_data_collection()
            elif cmd_type == 'get_status':
                await self.send_status()
            elif cmd_type == 'update_config':
                await self._update_config(command.get('config', {}))
            else:
                self.logger.warning(f"Unknown command type: {cmd_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling control command: {e}")
    
    async def _update_config(self, new_config: Dict[str, Any]):
        """Update configuration dynamically."""
        try:
            # Update collection interval
            if 'collection_interval' in new_config:
                self.config.sensor.collection_interval = float(new_config['collection_interval'])
                self.logger.info(f"Updated collection interval to {self.config.sensor.collection_interval}s")
            
            # Update MQTT settings
            if 'mqtt' in new_config:
                mqtt_config = new_config['mqtt']
                if 'qos' in mqtt_config:
                    self.config.mqtt.qos = int(mqtt_config['qos'])
                    self.logger.info(f"Updated MQTT QoS to {self.config.mqtt.qos}")
            
            # Send confirmation
            await self.mqtt_adapter.send_status({
                'message': 'Configuration updated successfully',
                'new_config': new_config
            })
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
    
    async def _send_data(self, sensor_data: SensorData):
        """Send sensor data via MQTT."""
        try:
            success = await self.mqtt_adapter.send_sensor_data(sensor_data)
            if success:
                self.total_transmissions += 1
                self.logger.debug("Data transmitted successfully")
            else:
                self.error_count += 1
                self.logger.warning("Failed to transmit data")
                
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Error sending data: {e}")
    
    async def start(self):
        """Start the sensor service."""
        try:
            self.logger.info("Starting AgriNex Sensor Service")
            self.start_time = datetime.now()
            self.running = True
            
            # Connect to MQTT
            self.logger.info("Connecting to MQTT broker...")
            mqtt_connected = await self.mqtt_adapter.connect()
            if not mqtt_connected:
                raise RuntimeError("Failed to connect to MQTT broker")
            
            # Connect to serial port and start data collection
            self.logger.info("Starting sensor data collection...")
            await self.serial_adapter.start_data_collection()
            
            # Send initial status
            await self.send_status()
            
            # Start periodic status updates
            asyncio.create_task(self._periodic_status_task())
            
            self.logger.info("Sensor service started successfully")
            
            # Keep the service running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error starting sensor service: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the sensor service."""
        try:
            self.logger.info("Stopping sensor service...")
            self.running = False
            
            # Disconnect adapters
            self.serial_adapter.disconnect()
            self.mqtt_adapter.disconnect()
            
            self.logger.info("Sensor service stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping sensor service: {e}")
    
    async def restart_data_collection(self):
        """Restart data collection."""
        try:
            self.logger.info("Restarting data collection...")
            
            # Disconnect and reconnect serial
            self.serial_adapter.disconnect()
            await asyncio.sleep(1)
            await self.serial_adapter.start_data_collection()
            
            await self.mqtt_adapter.send_status({
                'message': 'Data collection restarted'
            })
            
        except Exception as e:
            self.logger.error(f"Error restarting data collection: {e}")
    
    async def send_status(self):
        """Send current service status."""
        try:
            uptime = None
            if self.start_time:
                uptime = str(datetime.now() - self.start_time)
            
            status = {
                'service': {
                    'running': self.running,
                    'start_time': self.start_time.isoformat() if self.start_time else None,
                    'uptime': uptime,
                    'total_readings': self.total_readings,
                    'total_transmissions': self.total_transmissions,
                    'error_count': self.error_count
                },
                'mqtt': self.mqtt_adapter.get_stats(),
                'serial': self.serial_adapter.get_stats(),
                'config': {
                    'client_id': self.config.client_id,
                    'collection_interval': self.config.sensor.collection_interval,
                    'simulation_mode': self.config.serial.simulation_mode
                }
            }
            
            await self.mqtt_adapter.send_status(status)
            
        except Exception as e:
            self.logger.error(f"Error sending status: {e}")
    
    async def _periodic_status_task(self):
        """Send periodic status updates."""
        while self.running:
            try:
                await asyncio.sleep(300)  # Send status every 5 minutes
                if self.running:
                    await self.send_status()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in periodic status task: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics."""
        uptime = None
        if self.start_time:
            uptime = str(datetime.now() - self.start_time)
        
        return {
            'service': {
                'running': self.running,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'uptime': uptime,
                'total_readings': self.total_readings,
                'total_transmissions': self.total_transmissions,
                'error_count': self.error_count
            },
            'adapters': {
                'mqtt': self.mqtt_adapter.get_stats(),
                'serial': self.serial_adapter.get_stats()
            },
            'config': self.config.to_dict()
        }
