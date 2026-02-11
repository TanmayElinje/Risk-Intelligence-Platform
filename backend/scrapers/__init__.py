"""
Data scrapers
"""
from backend.scrapers.base_scraper import BaseScraper
from backend.scrapers.selenium_news_scraper import SeleniumNewsScraper

__all__ = [
    'BaseScraper',
    'SeleniumNewsScraper'
]