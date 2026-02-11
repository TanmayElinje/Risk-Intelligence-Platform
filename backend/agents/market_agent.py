"""
Market Data Agent - Compute quantitative risk features from market data
Now using PostgreSQL for data persistence
"""
import pandas as pd
import numpy as np
from backend.utils import log, load_config
from backend.database import DatabaseService

class MarketDataAgent:
    """
    Agent responsible for computing market-based risk features
    """
    
    def __init__(self):
        self.config = load_config()
        #self.features_config = self.config['features']
    
    def compute_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute daily returns"""
        df = df.copy()
        df['returns'] = df.groupby('symbol')['Close'].pct_change()
        return df
    
    def compute_volatility(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute rolling volatility (annualized)"""
        df = df.copy()
        
        # 21-day volatility (approximately 1 month)
        df['volatility_21d'] = df.groupby('symbol')['returns'].transform(
            lambda x: x.rolling(window=21, min_periods=10).std() * np.sqrt(252)
        )
        
        # 60-day volatility (approximately 3 months)
        df['volatility_60d'] = df.groupby('symbol')['returns'].transform(
            lambda x: x.rolling(window=60, min_periods=30).std() * np.sqrt(252)
        )
        
        return df
    
    def compute_max_drawdown(self, df: pd.DataFrame, window: int = 252) -> pd.DataFrame:
        """Compute maximum drawdown over rolling window"""
        df = df.copy()
        
        def max_dd(prices):
            """Calculate max drawdown for a price series"""
            if len(prices) < 2:
                return 0
            cummax = prices.expanding(min_periods=1).max()
            drawdown = (prices - cummax) / cummax
            return drawdown.min() * 100  # As percentage
        
        df['max_drawdown'] = df.groupby('symbol')['Close'].transform(
            lambda x: x.rolling(window=window, min_periods=20).apply(max_dd, raw=False)
        )
        
        return df
    
    def compute_beta(self, df: pd.DataFrame, benchmark_df: pd.DataFrame) -> pd.DataFrame:
        """Compute beta relative to benchmark (simplified)"""
        df = df.copy()
        
        # Merge with benchmark
        benchmark_df = benchmark_df.rename(columns={'Close': 'Benchmark_Close'})
        df = df.merge(
            benchmark_df[['Date', 'Benchmark_Close']], 
            on='Date', 
            how='left'
        )
        
        # Compute benchmark returns
        df['benchmark_returns'] = df['Benchmark_Close'].pct_change()
        
        # Compute rolling beta using simpler approach
        def calculate_beta(stock_df):
            """Calculate beta for a stock"""
            # Get valid data
            valid_data = stock_df[['returns', 'benchmark_returns']].dropna()
            
            if len(valid_data) < 20:
                return pd.Series([1.0] * len(stock_df), index=stock_df.index)
            
            # Calculate rolling beta
            betas = []
            for i in range(len(stock_df)):
                if i < 60:
                    betas.append(1.0)  # Default beta for early data
                else:
                    # Get last 60 days of data
                    window_start = max(0, i - 60)
                    window_data = stock_df.iloc[window_start:i][['returns', 'benchmark_returns']].dropna()
                    
                    if len(window_data) >= 20:
                        # Calculate covariance and variance
                        cov_matrix = window_data.cov()
                        if 'benchmark_returns' in cov_matrix.columns and len(cov_matrix) > 1:
                            covariance = cov_matrix.loc['returns', 'benchmark_returns']
                            variance = window_data['benchmark_returns'].var()
                            
                            if variance > 0:
                                beta = covariance / variance
                                betas.append(beta)
                            else:
                                betas.append(1.0)
                        else:
                            betas.append(1.0)
                    else:
                        betas.append(1.0)
            
            return pd.Series(betas, index=stock_df.index)
        
        # Apply to each stock
        df['beta'] = df.groupby('symbol', group_keys=False).apply(calculate_beta)
        
        return df
    
    def compute_sharpe_ratio(self, df: pd.DataFrame, risk_free_rate: float = 0.02) -> pd.DataFrame:
        """Compute rolling Sharpe ratio"""
        df = df.copy()
        
        # Rolling mean and std of returns (60-day window)
        rolling_mean = df.groupby('symbol')['returns'].transform(
            lambda x: x.rolling(window=60, min_periods=20).mean()
        )
        rolling_std = df.groupby('symbol')['returns'].transform(
            lambda x: x.rolling(window=60, min_periods=20).std()
        )
        
        # Annualize
        annualized_return = rolling_mean * 252
        annualized_std = rolling_std * np.sqrt(252)
        
        # Sharpe ratio
        df['sharpe_ratio'] = (annualized_return - risk_free_rate) / annualized_std
        
        return df
    
    def compute_atr(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Compute Average True Range (volatility measure)"""
        df = df.copy()
        
        # True Range
        df['high_low'] = df['High'] - df['Low']
        df['high_close'] = abs(df['High'] - df.groupby('symbol')['Close'].shift(1))
        df['low_close'] = abs(df['Low'] - df.groupby('symbol')['Close'].shift(1))
        
        df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        
        # Average True Range
        df['atr'] = df.groupby('symbol')['true_range'].transform(
            lambda x: x.rolling(window=window, min_periods=5).mean()
        )
        
        # ATR as percentage of price
        df['atr_pct'] = (df['atr'] / df['Close']) * 100
        
        # Clean up
        df = df.drop(columns=['high_low', 'high_close', 'low_close', 'true_range', 'atr'])
        
        return df
    
    def compute_liquidity_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute liquidity-based risk metrics"""
        df = df.copy()
        
        # Average volume (20-day)
        df['avg_volume_20d'] = df.groupby('symbol')['Volume'].transform(
            lambda x: x.rolling(window=20, min_periods=10).mean()
        )
        
        # Volume volatility (indicator of liquidity risk)
        df['volume_volatility'] = df.groupby('symbol')['Volume'].transform(
            lambda x: x.rolling(window=20, min_periods=10).std()
        )
        
        # Liquidity risk score (normalized)
        df['liquidity_risk'] = df['volume_volatility'] / (df['avg_volume_20d'] + 1e-9)
        
        return df
    
    def compute_all_features(self, market_data: pd.DataFrame, benchmark_data: pd.DataFrame) -> pd.DataFrame:
        """
        Compute all market-based risk features
        
        Args:
            market_data: DataFrame with OHLCV data
            benchmark_data: DataFrame with benchmark OHLCV data
        
        Returns:
            DataFrame with all computed features
        """
        log.info("Computing market-based risk features...")
        
        # Ensure Date column is datetime
        market_data['Date'] = pd.to_datetime(market_data['Date'])
        benchmark_data['Date'] = pd.to_datetime(benchmark_data['Date'])
        
        # Sort by symbol and date
        market_data = market_data.sort_values(['symbol', 'Date'])
        benchmark_data = benchmark_data.sort_values('Date')
        
        # Compute features
        df = self.compute_returns(market_data)
        df = self.compute_volatility(df)
        df = self.compute_max_drawdown(df)
        df = self.compute_beta(df, benchmark_data)
        df = self.compute_sharpe_ratio(df)
        df = self.compute_atr(df)
        df = self.compute_liquidity_metrics(df)
        
        # Handle infinities and NaNs
        df = df.replace([np.inf, -np.inf], np.nan)
        
        log.info(f"✓ Computed features for {df['symbol'].nunique()} stocks")
        
        return df
    
    def process(self):
        """
        Main processing method - Load data from DB, compute features, save back to DB
        """
        log.info("=" * 60)
        log.info("MARKET DATA AGENT - Computing Risk Features")
        log.info("=" * 60)
        
        with DatabaseService() as db:
            # Load market data from database
            log.info("Loading market data from database...")
            market_data = db.get_market_data(days=730)  # 2 years of data
            
            if market_data.empty:
                log.error("No market data found in database!")
                return None
            
            log.info(f"Loaded {len(market_data)} market data records")
            
            # Load benchmark data (SPY)
            log.info("Loading benchmark data...")
            benchmark_data = db.get_market_data(symbol='SPY', days=730)
            
            if benchmark_data.empty:
                log.warning("No benchmark data found, using market average as proxy")
                # Create synthetic benchmark from market average
                benchmark_data = market_data.groupby('Date').agg({
                    'Close': 'mean',
                    'Volume': 'sum'
                }).reset_index()
                benchmark_data['symbol'] = 'BENCHMARK'
            
            # Compute all features
            features_df = self.compute_all_features(market_data, benchmark_data)
            
            # Features are already part of market_data, just return
            log.info("✓ Market features computed successfully")
            
            return features_df

def main():
    """Main execution"""
    agent = MarketDataAgent()
    features = agent.process()
    
    if features is not None:
        log.info("=" * 60)
        log.info("✓ MARKET DATA AGENT COMPLETED SUCCESSFULLY")
        log.info("=" * 60)
    else:
        log.error("Market data agent failed")

if __name__ == "__main__":
    main()