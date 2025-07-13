#!/usr/bin/env python3
"""
AgriNex Sensor Client - 支持动态设备管理的版本

A modular and robust sensor data collection system for agricultural monitoring
with dynamic device simulation capabilities.
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
from src.managers.simple_device_manager import SimpleDynamicDeviceManager
from src.utils.log_utils import setup_logging


class DynamicSensorClientApplication:
    """动态传感器客户端应用"""
    
    def __init__(self):
        self.device_manager: Optional[SimpleDynamicDeviceManager] = None
        self.running = False
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}, shutting down gracefully...")
            self.running = False
            if self.device_manager:
                asyncio.create_task(self.device_manager.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self, config: Config):
        """Run the dynamic sensor client application."""
        logger = logging.getLogger(__name__)
        
        try:
            # Setup logging
            setup_logging(config.logging)
            
            logger.info("=== AgriNex Dynamic Sensor Client v2.1 ===")
            logger.info(f"Client ID: {config.client_id}")
            logger.info(f"MQTT Broker: {config.mqtt.host}:{config.mqtt.port}")
            
            # Initialize device manager
            self.device_manager = SimpleDynamicDeviceManager(config)
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Start device manager
            await self.device_manager.start()
            
            logger.info("Dynamic sensor client started successfully")
            logger.info("Listening for device management commands on 'simulation/control'")
            
            # Keep the application running
            self.running = True
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Application error: {e}")
            raise
        finally:
            # Cleanup
            if self.device_manager:
                await self.device_manager.stop()
            
            logger.info("Dynamic sensor client stopped")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AgriNex Dynamic Sensor Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_dynamic.py                    # Run with default configuration
  python main_dynamic.py --config custom.yaml  # Use custom configuration
  python main_dynamic.py --device-count 5      # Start with 5 default devices
        """
    )
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/default.yaml",
        help="Configuration file path (default: config/default.yaml)"
    )
    
    parser.add_argument(
        "--device-count",
        type=int,
        help="Number of default devices to start (overrides config)"
    )
    
    parser.add_argument(
        "--mqtt-host",
        type=str,
        help="MQTT broker host (overrides config)"
    )
    
    parser.add_argument(
        "--mqtt-port",
        type=int,
        help="MQTT broker port (overrides config)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (overrides config)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Load configuration
        try:
            config = Config.from_file(args.config)
        except:
            # Fallback to environment variables and defaults
            config = Config.from_env()
        
        # Apply command line overrides
        if args.device_count is not None:
            import os
            os.environ['DEVICE_COUNT'] = str(args.device_count)
        
        if args.mqtt_host:
            config.mqtt.host = args.mqtt_host
        
        if args.mqtt_port:
            config.mqtt.port = args.mqtt_port
        
        if args.log_level:
            config.logging.level = args.log_level
        
        # Create and run application
        app = DynamicSensorClientApplication()
        asyncio.run(app.run(config))
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
