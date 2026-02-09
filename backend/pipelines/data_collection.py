"""
Data collection pipeline - orchestrates all data fetching
"""
import pandas as pd
from typing import List, Dict
from datetime import datetime
from backend.scrapers import (
    MoneyControlScraper,
    EconomicTimesScraper,
    MarketDataFetcher
)
from backend.utils import log, load_config, get_stock_symbols, save_dataframe, ensure_dir

class DataCollectionPipeline:
    """
    Orchestrates data collection from all sources
    """
    
    def __init__(self):
        """Initialize data collection pipeline"""
        self.config = load_config()
        self.stock_symbols = get_stock_symbols()
        
        # Initialize scrapers
        self.mc_scraper = MoneyControlScraper()
        self.et_scraper = EconomicTimesScraper()
        self.market_fetcher = MarketDataFetcher()
        
        log.info("Data collection pipeline initialized")
    
    def collect_market_data(self, save: bool = True) -> pd.DataFrame:
        """
        Collect market data for all stocks
        
        Args:
            save: Whether to save data to file
            
        Returns:
            DataFrame with market data
        """
        log.info("=" * 60)
        log.info("COLLECTING MARKET DATA")
        log.info("=" * 60)
        
        # Fetch data for all stocks
        market_df = self.market_fetcher.fetch_multiple_stocks(self.stock_symbols)
        
        # Fetch benchmark data
        benchmark_df = self.market_fetcher.fetch_benchmark_data()
        
        if save:
            # Save market data
            self.market_fetcher.save_market_data(market_df, "stocks_data.parquet")
            if benchmark_df is not None:
                self.market_fetcher.save_market_data(benchmark_df, "benchmark_data.parquet")
        
        log.info(f"Market data collection complete: {len(market_df)} total rows")
        return market_df
    
    def collect_news_data(
        self,
        stock_specific: bool = True,
        general_news: bool = True,
        save: bool = True
    ) -> pd.DataFrame:
        """
        Collect news data from all sources
        
        Args:
            stock_specific: Collect stock-specific news
            general_news: Collect general market news
            save: Whether to save data to file
            
        Returns:
            DataFrame with news data
        """
        log.info("=" * 60)
        log.info("COLLECTING NEWS DATA")
        log.info("=" * 60)
        
        all_articles = []
        
        # Collect general market news
        if general_news:
            log.info("Collecting general market news...")
            
            # MoneyControl general news
            mc_articles = self.mc_scraper.get_latest_news(max_articles=50)
            all_articles.extend(mc_articles)
            
            # Economic Times general news
            et_articles = self.et_scraper.get_latest_news(max_articles=50)
            all_articles.extend(et_articles)
        
        # Collect stock-specific news (for top 10 stocks to save time in testing)
        if stock_specific:
            log.info("Collecting stock-specific news...")
            
            # For demo, only scrape for first 10 stocks
            test_stocks = self.stock_symbols[:10]
            
            for symbol in test_stocks:
                log.info(f"Scraping news for {symbol}")
                
                # MoneyControl
                mc_stock_news = self.mc_scraper.scrape_news(symbol, max_articles=5)
                all_articles.extend(mc_stock_news)
                
                # Economic Times
                et_stock_news = self.et_scraper.scrape_news(symbol, max_articles=5)
                all_articles.extend(et_stock_news)
        
        # Convert to DataFrame
        if all_articles:
            news_df = pd.DataFrame(all_articles)
            
            # Remove duplicates based on URL
            news_df = news_df.drop_duplicates(subset=['url'], keep='first')
            
            if save:
                filepath = f"{self.config['paths']['data_raw']}/news_data.parquet"
                save_dataframe(news_df, filepath, format='parquet')
                log.info(f"Saved {len(news_df)} unique articles to {filepath}")
            
            log.info(f"News data collection complete: {len(news_df)} unique articles")
            return news_df
        else:
            log.warning("No news articles collected")
            return pd.DataFrame()
        
    def collect_market_data_synthetic(self, save: bool = True) -> pd.DataFrame:
        """
        Collect synthetic market data (fallback when Yahoo Finance fails)
        
        Args:
            save: Whether to save data to file
            
        Returns:
            DataFrame with market data
        """
        log.info("=" * 60)
        log.info("COLLECTING MARKET DATA (SYNTHETIC)")
        log.info("=" * 60)
        
        from backend.scrapers import SyntheticDataGenerator
        
        generator = SyntheticDataGenerator()
        
        # Generate data for all stocks
        market_df = generator.generate_multiple_stocks(
            symbols=self.stock_symbols,
            days=self.config['data_sources']['market_data']['history_days']
        )
        
        # Generate benchmark data
        benchmark_symbol = self.config['agents']['market_data']['benchmark']
        benchmark_df = generator.generate_benchmark_data(
            symbol=benchmark_symbol,
            days=self.config['data_sources']['market_data']['history_days']
        )
        
        if save:
            # Save market data
            self.market_fetcher.save_market_data(market_df, "stocks_data.parquet")
            self.market_fetcher.save_market_data(benchmark_df, "benchmark_data.parquet")
        
        log.info(f"Synthetic market data collection complete: {len(market_df)} total rows")
        return market_df

    
    def run_full_pipeline(self, use_synthetic: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Run complete data collection pipeline
        
        Args:
            use_synthetic: Force use of synthetic data
            
        Returns:
            Dictionary with all collected data
        """
        log.info("=" * 60)
        log.info("STARTING FULL DATA COLLECTION PIPELINE")
        log.info("=" * 60)
        
        start_time = datetime.now()
        
        # Ensure directories exist
        ensure_dir(self.config['paths']['data_raw'])
        
        # Collect market data
        if use_synthetic:
            log.warning("Using synthetic data as requested")
            market_df = self.collect_market_data_synthetic()
        else:
            try:
                market_df = self.collect_market_data()
                
                # If no data was fetched, fall back to synthetic
                if market_df.empty:
                    log.warning("No real market data fetched, falling back to synthetic data")
                    market_df = self.collect_market_data_synthetic()
            except Exception as e:
                log.error(f"Error fetching real data: {str(e)}")
                log.warning("Falling back to synthetic data")
                market_df = self.collect_market_data_synthetic()
        
        # Collect news data (skip for now)
        news_df = pd.DataFrame()
        log.info("Skipping news collection for now")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        log.info("=" * 60)
        log.info(f"PIPELINE COMPLETE in {duration:.2f} seconds")
        log.info(f"Market data: {len(market_df)} rows")
        log.info(f"News data: {len(news_df)} articles")
        log.info("=" * 60)
        
        return {
            'market_data': market_df,
            'news_data': news_df
        }