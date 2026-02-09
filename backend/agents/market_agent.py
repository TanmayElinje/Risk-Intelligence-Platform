"""
Market Data Agent - Computes quantitative risk features
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
from backend.utils import log, load_config, load_dataframe, save_dataframe, ensure_dir

class MarketDataAgent:
    """
    Agent responsible for computing market-based risk features
    """
    
    def __init__(self):
        """Initialize Market Data Agent"""
        self.config = load_config()
        self.agent_config = self.config['agents']['market_data']
        self.features_config = self.agent_config['features']
        log.info("Market Data Agent initialized")
    
    def load_data(self) -> tuple:
        """
        Load market data and benchmark data
        
        Returns:
            Tuple of (stocks_df, benchmark_df)
        """
        log.info("Loading market data...")
        
        stocks_path = f"{self.config['paths']['data_raw']}/stocks_data.parquet"
        benchmark_path = f"{self.config['paths']['data_raw']}/benchmark_data.parquet"
        
        stocks_df = load_dataframe(stocks_path, format='parquet')
        benchmark_df = load_dataframe(benchmark_path, format='parquet')
        
        log.info(f"Loaded {len(stocks_df)} rows of stock data")
        log.info(f"Loaded {len(benchmark_df)} rows of benchmark data")
        
        return stocks_df, benchmark_df
    
    def compute_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute daily returns
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with returns column
        """
        df = df.copy()
        df = df.sort_values(['symbol', 'Date'])
        
        # Compute daily returns per symbol
        df['returns'] = df.groupby('symbol')['Close'].pct_change()
        
        # Handle inf and nan
        df['returns'] = df['returns'].replace([np.inf, -np.inf], np.nan)
        df['returns'] = df['returns'].fillna(0)
        
        log.info("✓ Computed daily returns")
        return df
    
    def compute_volatility(self, df: pd.DataFrame, windows: list = [21, 60]) -> pd.DataFrame:
        """
        Compute rolling volatility
        
        Args:
            df: DataFrame with returns
            windows: List of rolling window sizes
            
        Returns:
            DataFrame with volatility columns
        """
        df = df.copy()
        df = df.sort_values(['symbol', 'Date'])
        
        for window in windows:
            col_name = f'volatility_{window}d'
            
            # Rolling standard deviation of returns (annualized)
            df[col_name] = df.groupby('symbol')['returns'].transform(
                lambda x: x.rolling(window=window, min_periods=max(1, window//2)).std() * np.sqrt(252)
            )
            
            # Fill initial NaN values with overall volatility
            df[col_name] = df.groupby('symbol')[col_name].transform(
                lambda x: x.fillna(x.mean())
            )
        
        log.info(f"✓ Computed volatility for windows: {windows}")
        return df
    
    def compute_max_drawdown(self, df: pd.DataFrame, window: int = 252) -> pd.DataFrame:
        """
        Compute maximum drawdown over rolling window
        
        Args:
            df: DataFrame with Close prices
            window: Rolling window size
            
        Returns:
            DataFrame with max_drawdown column
        """
        df = df.copy()
        df = df.sort_values(['symbol', 'Date'])
        
        def rolling_max_drawdown(prices):
            """Calculate rolling max drawdown"""
            rolling_max = prices.rolling(window=window, min_periods=1).max()
            drawdown = (prices - rolling_max) / rolling_max
            return drawdown.rolling(window=window, min_periods=1).min()
        
        df['max_drawdown'] = df.groupby('symbol')['Close'].transform(rolling_max_drawdown)
        
        # Convert to positive percentage
        df['max_drawdown'] = abs(df['max_drawdown']) * 100
        
        log.info("✓ Computed maximum drawdown")
        return df
    
    def compute_beta(self, stocks_df: pd.DataFrame, benchmark_df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
        """
        Compute beta (correlation with market)
        
        Args:
            stocks_df: Stock data with returns
            benchmark_df: Benchmark data with returns
            window: Rolling window for beta calculation
            
        Returns:
            DataFrame with beta column
        """
        stocks_df = stocks_df.copy()
        
        # Compute benchmark returns if not present
        if 'returns' not in benchmark_df.columns:
            benchmark_df = benchmark_df.sort_values('Date')
            benchmark_df['returns'] = benchmark_df['Close'].pct_change()
            benchmark_df['returns'] = benchmark_df['returns'].replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Merge stock and benchmark returns on date
        merged = stocks_df.merge(
            benchmark_df[['Date', 'returns']].rename(columns={'returns': 'market_returns'}),
            on='Date',
            how='left'
        )
        
        def rolling_beta(group):
            """Calculate rolling beta for a stock"""
            betas = []
            for i in range(len(group)):
                start_idx = max(0, i - window + 1)
                window_data = group.iloc[start_idx:i+1]
                
                if len(window_data) < max(1, window//2):
                    betas.append(1.0)  # Default beta
                else:
                    stock_ret = window_data['returns'].values
                    market_ret = window_data['market_returns'].values
                    
                    # Covariance / Variance
                    covariance = np.cov(stock_ret, market_ret)[0, 1]
                    market_variance = np.var(market_ret)
                    
                    if market_variance > 0:
                        beta = covariance / market_variance
                    else:
                        beta = 1.0
                    
                    betas.append(beta)
            
            return betas
        
        merged = merged.sort_values(['symbol', 'Date'])
        merged['beta'] = merged.groupby('symbol').apply(
            lambda x: pd.Series(rolling_beta(x), index=x.index)
        ).reset_index(level=0, drop=True)
        
        # Drop market_returns column
        stocks_df['beta'] = merged['beta']
        
        log.info("✓ Computed beta vs benchmark")
        return stocks_df
    
    def compute_sharpe_ratio(self, df: pd.DataFrame, window: int = 60, risk_free_rate: float = 0.02) -> pd.DataFrame:
        """
        Compute Sharpe ratio (risk-adjusted returns)
        
        Args:
            df: DataFrame with returns
            window: Rolling window size
            risk_free_rate: Annual risk-free rate
            
        Returns:
            DataFrame with sharpe_ratio column
        """
        df = df.copy()
        df = df.sort_values(['symbol', 'Date'])
        
        # Daily risk-free rate
        daily_rf = risk_free_rate / 252
        
        def rolling_sharpe(returns):
            """Calculate rolling Sharpe ratio"""
            mean_return = returns.rolling(window=window, min_periods=max(1, window//2)).mean()
            std_return = returns.rolling(window=window, min_periods=max(1, window//2)).std()
            
            sharpe = (mean_return - daily_rf) / std_return
            
            # Annualize
            sharpe = sharpe * np.sqrt(252)
            
            return sharpe
        
        df['sharpe_ratio'] = df.groupby('symbol')['returns'].transform(rolling_sharpe)
        
        # Fill NaN with 0
        df['sharpe_ratio'] = df['sharpe_ratio'].fillna(0)
        
        # Cap extreme values
        df['sharpe_ratio'] = df['sharpe_ratio'].clip(-5, 5)
        
        log.info("✓ Computed Sharpe ratio")
        return df
    
    def compute_atr(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """
        Compute Average True Range (ATR)
        
        Args:
            df: DataFrame with OHLC data
            window: Rolling window size
            
        Returns:
            DataFrame with atr column
        """
        df = df.copy()
        df = df.sort_values(['symbol', 'Date'])
        
        # True Range components
        df['h_l'] = df['High'] - df['Low']
        df['h_pc'] = abs(df['High'] - df.groupby('symbol')['Close'].shift(1))
        df['l_pc'] = abs(df['Low'] - df.groupby('symbol')['Close'].shift(1))
        
        # True Range is the maximum of the three
        df['true_range'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
        
        # ATR is the rolling average of True Range
        df['atr'] = df.groupby('symbol')['true_range'].transform(
            lambda x: x.rolling(window=window, min_periods=1).mean()
        )
        
        # Normalize ATR by price (as percentage)
        df['atr_pct'] = (df['atr'] / df['Close']) * 100
        
        # Drop intermediate columns
        df = df.drop(columns=['h_l', 'h_pc', 'l_pc', 'true_range'])
        
        log.info("✓ Computed ATR")
        return df
    
    def compute_liquidity(self, df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """
        Compute liquidity metrics
        
        Args:
            df: DataFrame with volume data
            window: Rolling window size
            
        Returns:
            DataFrame with liquidity columns
        """
        df = df.copy()
        df = df.sort_values(['symbol', 'Date'])
        
        # Average volume
        df['avg_volume'] = df.groupby('symbol')['Volume'].transform(
            lambda x: x.rolling(window=window, min_periods=1).mean()
        )
        
        # Volume volatility (liquidity risk)
        df['volume_volatility'] = df.groupby('symbol')['Volume'].transform(
            lambda x: x.rolling(window=window, min_periods=1).std()
        )
        
        # Normalized volume volatility
        df['liquidity_risk'] = df['volume_volatility'] / (df['avg_volume'] + 1)
        
        # Fill NaN
        df['liquidity_risk'] = df['liquidity_risk'].fillna(0)
        
        log.info("✓ Computed liquidity metrics")
        return df
    
    def compute_all_features(self) -> pd.DataFrame:
        """
        Compute all market features
        
        Returns:
            DataFrame with all computed features
        """
        log.info("=" * 60)
        log.info("COMPUTING MARKET FEATURES")
        log.info("=" * 60)
        
        # Load data
        stocks_df, benchmark_df = self.load_data()
        
        # Compute features in sequence
        log.info("Computing features...")
        
        if 'returns' in self.features_config:
            stocks_df = self.compute_returns(stocks_df)
        
        if 'volatility_21d' in self.features_config or 'volatility_60d' in self.features_config:
            windows = []
            if 'volatility_21d' in self.features_config:
                windows.append(21)
            if 'volatility_60d' in self.features_config:
                windows.append(60)
            stocks_df = self.compute_volatility(stocks_df, windows)
        
        if 'max_drawdown' in self.features_config:
            stocks_df = self.compute_max_drawdown(stocks_df)
        
        if 'beta' in self.features_config:
            stocks_df = self.compute_beta(stocks_df, benchmark_df)
        
        if 'sharpe_ratio' in self.features_config:
            stocks_df = self.compute_sharpe_ratio(stocks_df)
        
        if 'atr' in self.features_config:
            stocks_df = self.compute_atr(stocks_df)
        
        if 'liquidity' in self.features_config:
            stocks_df = self.compute_liquidity(stocks_df)
        
        log.info("=" * 60)
        log.info(f"✓ ALL FEATURES COMPUTED")
        log.info(f"Total rows: {len(stocks_df)}")
        log.info(f"Feature columns: {[col for col in stocks_df.columns if col not in ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits', 'symbol']]}")
        log.info("=" * 60)
        
        return stocks_df
    
    def save_features(self, df: pd.DataFrame, filename: str = "market_features.parquet"):
        """
        Save computed features to file
        
        Args:
            df: DataFrame with features
            filename: Output filename
        """
        ensure_dir(self.config['paths']['features'])
        filepath = f"{self.config['paths']['features']}/{filename}"
        save_dataframe(df, filepath, format='parquet')
        log.info(f"✓ Saved features to {filepath}")
    
    def run(self) -> pd.DataFrame:
        """
        Run the complete market data agent pipeline
        
        Returns:
            DataFrame with all features
        """
        log.info("Starting Market Data Agent...")
        
        # Compute features
        features_df = self.compute_all_features()
        
        # Save features
        self.save_features(features_df)
        
        log.info("Market Data Agent completed successfully")
        return features_df