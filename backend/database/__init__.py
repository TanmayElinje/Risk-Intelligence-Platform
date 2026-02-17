"""
Database package
"""
from backend.database.models import (
    Base, engine, SessionLocal,
    User, UserPreference, Stock, MarketData, RiskScore,
    NewsArticle, SentimentScore, Alert, Watchlist, WatchlistStock,
    AlertRule, UserAlert, RiskHistory, PortfolioHolding, PortfolioTransaction,
    EmailAlertPreference
)
from backend.database.db_service import DatabaseService

__all__ = [
    'Base', 'engine', 'SessionLocal',
    'User', 'UserPreference', 'Stock', 'MarketData', 'RiskScore',
    'NewsArticle', 'SentimentScore', 'Alert', 'Watchlist', 'WatchlistStock',
    'AlertRule', 'UserAlert', 'RiskHistory', 'PortfolioHolding', 'PortfolioTransaction',
    'EmailAlertPreference',
    'DatabaseService'
]