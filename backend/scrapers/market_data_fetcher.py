"""
Market data fetcher using yfinance
"""
from typing import List, Dict, Optional
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from backend.utils import log, load_config, ensure_dir, save_dataframe
import time

class MarketDataFetcher:
    """
    Fetch OHLCV market data for stocks
    """
    
    def __init__(self):
        """Initialize market data fetcher"""
        self.config = load_config()
        self.market_config = self.config['data_sources']['market_data']
        log.info("Market data fetcher initialized")
    
    def fetch_stock_data(
        self,
        symbol: str,
        period: str = None,
        interval: str = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for a single stock
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            period: Period to fetch (e.g., '1y', '6mo')
            interval: Data interval (e.g., '1d', '1h')
            
        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            # Use config defaults if not provided
            if not period:
                days = self.market_config['history_days']
                period = f"{days}d"
            if not interval:
                interval = self.market_config['interval']
            
            log.info(f"Fetching data for {symbol} (period={period}, interval={interval})")
            
            # Download data
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                log.warning(f"No data found for {symbol}")
                return None
            
            # Add symbol column
            df['symbol'] = symbol
            
            # Reset index to make Date a column
            df.reset_index(inplace=True)
            
            log.info(f"Fetched {len(df)} rows for {symbol}")
            return df
            
        except Exception as e:
            log.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def fetch_multiple_stocks(
        self,
        symbols: List[str],
        period: str = None,
        interval: str = None
    ) -> pd.DataFrame:
        """
        Fetch data for multiple stocks
        
        Args:
            symbols: List of stock symbols
            period: Period to fetch
            interval: Data interval
            
        Returns:
            Combined DataFrame
        """
        log.info(f"Fetching data for {len(symbols)} stocks")
        
        all_data = []
        
        for symbol in symbols:
            df = self.fetch_stock_data(symbol, period, interval)
            if df is not None:
                all_data.append(df)
        
        if not all_data:
            log.error("No data fetched for any stock")
            return pd.DataFrame()
        
        # Combine all dataframes
        combined_df = pd.concat(all_data, ignore_index=True)
        
        log.info(f"Combined data shape: {combined_df.shape}")
        return combined_df
    
    def fetch_benchmark_data(
        self,
        period: str = None,
        interval: str = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch benchmark index data (Nifty 50)
        
        Args:
            period: Period to fetch
            interval: Data interval
            
        Returns:
            DataFrame with benchmark data
        """
        benchmark = self.market_config['benchmark']
        log.info(f"Fetching benchmark data for {benchmark}")
        
        return self.fetch_stock_data(benchmark, period, interval)
    
    def save_market_data(self, df: pd.DataFrame, filename: str = "market_data.parquet"):
        """
        Save market data to file
        
        Args:
            df: DataFrame to save
            filename: Output filename
        """
        if df.empty:
            log.warning("Cannot save empty DataFrame")
            return
        
        filepath = f"{self.config['paths']['data_raw']}/{filename}"
        save_dataframe(df, filepath, format='parquet')
        log.info(f"Saved market data to {filepath}")