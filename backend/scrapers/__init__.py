"""
Data scrapers
"""
from backend.scrapers.base_scraper import BaseScraper
from backend.scrapers.selenium_news_scraper import SeleniumNewsScraper
from backend.scrapers.yfinance_collector import YFinanceCollector
from backend.scrapers.news_fetcher import NewsFetcher

__all__ = [
    'BaseScraper',
    'SeleniumNewsScraper',
    'YFinanceCollector',
    'NewsFetcher'
]