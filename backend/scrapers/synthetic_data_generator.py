"""
Synthetic market data generator for testing and development
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List
from backend.utils import log

class SyntheticDataGenerator:
    """
    Generate realistic synthetic market data for testing
    """
    
    def __init__(self, seed: int = 42):
        """Initialize generator with random seed for reproducibility"""
        np.random.seed(seed)
        self.seed = seed
        log.info("Synthetic data generator initialized")
    
    def generate_stock_data(
        self,
        symbol: str,
        days: int = 365,
        initial_price: float = 100.0,
        volatility: float = 0.02,
        trend: float = 0.0005
    ) -> pd.DataFrame:
        """
        Generate synthetic OHLCV data for a stock
        
        Args:
            symbol: Stock symbol
            days: Number of days to generate
            initial_price: Starting price
            volatility: Daily volatility (std dev of returns)
            trend: Daily trend (mean return)
            
        Returns:
            DataFrame with OHLCV data
        """
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        # Generate returns using geometric Brownian motion
        returns = np.random.normal(trend, volatility, days)
        
        # Calculate prices
        price_series = initial_price * np.exp(np.cumsum(returns))
        
        # Generate OHLC from close prices
        data = []
        for i, date in enumerate(dates):
            close = price_series[i]
            
            # High is close + random positive value
            high = close * (1 + abs(np.random.normal(0, volatility/2)))
            
            # Low is close - random positive value
            low = close * (1 - abs(np.random.normal(0, volatility/2)))
            
            # Open is between high and low
            open_price = np.random.uniform(low, high)
            
            # Volume with some randomness
            base_volume = 10_000_000
            volume = int(base_volume * (1 + np.random.uniform(-0.3, 0.3)))
            
            data.append({
                'Date': date,
                'Open': open_price,
                'High': high,
                'Low': low,
                'Close': close,
                'Volume': volume,
                'Dividends': 0.0,
                'Stock Splits': 0.0,
                'symbol': symbol
            })
        
        df = pd.DataFrame(data)
        log.info(f"Generated {len(df)} rows of synthetic data for {symbol}")
        return df
    
    def generate_multiple_stocks(
        self,
        symbols: List[str],
        days: int = 365
    ) -> pd.DataFrame:
        """
        Generate data for multiple stocks with varying characteristics
        
        Args:
            symbols: List of stock symbols
            days: Number of days
            
        Returns:
            Combined DataFrame
        """
        log.info(f"Generating synthetic data for {len(symbols)} stocks")
        
        all_data = []
        
        for i, symbol in enumerate(symbols):
            # Vary parameters for different stocks
            initial_price = np.random.uniform(50, 500)
            volatility = np.random.uniform(0.01, 0.04)
            trend = np.random.uniform(-0.001, 0.002)
            
            df = self.generate_stock_data(
                symbol=symbol,
                days=days,
                initial_price=initial_price,
                volatility=volatility,
                trend=trend
            )
            all_data.append(df)
        
        combined_df = pd.concat(all_data, ignore_index=True)
        log.info(f"Generated total {len(combined_df)} rows for all stocks")
        
        return combined_df
    
    def generate_benchmark_data(
        self,
        symbol: str = "^GSPC",
        days: int = 365
    ) -> pd.DataFrame:
        """
        Generate benchmark index data
        
        Args:
            symbol: Benchmark symbol
            days: Number of days
            
        Returns:
            DataFrame with benchmark data
        """
        # Benchmark has lower volatility and positive trend
        return self.generate_stock_data(
            symbol=symbol,
            days=days,
            initial_price=4500.0,
            volatility=0.01,
            trend=0.0003
        )