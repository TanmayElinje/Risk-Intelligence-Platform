"""
Risk Scoring Agent - Compute composite risk scores
Now using PostgreSQL for data persistence
"""
import pandas as pd
import numpy as np
from backend.utils import log, load_config
from backend.database import DatabaseService
from datetime import datetime

class RiskScoringAgent:
    """
    Agent responsible for computing composite risk scores
    """
    
    def __init__(self):
        self.config = load_config()
        self.weights = {
            'volatility': 0.4,
            'drawdown': 0.3,
            'sentiment': 0.2,
            'liquidity': 0.1
        }
    
    def normalize_feature(self, series: pd.Series, inverse: bool = False) -> pd.Series:
        """
        Normalize feature to 0-1 range
        
        Args:
            series: Feature series
            inverse: If True, higher values = lower risk (e.g., for sentiment)
        """
        min_val = series.min()
        max_val = series.max()
        
        if max_val == min_val:
            return pd.Series([0.5] * len(series), index=series.index)
        
        normalized = (series - min_val) / (max_val - min_val)
        
        if inverse:
            normalized = 1 - normalized
        
        return normalized
    
    def compute_risk_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute composite risk score
        
        Components:
        - Volatility (40%): Higher volatility = higher risk
        - Max Drawdown (30%): Larger drawdown = higher risk
        - Sentiment (20%): Negative sentiment = higher risk
        - Liquidity (10%): Lower liquidity = higher risk
        """
        log.info("Computing composite risk scores...")
        
        df = df.copy()
        
        # Normalize components
        df['norm_volatility'] = self.normalize_feature(df['volatility_21d'])
        df['norm_drawdown'] = self.normalize_feature(df['max_drawdown'].abs())
        df['norm_sentiment'] = self.normalize_feature(df['avg_sentiment'], inverse=True)
        df['norm_liquidity'] = self.normalize_feature(df['liquidity_risk'])
        
        # Handle NaN values
        df['norm_volatility'] = df['norm_volatility'].fillna(0.5)
        df['norm_drawdown'] = df['norm_drawdown'].fillna(0.5)
        df['norm_sentiment'] = df['norm_sentiment'].fillna(0.5)
        df['norm_liquidity'] = df['norm_liquidity'].fillna(0.5)
        
        # Compute weighted risk score
        df['risk_score'] = (
            df['norm_volatility'] * self.weights['volatility'] +
            df['norm_drawdown'] * self.weights['drawdown'] +
            df['norm_sentiment'] * self.weights['sentiment'] +
            df['norm_liquidity'] * self.weights['liquidity']
        )
        
        # Classify risk level
        df['risk_level'] = pd.cut(
            df['risk_score'],
            bins=[0, 0.3, 0.6, 1.0],
            labels=['Low', 'Medium', 'High']
        )
        
        # Rank stocks by risk
        df['risk_rank'] = df['risk_score'].rank(ascending=False, method='min').astype(int)
        
        # Generate risk drivers explanation
        df['risk_drivers'] = df.apply(self._generate_risk_drivers, axis=1)
        
        log.info(f"✓ Computed risk scores for {len(df)} stocks")
        
        return df
    
    def _generate_risk_drivers(self, row) -> str:
        """Generate human-readable risk drivers"""
        drivers = []
        
        if row['norm_volatility'] > 0.7:
            drivers.append("High volatility")
        if row['norm_drawdown'] > 0.7:
            drivers.append("Significant drawdown")
        if row['norm_sentiment'] > 0.6:
            drivers.append("Negative news sentiment")
        if row['norm_liquidity'] > 0.6:
            drivers.append("Liquidity concerns")
        
        if not drivers:
            drivers.append("Stable metrics")
        
        return " | ".join(drivers)
    
    def process(self):
        """
        Main processing method - Load features and sentiment, compute risk, save to DB
        """
        log.info("=" * 60)
        log.info("RISK SCORING AGENT - Computing Risk Scores")
        log.info("=" * 60)
        
        with DatabaseService() as db:
            # Get latest market data with features
            log.info("Loading market features from database...")
            market_data = db.get_market_data(days=365)
            
            if market_data.empty:
                log.error("No market data found!")
                return None
            
            # We need to recompute features first (or load from a features table)
            # For now, let's get the latest risk scores as they already have features
            log.info("Loading latest risk scores...")
            risk_scores = db.get_latest_risk_scores()
            
            if risk_scores.empty:
                log.error("No risk scores found! Run market agent first.")
                return None
            
            # Get recent sentiment (7-day average)
            log.info("Loading recent sentiment...")
            sentiment_data = db.get_recent_sentiment(days=7)
            
            # Aggregate sentiment by stock
            if not sentiment_data.empty:
                sentiment_avg = sentiment_data.groupby('stock_symbol').agg({
                    'avg_sentiment': 'mean'
                }).reset_index()
                
                # Merge with risk scores
                risk_scores = risk_scores.merge(
                    sentiment_avg,
                    left_on='symbol',
                    right_on='stock_symbol',
                    how='left'
                )
                risk_scores['avg_sentiment'] = risk_scores['avg_sentiment_y'].fillna(0)
            else:
                risk_scores['avg_sentiment'] = 0
            
            # Add current date
            risk_scores['Date'] = datetime.now().date()
            
            # Note: In full implementation, we'd recompute features from market_data
            # For now, we're using existing risk scores
            log.info("Risk scores already computed from previous run")
            log.info(f"Found {len(risk_scores)} stocks with risk scores")
            
            # Save to database
            log.info("Saving risk scores to database...")
            db.save_risk_scores(risk_scores)
            
            # Save to risk history for trending
            log.info("Saving to risk history...")
            db.save_risk_history(risk_scores[['symbol', 'risk_score', 'risk_level']])
            
            log.info("=" * 60)
            log.info("✓ RISK SCORING AGENT COMPLETED SUCCESSFULLY")
            log.info("=" * 60)
            
            return risk_scores

def main():
    """Main execution"""
    agent = RiskScoringAgent()
    risk_scores = agent.process()
    
    if risk_scores is not None:
        # Print summary
        print("\nRisk Distribution:")
        print(risk_scores['risk_level'].value_counts())
        print(f"\nTop 5 Risky Stocks:")
        print(risk_scores.nlargest(5, 'risk_score')[['symbol', 'risk_score', 'risk_level', 'risk_drivers']])

if __name__ == "__main__":
    main()