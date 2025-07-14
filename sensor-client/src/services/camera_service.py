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
from ..adapters.camera_adapter import CameraAdapter
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
            self.logger.error(f"Error handling control command: {e}")\n    \n    async def _send_camera_data(self, camera_data: Dict[str, Any]):\n        \"\"\"Send camera data via MQTT.\"\"\"\n        try:\n            # Send to appropriate topic based on data type\n            data_type = camera_data.get('type', 'unknown')\n            sensor_id = camera_data.get('sensor_id', 'camera_001')\n            topic = f\"sensors/{sensor_id}/{data_type}\"\n            \n            await self.mqtt_adapter.send_data(topic, camera_data)\n            \n            self.total_transmissions += 1\n            self.logger.debug(f\"Sent {data_type} data to {topic}\")\n            \n        except Exception as e:\n            self.error_count += 1\n            self.logger.error(f\"Error sending camera data: {e}\")\n    \n    async def _automatic_capture_loop(self):\n        \"\"\"Automatic capture loop.\"\"\"\n        self.logger.info(f\"Starting automatic {self.capture_type} capture every {self.capture_interval}s\")\n        \n        try:\n            while self.running and self.auto_capture:\n                try:\n                    if self.capture_type == 'image':\n                        await self.camera_adapter.capture_image()\n                    elif self.capture_type == 'video':\n                        await self.camera_adapter.capture_video(duration=self.video_duration)\n                    \n                    await asyncio.sleep(self.capture_interval)\n                    \n                except asyncio.CancelledError:\n                    self.logger.info(\"Automatic capture cancelled\")\n                    break\n                except Exception as e:\n                    self.logger.error(f\"Error in automatic capture: {e}\")\n                    await asyncio.sleep(5)  # Wait before retry\n                    \n        except Exception as e:\n            self.logger.error(f\"Error in automatic capture loop: {e}\")\n    \n    async def start(self):\n        \"\"\"Start the camera sensor service.\"\"\"\n        try:\n            self.logger.info(\"Starting camera sensor service...\")\n            \n            # Initialize adapters\n            await self.mqtt_adapter.initialize()\n            await self.camera_adapter.initialize()\n            \n            # Start HTTP health service\n            await self.http_service.start()\n            \n            # Set running state\n            self.running = True\n            self.start_time = datetime.now()\n            \n            # Subscribe to control topic\n            client_id = getattr(self.config, 'client_id', 'camera_001')\n            control_topic = f\"sensors/{client_id}/control\"\n            await self.mqtt_adapter.subscribe(control_topic)\n            \n            # Start automatic capture if enabled\n            if self.auto_capture:\n                self.capture_task = asyncio.create_task(self._automatic_capture_loop())\n            \n            self.logger.info(\"Camera sensor service started successfully\")\n            \n            # Keep service running\n            while self.running:\n                await asyncio.sleep(1)\n                \n        except Exception as e:\n            self.logger.error(f\"Error starting camera sensor service: {e}\")\n            raise\n    \n    async def stop(self):\n        \"\"\"Stop the camera sensor service.\"\"\"\n        try:\n            self.logger.info(\"Stopping camera sensor service...\")\n            \n            self.running = False\n            \n            # Cancel automatic capture\n            if self.capture_task and not self.capture_task.done():\n                self.capture_task.cancel()\n                try:\n                    await self.capture_task\n                except asyncio.CancelledError:\n                    pass\n            \n            # Stop HTTP service\n            if self.http_service:\n                await self.http_service.stop()\n            \n            # Cleanup adapters\n            await self.camera_adapter.cleanup()\n            await self.mqtt_adapter.cleanup()\n            \n            self.logger.info(\"Camera sensor service stopped\")\n            \n        except Exception as e:\n            self.logger.error(f\"Error stopping camera sensor service: {e}\")\n    \n    # Manual capture methods\n    async def capture_image_now(self) -> Optional[Dict[str, Any]]:\n        \"\"\"Manually trigger image capture.\"\"\"\n        return await self.camera_adapter.capture_image()\n    \n    async def capture_video_now(self, duration: Optional[int] = None) -> Optional[Dict[str, Any]]:\n        \"\"\"Manually trigger video capture.\"\"\"\n        return await self.camera_adapter.capture_video(duration=duration)\n    \n    def get_status(self) -> Dict[str, Any]:\n        \"\"\"Get service status.\"\"\"\n        uptime = None\n        if self.start_time:\n            uptime = (datetime.now() - self.start_time).total_seconds()\n        \n        camera_stats = self.camera_adapter.get_statistics()\n        mqtt_stats = self.mqtt_adapter.get_statistics() if hasattr(self.mqtt_adapter, 'get_statistics') else {}\n        \n        return {\n            'service_name': 'camera_sensor_service',\n            'running': self.running,\n            'uptime_seconds': uptime,\n            'start_time': self.start_time.isoformat() if self.start_time else None,\n            'configuration': {\n                'capture_interval': self.capture_interval,\n                'capture_type': self.capture_type,\n                'video_duration': self.video_duration,\n                'auto_capture': self.auto_capture\n            },\n            'statistics': {\n                'total_captures': self.total_captures,\n                'total_transmissions': self.total_transmissions,\n                'error_count': self.error_count\n            },\n            'camera_adapter': camera_stats,\n            'mqtt_adapter': mqtt_stats\n        }"
