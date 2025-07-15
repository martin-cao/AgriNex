"""
Camera sensor service for capturing and transmitting images/videos.
摄像头传感器服务，用于捕获和传输图片/视频。
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from ..core.config import Config
from ..adapters.mqtt_adapter import MQTTAdapter
from ..adapters.camera_adapter_simple import CameraAdapter
from .http_service import HTTPHealthService


class CameraSensorService:
    """Camera sensor service for image and video capture."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Adapters
        self.mqtt_adapter = MQTTAdapter(config)
        self.camera_adapter = CameraAdapter(config)
        
        # HTTP Health Service
        self.http_service = HTTPHealthService(self, port=8081)
        
        # Service state
        self.running = False
        self.start_time: Optional[datetime] = None
        
        # Configuration
        self.capture_interval = getattr(config, 'capture_interval', 60)  # seconds
        self.capture_type = getattr(config, 'capture_type', 'image')  # 'image' or 'video'
        self.video_duration = getattr(config, 'video_duration', 10)  # seconds for video
        self.auto_capture = getattr(config, 'auto_capture', True)  # automatic capture
        
        # Statistics
        self.total_captures = 0
        self.total_transmissions = 0
        self.error_count = 0
        
        # Background tasks
        self.capture_task: Optional[asyncio.Task] = None
        
        # Setup callbacks
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Setup adapter callbacks."""
        # Camera data callback
        self.camera_adapter.add_data_callback(self._on_camera_data)
        self.camera_adapter.add_error_callback(self._on_camera_error)
        
        # MQTT connection callback
        self.mqtt_adapter.add_connection_callback(self._on_mqtt_connection)
        self.mqtt_adapter.add_message_callback(self._on_mqtt_message)
    
    def _on_camera_data(self, camera_data: Dict[str, Any]):
        """Handle new camera data."""
        try:
            self.total_captures += 1
            self.logger.debug(f"Received camera data: {camera_data['type']}")
            
            # Send data via MQTT
            asyncio.create_task(self._send_camera_data(camera_data))
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Error handling camera data: {e}")
    
    def _on_camera_error(self, context: str, error: Exception):
        """Handle camera adapter errors."""
        self.error_count += 1
        self.logger.error(f"Camera error in {context}: {error}")
        
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
            self.logger.info("MQTT connected - ready to transmit camera data")
        else:
            self.logger.warning("MQTT disconnected - camera data transmission paused")
    
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
            
            if cmd_type == 'capture_image':
                self.logger.info("Manual image capture requested")
                await self.camera_adapter.capture_image()
                
            elif cmd_type == 'capture_video':
                duration = command.get('duration', self.video_duration)
                self.logger.info(f"Manual video capture requested ({duration}s)")
                await self.camera_adapter.capture_video(duration=duration)
                
            elif cmd_type == 'start_auto_capture':
                self.logger.info("Starting automatic capture")
                self.auto_capture = True
                if not self.capture_task or self.capture_task.done():
                    self.capture_task = asyncio.create_task(self._automatic_capture_loop())
                    
            elif cmd_type == 'stop_auto_capture':
                self.logger.info("Stopping automatic capture")
                self.auto_capture = False
                if self.capture_task and not self.capture_task.done():
                    self.capture_task.cancel()
                    
            elif cmd_type == 'set_interval':
                interval = command.get('interval', self.capture_interval)
                self.logger.info(f"Setting capture interval to {interval}s")
                self.capture_interval = interval
                
            elif cmd_type == 'set_capture_type':
                capture_type = command.get('capture_type', 'image')
                if capture_type in ['image', 'video']:
                    self.logger.info(f"Setting capture type to {capture_type}")
                    self.capture_type = capture_type
                else:
                    self.logger.warning(f"Invalid capture type: {capture_type}")
                    
            else:
                self.logger.warning(f"Unknown command type: {cmd_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling control command: {e}")
    
    async def _send_camera_data(self, camera_data: Dict[str, Any]):
        """Send camera data via MQTT."""
        try:
            # Create a sensor data object
            from ..core.sensor_data import SensorData, SensorReading
            
            # Convert camera data to sensor readings format
            sensor_id = camera_data.get('sensor_id', 'camera_001')
            timestamp = datetime.fromisoformat(camera_data['timestamp'])
            data_type = camera_data.get('type', 'unknown')
            
            # Create reading based on data type
            if data_type == 'image':
                reading = SensorReading(
                    sensor_type='camera_image',
                    timestamp=timestamp,
                    value=1.0,  # Indicator that image was captured
                    unit='image',
                    metadata=camera_data
                )
            elif data_type == 'video':
                reading = SensorReading(
                    sensor_type='camera_video',
                    timestamp=timestamp,
                    value=camera_data['data']['duration_seconds'],
                    unit='seconds',
                    metadata=camera_data
                )
            else:
                reading = SensorReading(
                    sensor_type='camera_unknown',
                    timestamp=timestamp,
                    value=0.0,
                    unit='unknown',
                    metadata=camera_data
                )
            
            # Create sensor data object
            sensor_data = SensorData(
                client_id=self.config.client_id,
                readings=[reading],
                location=getattr(self.config, 'location', 'greenhouse_001')
            )
            
            # Send via MQTT
            success = await self.mqtt_adapter.send_sensor_data(sensor_data)
            
            if success:
                self.total_transmissions += 1
                self.logger.debug(f"Sent {data_type} data successfully")
            else:
                self.error_count += 1
                self.logger.error(f"Failed to send {data_type} data")
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Error sending camera data: {e}")
    
    async def _automatic_capture_loop(self):
        """Automatic capture loop."""
        self.logger.info(f"Starting automatic {self.capture_type} capture every {self.capture_interval}s")
        
        try:
            while self.running and self.auto_capture:
                try:
                    if self.capture_type == 'image':
                        await self.camera_adapter.capture_image()
                    elif self.capture_type == 'video':
                        await self.camera_adapter.capture_video(duration=self.video_duration)
                    
                    await asyncio.sleep(self.capture_interval)
                    
                except asyncio.CancelledError:
                    self.logger.info("Automatic capture cancelled")
                    break
                except Exception as e:
                    self.logger.error(f"Error in automatic capture: {e}")
                    await asyncio.sleep(5)  # Wait before retry
                    
        except Exception as e:
            self.logger.error(f"Error in automatic capture loop: {e}")
    
    async def start(self):
        """Start the camera sensor service."""
        try:
            self.logger.info("Starting camera sensor service...")
            
            # Initialize adapters
            await self.mqtt_adapter.connect()
            await self.camera_adapter.initialize()
            
            # Start HTTP health service
            await self.http_service.start()
            
            # Set running state
            self.running = True
            self.start_time = datetime.now()
            
            # Note: control topic subscription is handled in mqtt_adapter.connect()
            
            # Start automatic capture if enabled
            if self.auto_capture:
                self.capture_task = asyncio.create_task(self._automatic_capture_loop())
            
            self.logger.info("Camera sensor service started successfully")
            
            # Keep service running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error starting camera sensor service: {e}")
            raise
    
    async def stop(self):
        """Stop the camera sensor service."""
        try:
            self.logger.info("Stopping camera sensor service...")
            
            self.running = False
            
            # Cancel automatic capture
            if self.capture_task and not self.capture_task.done():
                self.capture_task.cancel()
                try:
                    await self.capture_task
                except asyncio.CancelledError:
                    pass
            
            # Stop HTTP service
            if self.http_service:
                await self.http_service.stop()
            
            # Cleanup adapters
            await self.camera_adapter.cleanup()
            self.mqtt_adapter.disconnect()
            
            self.logger.info("Camera sensor service stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping camera sensor service: {e}")
    
    # Manual capture methods
    async def capture_image_now(self) -> Optional[Dict[str, Any]]:
        """Manually trigger image capture."""
        return await self.camera_adapter.capture_image()
    
    async def capture_video_now(self, duration: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Manually trigger video capture."""
        return await self.camera_adapter.capture_video(duration=duration)
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        camera_stats = self.camera_adapter.get_statistics()
        
        return {
            'service_name': 'camera_sensor_service',
            'running': self.running,
            'uptime_seconds': uptime,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'configuration': {
                'capture_interval': self.capture_interval,
                'capture_type': self.capture_type,
                'video_duration': self.video_duration,
                'auto_capture': self.auto_capture
            },
            'statistics': {
                'total_captures': self.total_captures,
                'total_transmissions': self.total_transmissions,
                'error_count': self.error_count
            },
            'camera_adapter': camera_stats
        }
