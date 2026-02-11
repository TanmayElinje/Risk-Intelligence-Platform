"""
SQLAlchemy Database Models
"""
from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, DateTime, Date,
    BigInteger, Text, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.types import Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import os

# Load .env from the project root
from pathlib import Path
from dotenv import load_dotenv

# Find and load .env file
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    # Fallback to hardcoded (only for development)
    DATABASE_URL = 'postgresql://postgres:Tanmay%407099@localhost:5432/risk_intelligence'
    print(f"⚠️  WARNING: Using hardcoded DATABASE_URL. Please check your .env file.")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    """User model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    
    # Relationships
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    watchlists = relationship("Watchlist", back_populates="user")
    alert_rules = relationship("AlertRule", back_populates="user")
    user_alerts = relationship("UserAlert", back_populates="user")


class UserPreference(Base):
    """User preferences model"""
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    theme = Column(String(50), default='light')
    email_alerts = Column(Boolean, default=True)
    email_frequency = Column(String(50), default='daily')
    dashboard_layout = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="preferences")


class Stock(Base):
    """Stock model"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255))
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(BigInteger)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    market_data = relationship("MarketData", back_populates="stock")
    risk_scores = relationship("RiskScore", back_populates="stock")
    news_articles = relationship("NewsArticle", back_populates="stock")
    sentiment_scores = relationship("SentimentScore", back_populates="stock")
    alerts = relationship("Alert", back_populates="stock")
    risk_history = relationship("RiskHistory", back_populates="stock")


class MarketData(Base):
    """Market data (OHLCV) model"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'))
    date = Column(Date, nullable=False)
    open = Column(Numeric(20, 4))
    high = Column(Numeric(20, 4))
    low = Column(Numeric(20, 4))
    close = Column(Numeric(20, 4))
    volume = Column(BigInteger)
    adjusted_close = Column(Numeric(20, 4))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="market_data")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('stock_id', 'date', name='uix_stock_date'),
        Index('idx_market_data_stock_date', 'stock_id', 'date'),
    )


class RiskScore(Base):
    """Risk score model"""
    __tablename__ = 'risk_scores'
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'))
    date = Column(Date, nullable=False)
    risk_score = Column(Numeric(10, 6))
    risk_level = Column(String(20))
    risk_rank = Column(Integer)
    volatility_21d = Column(Numeric(10, 6))
    volatility_60d = Column(Numeric(10, 6))
    max_drawdown = Column(Numeric(10, 4))
    beta = Column(Numeric(10, 6))
    sharpe_ratio = Column(Numeric(10, 6))
    atr_pct = Column(Numeric(10, 6))
    liquidity_risk = Column(Numeric(10, 6))
    norm_volatility = Column(Numeric(10, 6))
    norm_drawdown = Column(Numeric(10, 6))
    norm_sentiment = Column(Numeric(10, 6))
    norm_liquidity = Column(Numeric(10, 6))
    risk_drivers = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="risk_scores")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('stock_id', 'date', name='uix_risk_stock_date'),
        Index('idx_risk_scores_stock_date', 'stock_id', 'date'),
    )


class NewsArticle(Base):
    """News articles"""
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=True)
    source = Column(String(100))
    headline = Column(Text, nullable=False)
    description = Column(Text)
    content = Column(Text)  # ADD THIS LINE - Full article content
    url = Column(String(500), unique=True)
    published_date = Column(DateTime)
    sentiment_label = Column(String(20))
    sentiment_score = Column(Numeric(5, 4))
    sentiment_confidence = Column(Numeric(5, 4))
    authors = Column(Text)  # ADD THIS LINE - Comma-separated authors
    top_image = Column(String(500))  # ADD THIS LINE - Article image URL
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    stock = relationship('Stock', back_populates='news_articles')


class SentimentScore(Base):
    """Aggregated sentiment score model"""
    __tablename__ = 'sentiment_scores'
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'))
    date = Column(Date, nullable=False)
    avg_sentiment = Column(Numeric(10, 6))
    sentiment_std = Column(Numeric(10, 6))
    article_count = Column(Integer)
    positive_count = Column(Integer)
    negative_count = Column(Integer)
    neutral_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="sentiment_scores")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('stock_id', 'date', name='uix_sentiment_stock_date'),
        Index('idx_sentiment_stock_date', 'stock_id', 'date'),
    )


class Alert(Base):
    """Alert model"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'))
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    risk_score = Column(Numeric(10, 6))
    prev_risk_score = Column(Numeric(10, 6))
    risk_change = Column(Numeric(10, 6))
    risk_change_pct = Column(Numeric(10, 4))
    risk_level = Column(String(20))
    risk_drivers = Column(Text)
    explanation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    stock = relationship("Stock", back_populates="alerts")
    user_alerts = relationship("UserAlert", back_populates="alert")
    
    # Indexes
    __table_args__ = (
        Index('idx_alerts_created', 'created_at'),
        Index('idx_alerts_stock', 'stock_id'),
    )


class Watchlist(Base):
    """Watchlist model"""
    __tablename__ = 'watchlists'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="watchlists")
    stocks = relationship("WatchlistStock", back_populates="watchlist")


class WatchlistStock(Base):
    """Watchlist-Stock association model"""
    __tablename__ = 'watchlist_stocks'
    
    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey('watchlists.id', ondelete='CASCADE'))
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'))
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="stocks")
    stock = relationship("Stock")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('watchlist_id', 'stock_id', name='uix_watchlist_stock'),
    )


class AlertRule(Base):
    """User-defined alert rule model"""
    __tablename__ = 'alert_rules'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'))
    condition = Column(String(50), nullable=False)
    threshold = Column(Numeric(10, 6))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="alert_rules")
    stock = relationship("Stock")


class UserAlert(Base):
    """User alert notification model"""
    __tablename__ = 'user_alerts'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    alert_id = Column(Integer, ForeignKey('alerts.id', ondelete='CASCADE'))
    is_read = Column(Boolean, default=False)
    is_acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_alerts")
    alert = relationship("Alert", back_populates="user_alerts")


class RiskHistory(Base):
    """Risk history for trending model"""
    __tablename__ = 'risk_history'
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'))
    risk_score = Column(Numeric(10, 6))
    risk_level = Column(String(20))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    stock = relationship("Stock", back_populates="risk_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_risk_history_stock_time', 'stock_id', 'timestamp'),
    )


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


def drop_db():
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)
    print("✓ Database tables dropped")