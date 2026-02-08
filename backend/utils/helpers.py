"""
Helper utility functions
"""
import os
from pathlib import Path
from typing import List
import pandas as pd
from datetime import datetime, timedelta

def ensure_dir(directory: str) -> Path:
    """
    Create directory if it doesn't exist
    
    Args:
        directory: Directory path
        
    Returns:
        Path object
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def get_date_range(days: int = 365) -> tuple:
    """
    Get start and end date for data fetching
    
    Args:
        days: Number of days in the past
        
    Returns:
        Tuple of (start_date, end_date)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

def save_dataframe(df: pd.DataFrame, filepath: str, format: str = 'parquet'):
    """
    Save dataframe to file
    
    Args:
        df: Pandas DataFrame
        filepath: Output file path
        format: File format (parquet, csv)
    """
    ensure_dir(os.path.dirname(filepath))
    
    if format == 'parquet':
        df.to_parquet(filepath, index=False)
    elif format == 'csv':
        df.to_csv(filepath, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")

def load_dataframe(filepath: str, format: str = 'parquet') -> pd.DataFrame:
    """
    Load dataframe from file
    
    Args:
        filepath: Input file path
        format: File format (parquet, csv)
        
    Returns:
        Pandas DataFrame
    """
    if format == 'parquet':
        return pd.read_parquet(filepath)
    elif format == 'csv':
        return pd.read_csv(filepath)
    else:
        raise ValueError(f"Unsupported format: {format}")

def normalize_score(value: float, min_val: float, max_val: float) -> float:
    """
    Normalize value to 0-1 range
    
    Args:
        value: Value to normalize
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Normalized value
    """
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)