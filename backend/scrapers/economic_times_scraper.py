"""
Economic Times news scraper
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re
from backend.scrapers.base_scraper import BaseScraper
from backend.utils import log

class EconomicTimesScraper(BaseScraper):
    """
    Scraper for EconomicTimes.com
    """
    
    BASE_URL = "https://economictimes.indiatimes.com"
    MARKETS_URL = "https://economictimes.indiatimes.com/markets/stocks/news"
    
    def __init__(self):
        """Initialize Economic Times scraper"""
        super().__init__()
        log.info("Economic Times scraper initialized")
    
    def scrape_news(self, stock_symbol: str, max_articles: int = 50) -> List[Dict]:
        """
        Scrape news for a specific stock
        
        Args:
            stock_symbol: Stock symbol
            max_articles: Maximum articles to scrape
            
        Returns:
            List of article dictionaries
        """
        log.info(f"Scraping Economic Times news for {stock_symbol}")
        articles = []
        
        clean_symbol = stock_symbol.replace('.NS', '')
        
        try:
            # Get general market news and filter
            soup = self._get_page(self.MARKETS_URL)
            if not soup:
                return articles
            
            # Find article containers
            article_items = soup.find_all('div', class_='eachStory')
            
            for item in article_items[:max_articles * 2]:  # Get more to filter
                try:
                    article = self._parse_article(item, stock_symbol)
                    if article:
                        articles.append(article)
                        if len(articles) >= max_articles:
                            break
                except Exception as e:
                    log.warning(f"Error parsing article: {str(e)}")
                    continue
            
            log.info(f"Scraped {len(articles)} articles for {stock_symbol} from Economic Times")
            
        except Exception as e:
            log.error(f"Error scraping Economic Times for {stock_symbol}: {str(e)}")
        
        return articles
    
    def get_latest_news(self, max_articles: int = 100) -> List[Dict]:
        """
        Scrape latest market news
        
        Args:
            max_articles: Maximum articles to scrape
            
        Returns:
            List of article dictionaries
        """
        log.info(f"Scraping latest news from Economic Times")
        articles = []
        
        try:
            soup = self._get_page(self.MARKETS_URL)
            if not soup:
                return articles
            
            article_items = soup.find_all('div', class_='eachStory')
            
            for item in article_items[:max_articles]:
                try:
                    article = self._parse_article(item)
                    if article:
                        articles.append(article)
                except Exception as e:
                    log.warning(f"Error parsing article: {str(e)}")
                    continue
            
            log.info(f"Scraped {len(articles)} latest articles from Economic Times")
            
        except Exception as e:
            log.error(f"Error scraping latest news from Economic Times: {str(e)}")
        
        return articles
    
    def _parse_article(self, item, stock_symbol: Optional[str] = None) -> Optional[Dict]:
        """
        Parse individual article from news item
        
        Args:
            item: BeautifulSoup element
            stock_symbol: Optional stock symbol for filtering
            
        Returns:
            Article dictionary or None
        """
        try:
            # Find headline
            headline_tag = item.find('h3') or item.find('h2')
            if not headline_tag:
                return None
            
            headline = self._clean_text(headline_tag.get_text())
            
            # Find URL
            link = item.find('a', href=True)
            url = link['href'] if link else None
            if url and not url.startswith('http'):
                url = self.BASE_URL + url
            
            # Find description
            desc_tag = item.find('p')
            description = self._clean_text(desc_tag.get_text()) if desc_tag else ""
            
            # Find date
            date_tag = item.find('time')
            date_str = date_tag.get('datetime', '') if date_tag else ""
            published_date = self._parse_date(date_str)
            
            # Check relevance to stock
            if stock_symbol:
                clean_symbol = stock_symbol.replace('.NS', '')
                text_to_check = f"{headline} {description}".lower()
                if clean_symbol.lower() not in text_to_check:
                    return None
            
            article = {
                'source': 'EconomicTimes',
                'headline': headline,
                'description': description,
                'url': url,
                'published_date': published_date,
                'stock_symbol': stock_symbol if stock_symbol else 'GENERAL',
                'scraped_at': datetime.now()
            }
            
            return article
            
        except Exception as e:
            log.warning(f"Error parsing Economic Times article: {str(e)}")
            return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse Economic Times date format
        
        Args:
            date_str: Date string (ISO format or relative)
            
        Returns:
            datetime object
        """
        try:
            if not date_str:
                return datetime.now()
            
            # Try ISO format first
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Handle relative dates
            if 'hour' in date_str.lower():
                hours = int(re.search(r'\d+', date_str).group())
                return datetime.now() - timedelta(hours=hours)
            elif 'day' in date_str.lower():
                days = int(re.search(r'\d+', date_str).group())
                return datetime.now() - timedelta(days=days)
            else:
                from dateutil import parser
                return parser.parse(date_str)
        except:
            return datetime.now()