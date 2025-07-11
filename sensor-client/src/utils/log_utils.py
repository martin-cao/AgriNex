"""
Logging utilities for the sensor client.
"""

import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.config import LoggingConfig


def setup_logging(config) -> logging.Logger:
    """Setup logging configuration."""
    
    # Create formatter
    formatter = logging.Formatter(config.format)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, config.level.upper()))
    root_logger.addHandler(console_handler)
    
    # File handler (if configured)
    if config.file_path:
        log_path = Path(config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            config.file_path,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, config.level.upper()))
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)
