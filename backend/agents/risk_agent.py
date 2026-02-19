"""
Risk Scoring Agent - Compute composite risk scores
Uses ML model (XGBoost) when available, falls back to manual weighted formula.
"""
import pandas as pd
import numpy as np
from backend.utils import log, load_config
from backend.database import DatabaseService
from datetime import datetime

class RiskScoringAgent:
    """
    Agent responsible for computing composite risk scores.
    Tries ML model first, falls back to manual formula.
    """
    
    def __init__(self):
        self.config = load_config()
        self.ml_scorer = None
        self._try_load_ml()
        self.weights = {
            'volatility': 0.4,
            'drawdown': 0.3,
            'sentiment': 0.2,
            'liquidity': 0.1
        }
    
    def _try_load_ml(self):
        """Try to load the ML risk scorer."""
        try:
            from backend.services.ml_risk_scorer import MLRiskScorer
            self.ml_scorer = MLRiskScorer()
            if self.ml_scorer.is_ml_available:
                log.info("ML Risk Model loaded successfully")
            else:
                log.info("ML model files not found — using manual formula")
                self.ml_scorer = None
        except Exception as e:
            log.warning(f"Could not load ML scorer: {e}")
            self.ml_scorer = None
    
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
        Main processing method - Load features and sentiment, compute risk, save to DB.
        Uses ML model when available, falls back to manual scoring.
        """
        log.info("=" * 60)
        log.info("RISK SCORING AGENT - Computing Risk Scores")
        log.info("=" * 60)
        
        with DatabaseService() as db:
            # Try ML-based scoring first
            if self.ml_scorer and self.ml_scorer.is_ml_available:
                log.info("Using ML model for risk scoring...")
                return self._process_ml(db)
            else:
                log.info("Using manual formula for risk scoring...")
                return self._process_manual(db)
    
    def _process_ml(self, db):
        """Score stocks using SHAP pre-computed scores (calibrated from training pipeline)."""
        try:
            result_df = self.ml_scorer.score_stocks_from_shap()
            
            if result_df.empty:
                log.warning("SHAP scores not available, falling back to manual")
                return self._process_manual(db)
            
            # Add required columns for DB compatibility
            result_df['avg_sentiment'] = 0.0
            result_df['norm_volatility'] = result_df['risk_score']
            result_df['norm_drawdown'] = 0.5
            result_df['norm_sentiment'] = 0.5
            result_df['norm_liquidity'] = 0.5
            result_df['Date'] = datetime.now().date()
            
            # Save to DB
            log.info("Saving ML risk scores to database...")
            db.save_risk_scores(result_df, upsert=True)
            
            try:
                db.save_risk_history(result_df[['symbol', 'risk_score', 'risk_level']])
                log.info("Risk history updated")
            except Exception as e:
                log.warning(f"Could not save risk history: {e}")
            
            log.info("=" * 60)
            log.info(f"ML RISK SCORING COMPLETE — {len(result_df)} stocks scored")
            log.info("=" * 60)
            
            return result_df
            
        except Exception as e:
            log.error(f"ML scoring failed: {e}")
            import traceback
            traceback.print_exc()
            return self._process_manual(db)
    
    def _process_manual(self, db):
        """Fallback: manual weighted formula risk scoring."""
        log.info("Loading market features from database...")
        market_data = db.get_market_data(days=365)
        
        if market_data.empty:
            log.error("No market data found!")
            return None
        
        log.info("Loading latest risk scores...")
        risk_scores = db.get_latest_risk_scores()
        
        if risk_scores.empty:
            log.error("No risk scores found! Run market agent first.")
            return None
        
        log.info("Loading recent sentiment...")
        sentiment_data = db.get_recent_sentiment(days=7)
        
        if not sentiment_data.empty:
            sentiment_avg = sentiment_data.groupby('stock_symbol').agg({
                'avg_sentiment': 'mean'
            }).reset_index()
            risk_scores = risk_scores.merge(
                sentiment_avg, left_on='symbol', right_on='stock_symbol', how='left'
            )
            risk_scores['avg_sentiment'] = risk_scores['avg_sentiment_y'].fillna(0)
        else:
            risk_scores['avg_sentiment'] = 0
        
        risk_scores['Date'] = datetime.now().date()
        
        log.info(f"Found {len(risk_scores)} stocks with risk scores")
        
        db.save_risk_scores(risk_scores)
        
        try:
            db.save_risk_history(risk_scores[['symbol', 'risk_score', 'risk_level']])
        except Exception as e:
            log.warning(f"Could not save risk history: {e}")
        
        log.info("✓ MANUAL RISK SCORING COMPLETED")
        
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