"""
Selenium-based news scraper for JavaScript-rendered sites
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import time
from typing import List, Dict, Optional
from backend.utils import log
import re

class SeleniumNewsScraper:
    """
    News scraper using Selenium to handle JavaScript-rendered content
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self._init_driver()
    
    def _init_driver(self):
        """Initialize Chrome driver"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Use webdriver-manager to auto-download chromedriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            log.info("✓ Chrome driver initialized")
            
        except Exception as e:
            log.error(f"Failed to initialize Chrome driver: {str(e)}")
            self.driver = None
    
    def __del__(self):
        """Cleanup"""
        if self.driver:
            self.driver.quit()
    
    def _get_page_content(self, url: str, wait_time: int = 5) -> Optional[str]:
        """Get page content after JavaScript execution"""
        try:
            log.info(f"Loading: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(wait_time)
            
            # Get page source after JavaScript execution
            html = self.driver.page_source
            
            return html
            
        except Exception as e:
            log.error(f"Error loading {url}: {str(e)}")
            return None
    
    def scrape_moneycontrol(self, stock_symbol: str, max_articles: int = 5) -> List[Dict]:
        """Scrape MoneyControl with Selenium"""
        log.info(f"Scraping MoneyControl for {stock_symbol} with Selenium...")
        articles = []
        
        try:
            urls = [
                f"https://www.moneycontrol.com/news/tags/{stock_symbol.lower()}.html",
                f"https://www.moneycontrol.com/news/business/stocks/{stock_symbol.lower()}.html",
            ]
            
            for url in urls:
                html = self._get_page_content(url, wait_time=5)
                if not html:
                    continue
                
                soup = BeautifulSoup(html, 'lxml')
                
                # Find article links - be more specific
                all_links = soup.find_all('a', href=True)
                
                # Filter for actual news articles (not homepage, not navigation)
                article_links = [
                    a for a in all_links 
                    if '/news/' in a.get('href', '') 
                    and 'articleshow' not in a.get('href', '')  # Avoid ET links
                    and len(a.get('href', '')) > 30  # Avoid short navigation links
                    and a.get_text(strip=True)
                    and len(a.get_text(strip=True)) > 20  # Meaningful headlines
                    and not a.get('href', '').endswith('.html')  # Avoid tag pages
                    and '.cms' in a.get('href', '')  # MoneyControl article URLs end in .cms
                ][:max_articles]
                
                log.info(f"Found {len(article_links)} article links")
                
                for link in article_links:
                    try:
                        article_url = link.get('href')
                        if not article_url.startswith('http'):
                            article_url = f"https://www.moneycontrol.com{article_url}"
                        
                        headline = link.get_text(strip=True)
                        
                        # Skip if it's not a real article
                        if 'Latest News' in headline or 'Moneycontrol' in headline:
                            continue
                        
                        # Get full article
                        article_data = self._extract_article(article_url, 'MoneyControl')
                        
                        if article_data:
                            article_data['stock_symbol'] = stock_symbol
                            articles.append(article_data)
                            log.info(f"✓ Scraped: {headline[:50]}...")
                        
                    except Exception as e:
                        log.error(f"Error scraping article: {str(e)}")
                        continue
                
                if articles:
                    break  # If we got articles, don't try other URLs
            
        except Exception as e:
            log.error(f"Error scraping MoneyControl: {str(e)}")
        
        return articles
    
    def scrape_economic_times(self, stock_symbol: str, max_articles: int = 5) -> List[Dict]:
        """Scrape Economic Times with Selenium"""
        log.info(f"Scraping Economic Times for {stock_symbol} with Selenium...")
        articles = []
        
        try:
            url = f"https://economictimes.indiatimes.com/topic/{stock_symbol.lower()}"
            
            html = self._get_page_content(url, wait_time=5)
            if not html:
                return articles
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Debug
            all_links = soup.find_all('a', href=True)
            log.info(f"Found {len(all_links)} total links after JS execution")
            
            # Find article links
            article_links = [
                a for a in all_links 
                if 'articleshow' in a.get('href', '') and a.get_text(strip=True)
            ][:max_articles]
            
            log.info(f"Found {len(article_links)} article links")
            
            for link in article_links:
                try:
                    article_url = link.get('href')
                    if not article_url.startswith('http'):
                        article_url = f"https://economictimes.indiatimes.com{article_url}"
                    
                    headline = link.get_text(strip=True)
                    
                    if not headline or len(headline) < 10:
                        continue
                    
                    article_data = self._extract_article(article_url, 'Economic Times')
                    
                    if article_data:
                        article_data['stock_symbol'] = stock_symbol
                        articles.append(article_data)
                        log.info(f"✓ Scraped: {headline[:50]}...")
                    
                except Exception as e:
                    log.error(f"Error scraping article: {str(e)}")
                    continue
            
        except Exception as e:
            log.error(f"Error scraping Economic Times: {str(e)}")
        
        return articles
    
    def _extract_article(self, url: str, source: str) -> Optional[Dict]:
        """Extract full article content"""
        try:
            html = self._get_page_content(url, wait_time=3)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract title
            title = soup.find('h1') or soup.find('title')
            headline = title.get_text(strip=True) if title else "No Title"
            
            # Extract content - get all paragraphs
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])
            
            if len(content) < 100:
                return None
            
            # Clean
            headline = re.sub(r'\s+', ' ', headline).strip()
            content = re.sub(r'\s+', ' ', content).strip()
            
            return {
                'headline': headline,
                'content': content,
                'description': content[:500],
                'url': url,
                'published_date': datetime.now(),
                'source': source,
                'authors': [],
                'top_image': None
            }
            
        except Exception as e:
            log.error(f"Error extracting article from {url}: {str(e)}")
            return None
    
    def scrape_all_sources(self, stock_symbol: str, articles_per_source: int = 5) -> List[Dict]:
        """Scrape from all sources"""
        log.info(f"Scraping all sources for {stock_symbol}...")
        
        all_articles = []
        all_articles.extend(self.scrape_moneycontrol(stock_symbol, articles_per_source))
        all_articles.extend(self.scrape_economic_times(stock_symbol, articles_per_source))
        
        log.info(f"✓ Total articles: {len(all_articles)}")
        
        return all_articles

def main():
    """Test Selenium scraper"""
    scraper = SeleniumNewsScraper(headless=True)
    
    test_stocks = ['RELIANCE', 'TCS']
    
    for stock in test_stocks:
        log.info(f"\n{'='*60}")
        log.info(f"Testing {stock}")
        log.info('='*60)
        
        articles = scraper.scrape_all_sources(stock, articles_per_source=2)
        
        for i, article in enumerate(articles, 1):
            print(f"\nArticle {i}:")
            print(f"Source: {article['source']}")
            print(f"Headline: {article['headline'][:80]}...")
            print(f"Content: {len(article['content'])} chars")
            print(f"URL: {article['url']}")

if __name__ == "__main__":
    main()