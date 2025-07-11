#!/usr/bin/env python3
"""
AgriNex Sensor Client - Main Entry Point

A modular and robust sensor data collection system for agricultural monitoring.
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
from src.services.sensor_service import SensorService
from src.utils.log_utils import setup_logging


class SensorClientApplication:
    """Main application controller."""
    
    def __init__(self):
        self.service: Optional[SensorService] = None
        self.running = False
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}, shutting down gracefully...")
            self.running = False
            if self.service:
                asyncio.create_task(self.service.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self, config: Config):
        """Run the sensor client application."""
        logger = logging.getLogger(__name__)
        
        try:
            # Setup logging
            setup_logging(config.logging)
            
            logger.info("=== AgriNex Sensor Client v2.0 ===")
            logger.info(f"Client ID: {config.client_id}")
            logger.info(f"MQTT Broker: {config.mqtt.host}:{config.mqtt.port}")
            logger.info(f"Simulation Mode: {config.serial.simulation_mode}")
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Create and start service
            self.service = SensorService(config)
            self.running = True
            
            # Start the service
            await self.service.start()
            
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
            raise
        finally:
            if self.service:
                await self.service.stop()
            logger.info("Application shutdown complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AgriNex Sensor Client - Agricultural Sensor Data Collection"
    )
    
    # Configuration options
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config/sensor_client.json",
        help="Configuration file path (default: config/sensor_client.json)"
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
        help="Force simulation mode"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--collection-interval",
        type=float,
        help="Sensor data collection interval in seconds"
    )
    
    # Environment mode
    parser.add_argument(
        "--env-config",
        action="store_true",
        help="Load configuration from environment variables"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        if args.env_config:
            config = Config.from_env()
        else:
            config = Config.from_file(args.config)
        
        # Override with command line arguments
        if args.client_id:
            config.client_id = args.client_id
        
        if args.mqtt_host:
            config.mqtt.host = args.mqtt_host
        
        if args.mqtt_port:
            config.mqtt.port = args.mqtt_port
        
        if args.simulation:
            config.serial.simulation_mode = True
        
        if args.debug:
            config.debug = True
            config.logging.level = "DEBUG"
        
        if args.collection_interval:
            config.sensor.collection_interval = args.collection_interval
        
        # Setup logging path
        if not config.logging.file_path:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            config.logging.file_path = str(log_dir / "sensor_client.log")
        
        # Run the application
        app = SensorClientApplication()
        asyncio.run(app.run(config))
        
    except KeyboardInterrupt:
        print("\nApplication interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
