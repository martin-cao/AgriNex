#!/usr/bin/env python3
"""
AgriNex Camera Sensor Client - Image/Video Capture Service

A specialized sensor client for capturing images and videos from device camera.
专门用于从设备摄像头捕获图片和视频的传感器客户端。
"""

import asyncio
import argparse
import signal
import sys
import logging
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config import Config
from src.services.camera_service_new import CameraSensorService
from src.utils.log_utils import setup_logging


class CameraClientApplication:
    """Camera client application controller."""
    
    def __init__(self):
        self.service: Optional[CameraSensorService] = None
        self.running = False
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}, shutting down camera client...")
            self.running = False
            if self.service:
                asyncio.create_task(self.service.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self, config: Config):
        """Run the camera sensor client application."""
        logger = logging.getLogger(__name__)
        
        try:
            # Setup logging
            setup_logging(config.logging)
            
            logger.info("=== AgriNex Camera Sensor Client v1.0 ===")
            logger.info(f"Client ID: {config.client_id}")
            logger.info(f"MQTT Broker: {config.mqtt.host}:{config.mqtt.port}")
            logger.info(f"Simulation Mode: {getattr(config, 'simulation_mode', False)}")
            logger.info(f"Capture Type: {getattr(config, 'capture_type', 'image')}")
            logger.info(f"Capture Interval: {getattr(config, 'capture_interval', 60)}s")
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Create and start service
            self.service = CameraSensorService(config)
            self.running = True
            
            # Start the service
            await self.service.start()
            
        except KeyboardInterrupt:
            logger.info("Camera client interrupted by user")
        except Exception as e:
            logger.error(f"Camera client error: {e}")
            raise
        finally:
            if self.service:
                await self.service.stop()
            logger.info("Camera client shutdown complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AgriNex Camera Sensor Client - Image/Video Capture Service"
    )
    
    # Configuration options
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config/camera_client.json",
        help="Configuration file path (default: config/camera_client.json)"
    )
    
    parser.add_argument(
        "--client-id",
        type=str,
        help="Override client ID"
    )
    
    parser.add_argument(
        "--mqtt-host",
        type=str,
        help="MQTT broker host"
    )
    
    parser.add_argument(
        "--mqtt-port",
        type=int,
        help="MQTT broker port"
    )
    
    parser.add_argument(
        "--simulation",
        action="store_true",
        help="Enable simulation mode (no real camera)"
    )
    
    parser.add_argument(
        "--capture-type",
        choices=["image", "video"],
        help="Type of capture (image or video)"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        help="Capture interval in seconds"
    )
    
    parser.add_argument(
        "--no-auto-capture",
        action="store_true",
        help="Disable automatic capture"
    )
    
    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="Camera device index (default: 0)"
    )
    
    parser.add_argument(
        "--video-duration",
        type=int,
        help="Video capture duration in seconds"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config_path = Path(args.config)
        if config_path.exists():
            config = Config.from_file(str(config_path))
        else:
            # Use default config if file doesn't exist
            print(f"Config file {config_path} not found, using default config...")
            config = Config()
        
        # Apply command line overrides
        if args.client_id:
            config.client_id = args.client_id
        
        if args.mqtt_host:
            config.mqtt.host = args.mqtt_host
            
        if args.mqtt_port:
            config.mqtt.port = args.mqtt_port
        
        # Set log level
        config.logging.level = args.log_level
        
        # Add camera-specific attributes to config dynamically using setattr
        setattr(config, 'simulation_mode', args.simulation or getattr(config, 'simulation_mode', False))
        setattr(config, 'capture_type', args.capture_type or getattr(config, 'capture_type', 'image'))
        setattr(config, 'capture_interval', args.interval or getattr(config, 'capture_interval', 60))
        setattr(config, 'auto_capture', not args.no_auto_capture and getattr(config, 'auto_capture', True))
        setattr(config, 'camera_index', args.camera_index if args.camera_index is not None else getattr(config, 'camera_index', 0))
        setattr(config, 'video_duration', args.video_duration or getattr(config, 'video_duration', 10))
        
        # Create and run application
        app = CameraClientApplication()
        asyncio.run(app.run(config))
        
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
