"""
Populate risk history with backdated entries for trending
"""
from datetime import datetime, timedelta
from backend.database import DatabaseService
from backend.database.models import RiskHistory
from backend.utils import log
import random

def populate_risk_history():
    """Create 30 days of risk history for trending"""
    log.info("Populating risk history with backdated entries...")
    
    with DatabaseService() as db:
        # Get latest risk scores
        risk_scores = db.get_latest_risk_scores()
        
        # Generate 30 days of history
        for days_ago in range(30, 0, -1):
            timestamp = datetime.now() - timedelta(days=days_ago)
            
            if days_ago % 5 == 0:
                log.info(f"Creating entries for {days_ago} days ago ({timestamp.date()})...")
            
            for _, stock in risk_scores.iterrows():
                # Add some random variation to create a trend
                base_risk = float(stock['risk_score'])
                
                # Create realistic variation (risk tends to change gradually)
                variation = random.uniform(-0.05, 0.05)
                # Add some trend (risk slightly increases over time for demo)
                trend = (30 - days_ago) * 0.002
                
                risk_score = max(0.1, min(0.95, base_risk + variation - trend))
                
                # Determine risk level
                if risk_score > 0.6:
                    risk_level = 'High'
                elif risk_score > 0.3:
                    risk_level = 'Medium'
                else:
                    risk_level = 'Low'
                
                risk_history = RiskHistory(
                    stock_id=db.get_stock_by_symbol(stock['symbol']).id,
                    risk_score=risk_score,
                    risk_level=risk_level,
                    timestamp=timestamp
                )
                db.db.add(risk_history)
            
            if days_ago % 5 == 0:
                db.db.commit()
        
        db.db.commit()
        log.info("✓ Risk history populated with 30 days of data")

if __name__ == "__main__":
    populate_risk_history()