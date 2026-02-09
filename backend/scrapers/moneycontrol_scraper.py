"""
MoneyControl news scraper
"""
from typing import List, Dict, Optional
from datetime import datetime
import re
from backend.scrapers.base_scraper import BaseScraper
from backend.utils import log

class MoneyControlScraper(BaseScraper):
    """
    Scraper for MoneyControl.com
    """
    
    BASE_URL = "https://www.moneycontrol.com"
    SEARCH_URL = "https://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php"
    NEWS_URL = "https://www.moneycontrol.com/news/business/stocks/"
    
    def __init__(self):
        """Initialize MoneyControl scraper"""
        super().__init__()
        log.info("MoneyControl scraper initialized")
    
    def _get_stock_url(self, stock_symbol: str) -> Optional[str]:
        """
        Get MoneyControl URL for a stock
        
        Args:
            stock_symbol: Stock symbol (e.g., 'RELIANCE')
            
        Returns:
            Stock URL or None
        """
        # Remove .NS suffix if present
        clean_symbol = stock_symbol.replace('.NS', '')
        
        try:
            # Search for the stock
            search_url = f"{self.SEARCH_URL}?search_data={clean_symbol}"
            soup = self._get_page(search_url)
            
            if soup:
                # Find stock link (this is a simplified approach)
                # In production, you'd need more robust parsing
                links = soup.find_all('a', href=True)
                for link in links:
                    if clean_symbol.lower() in link.text.lower():
                        return self.BASE_URL + link['href']
            
            log.warning(f"Could not find MoneyControl URL for {stock_symbol}")
            return None
            
        except Exception as e:
            log.error(f"Error finding stock URL for {stock_symbol}: {str(e)}")
            return None
    
    def scrape_news(self, stock_symbol: str, max_articles: int = 50) -> List[Dict]:
        """
        Scrape news for a specific stock
        
        Args:
            stock_symbol: Stock symbol
            max_articles: Maximum articles to scrape
            
        Returns:
            List of article dictionaries
        """
        log.info(f"Scraping MoneyControl news for {stock_symbol}")
        articles = []
        
        # Remove .NS suffix
        clean_symbol = stock_symbol.replace('.NS', '')
        
        # MoneyControl search by company name
        # For demo, we'll scrape general news and filter by company name
        # In production, you'd navigate to specific stock pages
        
        try:
            soup = self._get_page(self.NEWS_URL)
            if not soup:
                return articles
            
            # Find news articles
            news_items = soup.find_all('li', class_='clearfix')
            
            for item in news_items[:max_articles]:
                try:
                    article = self._parse_article(item, stock_symbol)
                    if article:
                        articles.append(article)
                except Exception as e:
                    log.warning(f"Error parsing article: {str(e)}")
                    continue
            
            log.info(f"Scraped {len(articles)} articles for {stock_symbol} from MoneyControl")
            
        except Exception as e:
            log.error(f"Error scraping MoneyControl for {stock_symbol}: {str(e)}")
        
        return articles
    
    def get_latest_news(self, max_articles: int = 100) -> List[Dict]:
        """
        Scrape latest market news
        
        Args:
            max_articles: Maximum articles to scrape
            
        Returns:
            List of article dictionaries
        """
        log.info(f"Scraping latest news from MoneyControl")
        articles = []
        
        try:
            soup = self._get_page(self.NEWS_URL)
            if not soup:
                return articles
            
            news_items = soup.find_all('li', class_='clearfix')
            
            for item in news_items[:max_articles]:
                try:
                    article = self._parse_article(item)
                    if article:
                        articles.append(article)
                except Exception as e:
                    log.warning(f"Error parsing article: {str(e)}")
                    continue
            
            log.info(f"Scraped {len(articles)} latest articles from MoneyControl")
            
        except Exception as e:
            log.error(f"Error scraping latest news from MoneyControl: {str(e)}")
        
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
            headline_tag = item.find('h2') or item.find('a')
            if not headline_tag:
                return None
            
            headline = self._clean_text(headline_tag.get_text())
            
            # Find URL
            link = headline_tag.find('a') if headline_tag.name == 'h2' else headline_tag
            url = link['href'] if link and 'href' in link.attrs else None
            if url and not url.startswith('http'):
                url = self.BASE_URL + url
            
            # Find description/snippet
            desc_tag = item.find('p')
            description = self._clean_text(desc_tag.get_text()) if desc_tag else ""
            
            # Find date
            date_tag = item.find('span')
            date_str = self._clean_text(date_tag.get_text()) if date_tag else ""
            published_date = self._parse_date(date_str)
            
            # If stock_symbol provided, check if article is relevant
            if stock_symbol:
                clean_symbol = stock_symbol.replace('.NS', '')
                text_to_check = f"{headline} {description}".lower()
                if clean_symbol.lower() not in text_to_check:
                    return None  # Not relevant to this stock
            
            article = {
                'source': 'MoneyControl',
                'headline': headline,
                'description': description,
                'url': url,
                'published_date': published_date,
                'stock_symbol': stock_symbol if stock_symbol else 'GENERAL',
                'scraped_at': datetime.now()
            }
            
            return article
            
        except Exception as e:
            log.warning(f"Error parsing MoneyControl article: {str(e)}")
            return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse MoneyControl date format
        
        Args:
            date_str: Date string
            
        Returns:
            datetime object
        """
        # MoneyControl uses formats like "January 15, 2024" or "2 hours ago"
        try:
            # Handle relative dates
            if 'hour' in date_str.lower() or 'minute' in date_str.lower():
                return datetime.now()
            elif 'day' in date_str.lower():
                # Extract number of days
                days = int(re.search(r'\d+', date_str).group())
                return datetime.now() - timedelta(days=days)
            else:
                # Try parsing absolute date
                from dateutil import parser
                return parser.parse(date_str)
        except:
            return datetime.now()