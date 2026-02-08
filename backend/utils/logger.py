"""
Logging utility using loguru
"""
from loguru import logger
import sys
from pathlib import Path
from backend.utils.config_loader import load_config

def setup_logger():
    """
    Configure logger with file and console output
    """
    config = load_config()
    log_config = config['logging']
    
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stdout,
        format=log_config['format'],
        level=log_config['level'],
        colorize=True
    )
    
    # Create logs directory if it doesn't exist
    log_dir = Path(config['paths']['logs'])
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Add file logger
    logger.add(
        log_config['log_file'],
        format=log_config['format'],
        level=log_config['level'],
        rotation=log_config['rotation'],
        retention=log_config['retention'],
        compression="zip"
    )
    
    logger.info("Logger initialized successfully")
    return logger

# Initialize logger
log = setup_logger()