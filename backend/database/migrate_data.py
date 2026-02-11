"""
Migrate existing CSV/Parquet data to PostgreSQL
"""
import pandas as pd
from datetime import datetime
from sqlalchemy import exists
from tqdm import tqdm
from backend.database.models import (
    SessionLocal, Stock, MarketData, RiskScore, NewsArticle,
    SentimentScore, Alert, RiskHistory
)
from backend.utils import log, load_config

class DataMigration:
    """Handle data migration from CSV/Parquet to PostgreSQL"""
    
    def __init__(self):
        self.config = load_config()
        self.db = SessionLocal()
        self.stats = {
            'market_data': 0,
            'risk_scores': 0,
            'news_articles': 0,
            'sentiment_scores': 0,
            'alerts': 0,
            'risk_history': 0,
        }
    
    def __del__(self):
        """Close database session"""
        self.db.close()
    
    def get_stock_id(self, symbol: str) -> int:
        """Get stock ID from symbol"""
        stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
        if stock:
            return stock.id
        else:
            # Create stock if doesn't exist
            log.warning(f"Stock {symbol} not found, creating...")
            new_stock = Stock(symbol=symbol, name=symbol, sector='Unknown', industry='Unknown')
            self.db.add(new_stock)
            self.db.commit()
            return new_stock.id
    
    def migrate_market_data(self):
        """Migrate market data from Parquet"""
        log.info("=" * 60)
        log.info("MIGRATING MARKET DATA")
        log.info("=" * 60)
        
        filepath = f"{self.config['paths']['data_raw']}/stocks_data.parquet"
        
        try:
            df = pd.read_parquet(filepath)
            log.info(f"Loaded {len(df)} rows from {filepath}")
            
            # Convert Date column to datetime
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Process in batches
            batch_size = 1000
            total_rows = len(df)
            
            with tqdm(total=total_rows, desc="Market Data") as pbar:
                for i in range(0, total_rows, batch_size):
                    batch = df.iloc[i:i+batch_size]
                    
                    for _, row in batch.iterrows():
                        stock_id = self.get_stock_id(row['symbol'])
                        
                        # Check if record exists
                        exists_query = self.db.query(MarketData).filter(
                            MarketData.stock_id == stock_id,
                            MarketData.date == row['Date'].date()
                        ).first()
                        
                        if not exists_query:
                            market_data = MarketData(
                                stock_id=stock_id,
                                date=row['Date'].date(),
                                open=float(row['Open']) if pd.notna(row['Open']) else None,
                                high=float(row['High']) if pd.notna(row['High']) else None,
                                low=float(row['Low']) if pd.notna(row['Low']) else None,
                                close=float(row['Close']) if pd.notna(row['Close']) else None,
                                volume=int(row['Volume']) if pd.notna(row['Volume']) else None,
                                adjusted_close=float(row['Close']) if pd.notna(row['Close']) else None,
                            )
                            self.db.add(market_data)
                            self.stats['market_data'] += 1
                    
                    self.db.commit()
                    pbar.update(len(batch))
            
            log.info(f"✓ Migrated {self.stats['market_data']} market data records")
            
        except FileNotFoundError:
            log.warning(f"File not found: {filepath}")
        except Exception as e:
            log.error(f"Error migrating market data: {str(e)}")
            self.db.rollback()
    
    def migrate_risk_scores(self):
        """Migrate risk scores from CSV"""
        log.info("=" * 60)
        log.info("MIGRATING RISK SCORES")
        log.info("=" * 60)
        
        filepath = f"{self.config['paths']['data_processed']}/risk_scores.csv"
        
        try:
            df = pd.read_csv(filepath)
            log.info(f"Loaded {len(df)} rows from {filepath}")
            
            # Convert Date column
            df['Date'] = pd.to_datetime(df['Date'])
            
            with tqdm(total=len(df), desc="Risk Scores") as pbar:
                for _, row in df.iterrows():
                    stock_id = self.get_stock_id(row['symbol'])
                    
                    # Check if record exists
                    exists_query = self.db.query(RiskScore).filter(
                        RiskScore.stock_id == stock_id,
                        RiskScore.date == row['Date'].date()
                    ).first()
                    
                    if not exists_query:
                        risk_score = RiskScore(
                            stock_id=stock_id,
                            date=row['Date'].date(),
                            risk_score=float(row['risk_score']) if pd.notna(row['risk_score']) else None,
                            risk_level=row.get('risk_level'),
                            risk_rank=int(row['risk_rank']) if pd.notna(row.get('risk_rank')) else None,
                            volatility_21d=float(row['volatility_21d']) if pd.notna(row.get('volatility_21d')) else None,
                            volatility_60d=float(row.get('volatility_60d', 0)) if pd.notna(row.get('volatility_60d')) else None,
                            max_drawdown=float(row['max_drawdown']) if pd.notna(row.get('max_drawdown')) else None,
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
                        self.stats['risk_scores'] += 1
                    
                    pbar.update(1)
                
                self.db.commit()
            
            log.info(f"✓ Migrated {self.stats['risk_scores']} risk score records")
            
        except FileNotFoundError:
            log.warning(f"File not found: {filepath}")
        except Exception as e:
            log.error(f"Error migrating risk scores: {str(e)}")
            self.db.rollback()
    
    def migrate_news_articles(self):
        """Migrate news articles from CSV"""
        log.info("=" * 60)
        log.info("MIGRATING NEWS ARTICLES")
        log.info("=" * 60)
        
        filepath = f"{self.config['paths']['data_processed']}/news_with_sentiment.csv"
        
        try:
            df = pd.read_csv(filepath)
            log.info(f"Loaded {len(df)} rows from {filepath}")
            
            # Convert dates
            if 'published_date' in df.columns:
                df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce')
            
            with tqdm(total=len(df), desc="News Articles") as pbar:
                for _, row in df.iterrows():
                    stock_symbol = row.get('stock_symbol', 'GENERAL')
                    stock_id = self.get_stock_id(stock_symbol) if stock_symbol != 'GENERAL' else None
                    
                    news_article = NewsArticle(
                        stock_id=stock_id,
                        source=row.get('source'),
                        headline=row.get('headline', ''),
                        description=row.get('description'),
                        url=row.get('url'),
                        published_date=row.get('published_date') if pd.notna(row.get('published_date')) else None,
                        sentiment_label=row.get('sentiment_label'),
                        sentiment_score=float(row['sentiment_score']) if pd.notna(row.get('sentiment_score')) else None,
                        sentiment_confidence=float(row.get('sentiment_confidence', 0)) if pd.notna(row.get('sentiment_confidence')) else None,
                    )
                    self.db.add(news_article)
                    self.stats['news_articles'] += 1
                    
                    pbar.update(1)
                
                self.db.commit()
            
            log.info(f"✓ Migrated {self.stats['news_articles']} news articles")
            
        except FileNotFoundError:
            log.warning(f"File not found: {filepath}")
        except Exception as e:
            log.error(f"Error migrating news articles: {str(e)}")
            self.db.rollback()
    
    def migrate_sentiment_scores(self):
        """Migrate sentiment scores from CSV"""
        log.info("=" * 60)
        log.info("MIGRATING SENTIMENT SCORES")
        log.info("=" * 60)
        
        filepath = f"{self.config['paths']['data_processed']}/sentiment_scores.csv"
        
        try:
            df = pd.read_csv(filepath)
            log.info(f"Loaded {len(df)} rows from {filepath}")
            
            # Convert date
            df['date'] = pd.to_datetime(df['date'])
            
            with tqdm(total=len(df), desc="Sentiment Scores") as pbar:
                for _, row in df.iterrows():
                    stock_id = self.get_stock_id(row['stock_symbol'])
                    
                    # Check if record exists
                    exists_query = self.db.query(SentimentScore).filter(
                        SentimentScore.stock_id == stock_id,
                        SentimentScore.date == row['date'].date()
                    ).first()
                    
                    if not exists_query:
                        sentiment_score = SentimentScore(
                            stock_id=stock_id,
                            date=row['date'].date(),
                            avg_sentiment=float(row['avg_sentiment']) if pd.notna(row['avg_sentiment']) else None,
                            sentiment_std=float(row['sentiment_std']) if pd.notna(row['sentiment_std']) else None,
                            article_count=int(row['article_count']) if pd.notna(row['article_count']) else 0,
                        )
                        self.db.add(sentiment_score)
                        self.stats['sentiment_scores'] += 1
                    
                    pbar.update(1)
                
                self.db.commit()
            
            log.info(f"✓ Migrated {self.stats['sentiment_scores']} sentiment score records")
            
        except FileNotFoundError:
            log.warning(f"File not found: {filepath}")
        except Exception as e:
            log.error(f"Error migrating sentiment scores: {str(e)}")
            self.db.rollback()
    
    def migrate_alerts(self):
        """Migrate alerts from CSV"""
        log.info("=" * 60)
        log.info("MIGRATING ALERTS")
        log.info("=" * 60)
        
        filepath = f"{self.config['paths']['data_processed']}/alerts.csv"
        
        try:
            df = pd.read_csv(filepath)
            log.info(f"Loaded {len(df)} rows from {filepath}")
            
            # Convert timestamp
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            with tqdm(total=len(df), desc="Alerts") as pbar:
                for _, row in df.iterrows():
                    stock_id = self.get_stock_id(row['symbol'])
                    
                    alert = Alert(
                        stock_id=stock_id,
                        alert_type=row.get('alert_type'),
                        severity=row.get('severity'),
                        risk_score=float(row['risk_score']) if pd.notna(row.get('risk_score')) else None,
                        prev_risk_score=float(row.get('prev_risk_score', 0)) if pd.notna(row.get('prev_risk_score')) else None,
                        risk_change=float(row.get('risk_change', 0)) if pd.notna(row.get('risk_change')) else None,
                        risk_change_pct=float(row.get('risk_change_pct', 0)) if pd.notna(row.get('risk_change_pct')) else None,
                        risk_level=row.get('risk_level'),
                        risk_drivers=row.get('risk_drivers'),
                        explanation=row.get('explanation'),
                        created_at=row.get('timestamp') if pd.notna(row.get('timestamp')) else datetime.utcnow(),
                    )
                    self.db.add(alert)
                    self.stats['alerts'] += 1
                    
                    pbar.update(1)
                
                self.db.commit()
            
            log.info(f"✓ Migrated {self.stats['alerts']} alerts")
            
        except FileNotFoundError:
            log.warning(f"File not found: {filepath}")
        except Exception as e:
            log.error(f"Error migrating alerts: {str(e)}")
            self.db.rollback()
    
    def migrate_risk_history(self):
        """Migrate risk history from CSV"""
        log.info("=" * 60)
        log.info("MIGRATING RISK HISTORY")
        log.info("=" * 60)
        
        filepath = f"{self.config['paths']['data_processed']}/risk_history.csv"
        
        try:
            df = pd.read_csv(filepath)
            log.info(f"Loaded {len(df)} rows from {filepath}")
            
            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            with tqdm(total=len(df), desc="Risk History") as pbar:
                for _, row in df.iterrows():
                    stock_id = self.get_stock_id(row['symbol'])
                    
                    risk_history = RiskHistory(
                        stock_id=stock_id,
                        risk_score=float(row['risk_score']) if pd.notna(row['risk_score']) else None,
                        risk_level=row.get('risk_level'),
                        timestamp=row['timestamp'],
                    )
                    self.db.add(risk_history)
                    self.stats['risk_history'] += 1
                    
                    pbar.update(1)
                
                self.db.commit()
            
            log.info(f"✓ Migrated {self.stats['risk_history']} risk history records")
            
        except FileNotFoundError:
            log.warning(f"File not found: {filepath}")
        except Exception as e:
            log.error(f"Error migrating risk history: {str(e)}")
            self.db.rollback()
    
    def run_all(self):
        """Run all migrations"""
        log.info("=" * 60)
        log.info("STARTING DATA MIGRATION")
        log.info("=" * 60)
        
        start_time = datetime.now()
        
        # Run migrations in order
        self.migrate_market_data()
        self.migrate_risk_scores()
        self.migrate_sentiment_scores()
        self.migrate_news_articles()
        self.migrate_alerts()
        self.migrate_risk_history()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Print summary
        log.info("=" * 60)
        log.info("MIGRATION SUMMARY")
        log.info("=" * 60)
        log.info(f"Market Data: {self.stats['market_data']} records")
        log.info(f"Risk Scores: {self.stats['risk_scores']} records")
        log.info(f"Sentiment Scores: {self.stats['sentiment_scores']} records")
        log.info(f"News Articles: {self.stats['news_articles']} records")
        log.info(f"Alerts: {self.stats['alerts']} records")
        log.info(f"Risk History: {self.stats['risk_history']} records")
        log.info(f"Total Time: {duration:.2f} seconds")
        log.info("=" * 60)
        log.info("✓ MIGRATION COMPLETED SUCCESSFULLY")
        log.info("=" * 60)

def main():
    """Main migration entry point"""
    migration = DataMigration()
    migration.run_all()

if __name__ == "__main__":
    main()