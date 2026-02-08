"""
Configuration loader utility
"""
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: str = "backend/configs/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config

def get_stock_symbols() -> list:
    """
    Get list of stock symbols from config
    
    Returns:
        List of stock symbols
    """
    config = load_config()
    return config['stocks']['symbols']

def get_data_sources() -> Dict[str, Any]:
    """
    Get data sources configuration
    
    Returns:
        Data sources config
    """
    config = load_config()
    return config['data_sources']