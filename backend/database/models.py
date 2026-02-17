# 🔧 REPLACE YOUR ENTIRE models.py WITH THIS

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
from werkzeug.security import generate_password_hash, check_password_hash

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


# ==================== USER & AUTH MODELS ====================

class User(Base):
    """User model for authentication (MERGED VERSION)"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    watchlists = relationship("Watchlist", back_populates="user")
    alert_rules = relationship("AlertRule", back_populates="user")
    user_alerts = relationship("UserAlert", back_populates="user")
    alert_preferences = relationship('UserAlertPreference', back_populates='user')
    portfolio_holdings = relationship('PortfolioHolding', back_populates='user', cascade='all, delete-orphan')
    portfolio_transactions = relationship('PortfolioTransaction', back_populates='user', cascade='all, delete-orphan')
    email_alert_pref = relationship('EmailAlertPreference', back_populates='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary (exclude password)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


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


class UserAlertPreference(Base):
    """User's alert notification preferences"""
    __tablename__ = 'user_alert_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'), nullable=True)
    alert_type = Column(String(50))
    is_enabled = Column(Boolean, default=True)
    min_severity = Column(String(20), default='medium')
    email_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='alert_preferences')
    stock = relationship('Stock')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stock_id': self.stock_id,
            'stock_symbol': self.stock.symbol if self.stock else None,
            'alert_type': self.alert_type,
            'is_enabled': self.is_enabled,
            'min_severity': self.min_severity,
            'email_enabled': self.email_enabled,
            'push_enabled': self.push_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ==================== STOCK MODELS ====================

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
    content = Column(Text)
    url = Column(String(500), unique=True)
    published_date = Column(DateTime)
    sentiment_label = Column(String(20))
    sentiment_score = Column(Numeric(5, 4))
    sentiment_confidence = Column(Numeric(5, 4))
    authors = Column(Text)
    top_image = Column(String(500))
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


# ==================== WATCHLIST MODELS ====================

class Watchlist(Base):
    """User watchlist model (MERGED VERSION)"""
    __tablename__ = 'watchlists'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    name = Column(String(255), nullable=False, default='My Watchlist')
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="watchlists")
    stocks = relationship("WatchlistStock", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistStock(Base):
    """Watchlist-Stock association model"""
    __tablename__ = 'watchlist_stocks'
    
    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey('watchlists.id', ondelete='CASCADE'))
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'))
    added_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(String(500))
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="stocks")
    stock = relationship("Stock")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('watchlist_id', 'stock_id', name='uix_watchlist_stock'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'watchlist_id': self.watchlist_id,
            'stock_id': self.stock_id,
            'stock_symbol': self.stock.symbol if self.stock else None,
            'stock_name': self.stock.name if self.stock else None,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'notes': self.notes
        }


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


# ==================== EMAIL ALERT PREFERENCES ====================

class EmailAlertPreference(Base):
    """User email alert preferences"""
    __tablename__ = 'email_alert_preferences'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    email_alerts_enabled = Column(Boolean, default=False)
    alert_email = Column(String(255))
    high_risk_alerts = Column(Boolean, default=True)
    medium_risk_alerts = Column(Boolean, default=False)
    daily_digest = Column(Boolean, default=False)
    watchlist_only = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='email_alert_pref')
    
    def to_dict(self):
        return {
            'email_alerts_enabled': self.email_alerts_enabled,
            'alert_email': self.alert_email,
            'high_risk_alerts': self.high_risk_alerts,
            'medium_risk_alerts': self.medium_risk_alerts,
            'daily_digest': self.daily_digest,
            'watchlist_only': self.watchlist_only,
        }


# ==================== PORTFOLIO MODELS ====================

class PortfolioHolding(Base):
    """User portfolio holding model"""
    __tablename__ = 'portfolio_holdings'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(Numeric(20, 6), nullable=False)
    purchase_price = Column(Numeric(20, 4), nullable=False)
    purchase_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='portfolio_holdings')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'symbol', name='uix_portfolio_user_symbol'),
        Index('idx_portfolio_user', 'user_id'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'quantity': float(self.quantity) if self.quantity else 0,
            'purchase_price': float(self.purchase_price) if self.purchase_price else 0,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class PortfolioTransaction(Base):
    """Portfolio transaction history model"""
    __tablename__ = 'portfolio_transactions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    transaction_type = Column(String(10), nullable=False)  # BUY or SELL
    quantity = Column(Numeric(20, 6), nullable=False)
    price = Column(Numeric(20, 4), nullable=False)
    transaction_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='portfolio_transactions')
    
    # Indexes
    __table_args__ = (
        Index('idx_transaction_user', 'user_id'),
        Index('idx_transaction_date', 'transaction_date'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'transaction_type': self.transaction_type,
            'quantity': float(self.quantity) if self.quantity else 0,
            'price': float(self.price) if self.price else 0,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


def drop_db():
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)
    print("✓ Database tables dropped")


