"""
Test Risk Scoring Agent
"""
from backend.utils import log
from backend.agents import RiskScoringAgent
import pandas as pd

def main():
    """Test risk scoring agent"""
    log.info("=" * 60)
    log.info("TESTING RISK SCORING AGENT")
    log.info("=" * 60)
    
    # Initialize and run agent
    agent = RiskScoringAgent()
    risk_df = agent.run()
    
    # Display top risky stocks
    log.info("\n" + "=" * 60)
    log.info("TOP 10 HIGHEST RISK STOCKS")
    log.info("=" * 60)
    
    top_risk = risk_df.head(10)
    display_cols = ['symbol', 'risk_score', 'risk_level', 'risk_rank', 'risk_drivers']
    print(top_risk[display_cols].to_string(index=False))
    
    # Display lowest risk stocks
    log.info("\n" + "=" * 60)
    log.info("TOP 10 LOWEST RISK STOCKS")
    log.info("=" * 60)
    
    low_risk = risk_df.tail(10)
    print(low_risk[display_cols].to_string(index=False))
    
    # Statistics
    log.info("\n" + "=" * 60)
    log.info("RISK SCORE STATISTICS")
    log.info("=" * 60)
    
    print(risk_df['risk_score'].describe().to_string())
    
    # Component analysis
    log.info("\n" + "=" * 60)
    log.info("RISK COMPONENT CONTRIBUTIONS")
    log.info("=" * 60)
    
    component_cols = ['norm_volatility', 'norm_drawdown', 'norm_sentiment', 'norm_liquidity']
    print(risk_df[component_cols].mean().to_string())
    
    # Risk level distribution
    log.info("\n" + "=" * 60)
    log.info("RISK LEVEL DISTRIBUTION")
    log.info("=" * 60)
    
    risk_dist = risk_df['risk_level'].value_counts()
    for level, count in risk_dist.items():
        pct = (count / len(risk_df)) * 100
        log.info(f"{level}: {count} stocks ({pct:.1f}%)")
    
    log.info("\n" + "=" * 60)
    log.info("✓ RISK SCORING AGENT TEST COMPLETE")
    log.info("=" * 60)

if __name__ == "__main__":
    main()