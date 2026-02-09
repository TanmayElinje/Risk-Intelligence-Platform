"""
Test Market Data Agent
"""
from backend.utils import log
from backend.agents import MarketDataAgent

def main():
    """Test market data agent"""
    log.info("=" * 60)
    log.info("TESTING MARKET DATA AGENT")
    log.info("=" * 60)
    
    # Initialize and run agent
    agent = MarketDataAgent()
    features_df = agent.run()
    
    # Display sample results
    log.info("\n" + "=" * 60)
    log.info("SAMPLE RESULTS FOR AAPL")
    log.info("=" * 60)
    
    aapl_data = features_df[features_df['symbol'] == 'AAPL'].tail(10)
    
    display_cols = [
        'Date', 'Close', 'returns', 'volatility_21d', 
        'max_drawdown', 'beta', 'sharpe_ratio', 'atr_pct', 'liquidity_risk'
    ]
    
    print(aapl_data[display_cols].to_string())
    
    log.info("\n" + "=" * 60)
    log.info("FEATURE STATISTICS")
    log.info("=" * 60)
    
    stats_cols = ['returns', 'volatility_21d', 'volatility_60d', 'max_drawdown', 
                  'beta', 'sharpe_ratio', 'atr_pct', 'liquidity_risk']
    
    print(features_df[stats_cols].describe().to_string())
    
    log.info("\n" + "=" * 60)
    log.info("✓ MARKET DATA AGENT TEST COMPLETE")
    log.info("=" * 60)

if __name__ == "__main__":
    main()