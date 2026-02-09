"""
Web scrapers and data fetchers
"""
from backend.scrapers.base_scraper import BaseScraper
from backend.scrapers.moneycontrol_scraper import MoneyControlScraper
from backend.scrapers.economic_times_scraper import EconomicTimesScraper
from backend.scrapers.market_data_fetcher import MarketDataFetcher
from backend.scrapers.synthetic_data_generator import SyntheticDataGenerator

__all__ = [
    'BaseScraper',
    'MoneyControlScraper',
    'EconomicTimesScraper',
    'MarketDataFetcher',
    'SyntheticDataGenerator'
]