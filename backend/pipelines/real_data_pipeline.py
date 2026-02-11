"""
Real Data Collection Pipeline
Uses yfinance for stock data and Selenium for news
"""
from datetime import datetime, timedelta
from backend.scrapers.yfinance_collector import YFinanceCollector
from backend.scrapers.selenium_news_scraper import SeleniumNewsScraper
from backend.database import DatabaseService
from backend.utils import log, load_config

class RealDataPipeline:
    """
    Collect real market data and news
    """
    
    def __init__(self):
        self.config = load_config()
        self.yfinance = YFinanceCollector()
        self.news_scraper = SeleniumNewsScraper(headless=True)
    
    def collect_stock_data(self, symbols: list = None, period: str = "1mo"):
        """
        Collect real stock data using yfinance
        """
        log.info("=" * 60)
        log.info("COLLECTING REAL STOCK DATA")
        log.info("=" * 60)
        
        if symbols is None:
            symbols = self.config['stocks']['symbols']
        
        # Fetch data
        market_data = self.yfinance.get_multiple_stocks(symbols, period=period)
        
        if market_data.empty:
            log.error("No market data collected!")
            return None
        
        # Save to database
        with DatabaseService() as db:
            log.info("Saving market data to database...")
            db.save_market_data(market_data, upsert=True)
        
        log.info(f"✓ Collected and saved {len(market_data)} market data records")
        return market_data
    
    def collect_news(self, symbols: list = None, articles_per_source: int = 3):
        """
        Collect real news using Selenium scraping
        """
        log.info("=" * 60)
        log.info("COLLECTING REAL NEWS ARTICLES")
        log.info("=" * 60)
        
        if symbols is None:
            # Focus on high-risk stocks or top stocks
            symbols = self.config['stocks']['symbols'][:10]  # Top 10 stocks
        
        all_articles = []
        
        for symbol in symbols:
            log.info(f"Scraping news for {symbol}...")
            articles = self.news_scraper.scrape_all_sources(symbol, articles_per_source)
            all_articles.extend(articles)
        
        log.info(f"✓ Collected {len(all_articles)} news articles")
        
        # Save to database
        if all_articles:
            self._save_news_to_db(all_articles)
        
        return all_articles
    
    def _save_news_to_db(self, articles: list):
        """Save news articles to database"""
        with DatabaseService() as db:
            from backend.database.models import NewsArticle, Stock
            
            saved_count = 0
            
            for article in articles:
                try:
                    # Get stock
                    stock = db.get_stock_by_symbol(article.get('stock_symbol', 'GENERAL'))
                    
                    # Check if article already exists (by URL)
                    existing = db.db.query(NewsArticle).filter(
                        NewsArticle.url == article['url']
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Create new article
                    news_article = NewsArticle(
                        stock_id=stock.id if stock else None,
                        source=article.get('source'),
                        headline=article.get('headline'),
                        description=article.get('description'),
                        content=article.get('content'),  # Full article content!
                        url=article.get('url'),
                        published_date=article.get('published_date'),
                        authors=', '.join(article.get('authors', [])),
                        top_image=article.get('top_image')
                    )
                    
                    db.db.add(news_article)
                    saved_count += 1
                    
                except Exception as e:
                    log.error(f"Error saving article: {str(e)}")
                    continue
            
            db.db.commit()
            log.info(f"✓ Saved {saved_count} new articles to database")
    
    def run_full_collection(self):
        """
        Run full data collection
        """
        log.info("=" * 80)
        log.info("REAL DATA COLLECTION PIPELINE")
        log.info("=" * 80)
        
        # Collect news first (Selenium works!)
        log.info("\n📰 Step 1: Collecting news articles...")
        news_articles = self.collect_news(articles_per_source=2)
        
        # Collect stock data (may fail due to rate limiting)
        log.info("\n📊 Step 2: Collecting stock data...")
        try:
            market_data = self.collect_stock_data(period="1mo")
        except Exception as e:
            log.error(f"Stock data collection failed: {str(e)}")
            log.warning("Continuing with news only...")
            market_data = None
        
        log.info("=" * 80)
        log.info("✓ REAL DATA COLLECTION COMPLETED")
        log.info(f"  - Market Data: {len(market_data) if market_data is not None else 0} records")
        log.info(f"  - News Articles: {len(news_articles)} articles")
        log.info("=" * 80)
        
        return {
            'market_data': market_data,
            'news_articles': news_articles
        }

def main():
    """Run the pipeline"""
    pipeline = RealDataPipeline()
    pipeline.run_full_collection()

if __name__ == "__main__":
    main()