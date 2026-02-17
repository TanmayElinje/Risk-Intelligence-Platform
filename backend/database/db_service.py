"""
Database Service Layer - Helper functions for common DB operations
"""
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from backend.database.models import (
    SessionLocal, Stock, MarketData, RiskScore, NewsArticle,
    SentimentScore, Alert, RiskHistory
)
from backend.utils import log
import pandas as pd
import numpy as np

class DatabaseService:
    """Service layer for database operations"""
    
    def __init__(self):
        self.db: Session = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def close(self):
        """Close database session"""
        self.db.close()
    
    # ==================== STOCK OPERATIONS ====================
    
    def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        """Get stock by symbol"""
        return self.db.query(Stock).filter(Stock.symbol == symbol).first()
    
    def get_all_stocks(self, active_only: bool = True) -> List[Stock]:
        """Get all stocks"""
        query = self.db.query(Stock)
        if active_only:
            query = query.filter(Stock.is_active == True)
        return query.all()
    
    def get_stock_symbols(self, active_only: bool = True) -> List[str]:
        """Get list of stock symbols"""
        stocks = self.get_all_stocks(active_only)
        return [stock.symbol for stock in stocks]
    
    # ==================== MARKET DATA OPERATIONS ====================
    
    def save_market_data(self, data: pd.DataFrame, upsert: bool = True):
        """
        Save market data to database
        
        Args:
            data: DataFrame with columns: symbol, Date, Open, High, Low, Close, Volume
            upsert: If True, update existing records
        """
        log.info(f"Saving {len(data)} market data records to database...")
        
        saved_count = 0
        updated_count = 0
        
        for _, row in data.iterrows():
            stock = self.get_stock_by_symbol(row['symbol'])
            if not stock:
                log.warning(f"Stock {row['symbol']} not found, skipping...")
                continue
            
            # Check if record exists
            existing = self.db.query(MarketData).filter(
                MarketData.stock_id == stock.id,
                MarketData.date == row['Date'].date() if hasattr(row['Date'], 'date') else row['Date']
            ).first()
            
            if existing and upsert:
                # Update existing
                existing.open = float(row['Open']) if pd.notna(row['Open']) else None
                existing.high = float(row['High']) if pd.notna(row['High']) else None
                existing.low = float(row['Low']) if pd.notna(row['Low']) else None
                existing.close = float(row['Close']) if pd.notna(row['Close']) else None
                existing.volume = int(row['Volume']) if pd.notna(row['Volume']) else None
                updated_count += 1
            elif not existing:
                # Insert new
                market_data = MarketData(
                    stock_id=stock.id,
                    date=row['Date'].date() if hasattr(row['Date'], 'date') else row['Date'],
                    open=float(row['Open']) if pd.notna(row['Open']) else None,
                    high=float(row['High']) if pd.notna(row['High']) else None,
                    low=float(row['Low']) if pd.notna(row['Low']) else None,
                    close=float(row['Close']) if pd.notna(row['Close']) else None,
                    volume=int(row['Volume']) if pd.notna(row['Volume']) else None,
                    adjusted_close=float(row['Close']) if pd.notna(row['Close']) else None,
                )
                self.db.add(market_data)
                saved_count += 1
        
        self.db.commit()
        log.info(f"✓ Saved {saved_count} new records, updated {updated_count} records")
    
    def get_market_data(self, symbol: str = None, days: int = 365) -> pd.DataFrame:
        """
        Get market data from database
        
        Args:
            symbol: Stock symbol (None for all stocks)
            days: Number of days to retrieve
        """
        query = self.db.query(MarketData).join(Stock)
        
        if symbol:
            query = query.filter(Stock.symbol == symbol)
        
        # Filter by date
        cutoff_date = datetime.now().date() - timedelta(days=days)
        query = query.filter(MarketData.date >= cutoff_date)
        
        # Order by date
        query = query.order_by(Stock.symbol, MarketData.date)
        
        # Convert to DataFrame
        data = []
        for record in query.all():
            data.append({
                'symbol': record.stock.symbol,
                'Date': record.date,
                'Open': float(record.open) if record.open else None,
                'High': float(record.high) if record.high else None,
                'Low': float(record.low) if record.low else None,
                'Close': float(record.close) if record.close else None,
                'Volume': int(record.volume) if record.volume else None,
            })
        
        return pd.DataFrame(data)
    
    # ==================== RISK SCORE OPERATIONS ====================
    
    def save_risk_scores(self, data: pd.DataFrame, upsert: bool = True):
        """Save risk scores to database"""
        log.info(f"Saving {len(data)} risk score records to database...")
        
        saved_count = 0
        updated_count = 0
        
        for _, row in data.iterrows():
            stock = self.get_stock_by_symbol(row['symbol'])
            if not stock:
                continue
            
            record_date = row['Date'].date() if hasattr(row['Date'], 'date') else row['Date']
            
            # Check if record exists
            existing = self.db.query(RiskScore).filter(
                RiskScore.stock_id == stock.id,
                RiskScore.date == record_date
            ).first()
            
            if existing and upsert:
                # Update existing
                existing.risk_score = float(row['risk_score']) if pd.notna(row.get('risk_score')) else None
                existing.risk_level = row.get('risk_level')
                existing.risk_rank = int(row['risk_rank']) if pd.notna(row.get('risk_rank')) else None
                existing.volatility_21d = float(row.get('volatility_21d', 0)) if pd.notna(row.get('volatility_21d')) else None
                existing.max_drawdown = float(row.get('max_drawdown', 0)) if pd.notna(row.get('max_drawdown')) else None
                existing.risk_drivers = row.get('risk_drivers')
                updated_count += 1
            elif not existing:
                # Insert new
                risk_score = RiskScore(
                    stock_id=stock.id,
                    date=record_date,
                    risk_score=float(row['risk_score']) if pd.notna(row.get('risk_score')) else None,
                    risk_level=row.get('risk_level'),
                    risk_rank=int(row['risk_rank']) if pd.notna(row.get('risk_rank')) else None,
                    volatility_21d=float(row.get('volatility_21d', 0)) if pd.notna(row.get('volatility_21d')) else None,
                    volatility_60d=float(row.get('volatility_60d', 0)) if pd.notna(row.get('volatility_60d')) else None,
                    max_drawdown=float(row.get('max_drawdown', 0)) if pd.notna(row.get('max_drawdown')) else None,
                    beta=float(row.get('beta', 0)) if pd.notna(row.get('beta')) else None,
                    sharpe_ratio=float(row.get('sharpe_ratio', 0)) if pd.notna(row.get('sharpe_ratio')) else None,
                    atr_pct=float(row.get('atr_pct', 0)) if pd.notna(row.get('atr_pct')) else None,
                    liquidity_risk=float(row.get('liquidity_risk', 0)) if pd.notna(row.get('liquidity_risk')) else None,
                    norm_volatility=float(row.get('norm_volatility', 0)) if pd.notna(row.get('norm_volatility')) else None,
                    norm_drawdown=float(row.get('norm_drawdown', 0)) if pd.notna(row.get('norm_drawdown')) else None,
                    norm_sentiment=float(row.get('norm_sentiment', 0)) if pd.notna(row.get('norm_sentiment')) else None,
                    norm_liquidity=float(row.get('norm_liquidity', 0)) if pd.notna(row.get('norm_liquidity')) else None,
                    risk_drivers=row.get('risk_drivers'),
                )
                self.db.add(risk_score)
                saved_count += 1
        
        self.db.commit()
        log.info(f"✓ Saved {saved_count} new records, updated {updated_count} records")
    
    def get_latest_risk_scores(self) -> pd.DataFrame:
        """Get latest risk scores for all stocks with sentiment data"""
        from datetime import datetime, timedelta
        
        # Subquery to get latest date for each stock
        subquery = self.db.query(
            RiskScore.stock_id,
            func.max(RiskScore.date).label('max_date')
        ).group_by(RiskScore.stock_id).subquery()
        
        # Subquery to get average sentiment for last 30 days
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        
        sentiment_subquery = self.db.query(
            SentimentScore.stock_id,
            func.avg(SentimentScore.avg_sentiment).label('avg_sentiment')
        ).filter(
            SentimentScore.date >= thirty_days_ago
        ).group_by(SentimentScore.stock_id).subquery()
        
        # Main query with explicit select_from
        query = (
            self.db.query(
                Stock.symbol,
                RiskScore.date,
                RiskScore.risk_score,
                RiskScore.risk_level,
                RiskScore.risk_rank,
                RiskScore.volatility_21d,
                RiskScore.max_drawdown,
                RiskScore.liquidity_risk,
                RiskScore.risk_drivers,
                RiskScore.norm_volatility,
                RiskScore.norm_drawdown,
                RiskScore.norm_sentiment,
                RiskScore.norm_liquidity,
                sentiment_subquery.c.avg_sentiment
            )
            .select_from(RiskScore)  # ← Explicit FROM clause
            .join(Stock, RiskScore.stock_id == Stock.id)
            .join(
                subquery,
                (RiskScore.stock_id == subquery.c.stock_id) &
                (RiskScore.date == subquery.c.max_date)
            )
            .outerjoin(
                sentiment_subquery,
                RiskScore.stock_id == sentiment_subquery.c.stock_id
            )
            .order_by(RiskScore.risk_rank)
        )
        
        # Convert to DataFrame
        data = []
        for row in query.all():
            data.append({
                'symbol': row.symbol,
                'Date': row.date,
                'Close': None,  # Will need to fetch from market_data if needed
                'risk_score': float(row.risk_score) if row.risk_score else None,
                'risk_level': row.risk_level,
                'risk_rank': row.risk_rank,
                'volatility_21d': float(row.volatility_21d) if row.volatility_21d else None,
                'max_drawdown': float(row.max_drawdown) if row.max_drawdown else None,
                'avg_sentiment': float(row.avg_sentiment) if row.avg_sentiment else 0.0,  # ← FIXED!
                'liquidity_risk': float(row.liquidity_risk) if row.liquidity_risk else None,
                'risk_drivers': row.risk_drivers,
                'norm_volatility': float(row.norm_volatility) if row.norm_volatility else None,
                'norm_drawdown': float(row.norm_drawdown) if row.norm_drawdown else None,
                'norm_sentiment': float(row.norm_sentiment) if row.norm_sentiment else None,
                'norm_liquidity': float(row.norm_liquidity) if row.norm_liquidity else None,
            })
        
        return pd.DataFrame(data)
    
    # ==================== SENTIMENT OPERATIONS ====================
    
    def save_sentiment_scores(self, data: pd.DataFrame, upsert: bool = True):
        """Save sentiment scores to database"""
        log.info(f"Saving {len(data)} sentiment score records to database...")
        
        saved_count = 0
        
        for _, row in data.iterrows():
            stock = self.get_stock_by_symbol(row['stock_symbol'])
            if not stock:
                continue
            
            record_date = row['date'].date() if hasattr(row['date'], 'date') else row['date']
            
            # Check if record exists
            existing = self.db.query(SentimentScore).filter(
                SentimentScore.stock_id == stock.id,
                SentimentScore.date == record_date
            ).first()
            
            if existing and upsert:
                existing.avg_sentiment = float(row['avg_sentiment']) if pd.notna(row['avg_sentiment']) else None
                existing.sentiment_std = float(row.get('sentiment_std', 0)) if pd.notna(row.get('sentiment_std')) else None
                existing.article_count = int(row.get('article_count', 0)) if pd.notna(row.get('article_count')) else 0
            elif not existing:
                sentiment_score = SentimentScore(
                    stock_id=stock.id,
                    date=record_date,
                    avg_sentiment=float(row['avg_sentiment']) if pd.notna(row['avg_sentiment']) else None,
                    sentiment_std=float(row.get('sentiment_std', 0)) if pd.notna(row.get('sentiment_std')) else None,
                    article_count=int(row.get('article_count', 0)) if pd.notna(row.get('article_count')) else 0,
                )
                self.db.add(sentiment_score)
                saved_count += 1
        
        self.db.commit()
        log.info(f"✓ Saved {saved_count} sentiment score records")
    
    def get_recent_sentiment(self, days: int = 7) -> pd.DataFrame:
        """Get recent sentiment scores"""
        cutoff_date = datetime.now().date() - timedelta(days=days)
        
        query = self.db.query(SentimentScore).join(Stock).filter(
            SentimentScore.date >= cutoff_date
        )
        
        data = []
        for record in query.all():
            data.append({
                'stock_symbol': record.stock.symbol,
                'date': record.date,
                'avg_sentiment': float(record.avg_sentiment) if record.avg_sentiment else 0,
                'sentiment_std': float(record.sentiment_std) if record.sentiment_std else 0,
                'article_count': record.article_count,
            })
        
        return pd.DataFrame(data)
    
    # ==================== ALERT OPERATIONS ====================
    
    def save_alerts(self, alerts: List[Dict]):
        """Save alerts to database"""
        log.info(f"Saving {len(alerts)} alerts to database...")
        
        saved_count = 0
        
        for alert_data in alerts:
            stock = self.get_stock_by_symbol(alert_data['symbol'])
            if not stock:
                continue
            
            alert = Alert(
                stock_id=stock.id,
                alert_type=alert_data.get('alert_type'),
                severity=alert_data.get('severity'),
                risk_score=float(alert_data.get('risk_score', 0)) if alert_data.get('risk_score') else None,
                prev_risk_score=float(alert_data.get('prev_risk_score', 0)) if alert_data.get('prev_risk_score') else None,
                risk_change=float(alert_data.get('risk_change', 0)) if alert_data.get('risk_change') else None,
                risk_change_pct=float(alert_data.get('risk_change_pct', 0)) if alert_data.get('risk_change_pct') else None,
                risk_level=alert_data.get('risk_level'),
                risk_drivers=alert_data.get('risk_drivers'),
                explanation=alert_data.get('explanation'),
                created_at=alert_data.get('timestamp', datetime.utcnow()),
            )
            self.db.add(alert)
            saved_count += 1
        
        self.db.commit()
        log.info(f"✓ Saved {saved_count} alerts")
    
    def get_recent_alerts(self, limit: int = 100) -> List[Dict]:
        """Get recent alerts"""
        query = self.db.query(Alert).join(Stock).order_by(
            desc(Alert.created_at)
        ).limit(limit)
        
        alerts = []
        for record in query.all():
            alerts.append({
                'symbol': record.stock.symbol,
                'alert_type': record.alert_type,
                'severity': record.severity,
                'risk_score': float(record.risk_score) if record.risk_score else None,
                'prev_risk_score': float(record.prev_risk_score) if record.prev_risk_score else None,
                'risk_change': float(record.risk_change) if record.risk_change else None,
                'risk_change_pct': float(record.risk_change_pct) if record.risk_change_pct else None,
                'risk_level': record.risk_level,
                'risk_drivers': record.risk_drivers,
                'explanation': record.explanation,
                'timestamp': record.created_at,
            })
        
        return alerts
    
    # ==================== RISK HISTORY OPERATIONS ====================
    
    def save_risk_history(self, data: pd.DataFrame):
        """Save risk history"""
        log.info(f"Saving {len(data)} risk history records...")
        
        for _, row in data.iterrows():
            stock = self.get_stock_by_symbol(row['symbol'])
            if not stock:
                continue
            
            risk_history = RiskHistory(
                stock_id=stock.id,
                risk_score=float(row['risk_score']) if pd.notna(row['risk_score']) else None,
                risk_level=row.get('risk_level'),
                timestamp=datetime.utcnow(),
            )
            self.db.add(risk_history)
        
        self.db.commit()
        log.info(f"✓ Saved risk history")
    
    def get_risk_history(self, symbol: str = None, days: int = 30) -> pd.DataFrame:
        """Get risk history"""
        query = self.db.query(RiskHistory).join(Stock)
        
        if symbol:
            query = query.filter(Stock.symbol == symbol)
        
        cutoff_date = datetime.now() - timedelta(days=days)
        query = query.filter(RiskHistory.timestamp >= cutoff_date)
        query = query.order_by(RiskHistory.timestamp)
        
        data = []
        for record in query.all():
            data.append({
                'symbol': record.stock.symbol,
                'risk_score': float(record.risk_score) if record.risk_score else None,
                'risk_level': record.risk_level,
                'timestamp': record.timestamp,
            })
        
        return pd.DataFrame(data)
    
    def get_market_data_with_features(self, symbol: str, days: int = 90) -> pd.DataFrame:
        """Get market data with computed features for charting"""
        query = self.db.query(MarketData).join(Stock).filter(
            Stock.symbol == symbol
        )
        
        # Filter by date
        cutoff_date = datetime.now().date() - timedelta(days=days)
        query = query.filter(MarketData.date >= cutoff_date)
        query = query.order_by(MarketData.date)
        
        # Convert to DataFrame
        data = []
        for record in query.all():
            data.append({
                'Date': record.date,
                'Open': float(record.open) if record.open else None,
                'High': float(record.high) if record.high else None,
                'Low': float(record.low) if record.low else None,
                'Close': float(record.close) if record.close else None,
                'Volume': int(record.volume) if record.volume else None,
            })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return df
        
        # Compute volatility for chart
        df['returns'] = df['Close'].pct_change()
        df['volatility_21d'] = df['returns'].rolling(window=21, min_periods=10).std() * np.sqrt(252)
        
        return df