#!/usr/bin/env python3
"""
Quick start script for AgriNex Sensor Client.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config import Config
from src.services.sensor_service import SensorService
from src.utils.log_utils import setup_logging
import asyncio
import logging


async def main():
    """Quick start with default configuration."""
    logger = logging.getLogger(__name__)
    
    try:
        # Load default configuration
        config = Config()
        config.client_id = "agrinex_quick_start"
        config.serial.simulation_mode = True
        config.sensor.collection_interval = 10.0
        config.debug = True
        config.logging.level = "DEBUG"
        
        # Setup logging
        setup_logging(config.logging)
        
        logger.info("=== AgriNex Sensor Client - Quick Start ===")
        logger.info("Starting with default configuration...")
        logger.info("Press Ctrl+C to stop")
        
        # Create and start service
        service = SensorService(config)
        await service.start()
        
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
