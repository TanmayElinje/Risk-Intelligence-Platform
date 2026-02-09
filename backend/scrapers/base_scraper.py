"""
Base scraper class with common functionality
"""
from abc import ABC, abstractmethod
import time
import random
from typing import List, Dict, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from backend.utils import log, load_config

class BaseScraper(ABC):
    """
    Abstract base class for web scrapers
    """
    
    def __init__(self):
        """Initialize scraper with config"""
        self.config = load_config()
        self.scraping_config = self.config['data_sources']['news']['scraping']
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def _get_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a web page with retry logic
        
        Args:
            url: URL to fetch
            retries: Number of retries on failure
            
        Returns:
            BeautifulSoup object or None
        """
        for attempt in range(retries):
            try:
                # Add random delay to avoid rate limiting
                delay = self.scraping_config['request_delay']
                time.sleep(delay + random.uniform(0, 1))
                
                response = self.session.get(
                    url,
                    timeout=self.scraping_config['timeout']
                )
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                log.debug(f"Successfully fetched: {url}")
                return soup
                
            except requests.RequestException as e:
                log.warning(f"Attempt {attempt + 1}/{retries} failed for {url}: {str(e)}")
                if attempt == retries - 1:
                    log.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters but keep basic punctuation
        text = text.strip()
        
        return text
    
    def _extract_date(self, date_str: str) -> Optional[datetime]:
        """
        Extract datetime from date string
        
        Args:
            date_str: Date string
            
        Returns:
            datetime object or None
        """
        # This will be implemented by child classes as each site has different formats
        return None
    
    @abstractmethod
    def scrape_news(self, stock_symbol: str, max_articles: int = 50) -> List[Dict]:
        """
        Scrape news articles for a given stock
        
        Args:
            stock_symbol: Stock symbol (e.g., 'RELIANCE')
            max_articles: Maximum number of articles to scrape
            
        Returns:
            List of article dictionaries
        """
        pass
    
    @abstractmethod
    def get_latest_news(self, max_articles: int = 100) -> List[Dict]:
        """
        Scrape latest general market news
        
        Args:
            max_articles: Maximum number of articles
            
        Returns:
            List of article dictionaries
        """
        pass