"""
Test Sentiment Agent
"""
from backend.utils import log
from backend.agents import SentimentAgent
import pandas as pd

def main():
    """Test sentiment agent"""
    log.info("=" * 60)
    log.info("TESTING SENTIMENT AGENT")
    log.info("=" * 60)
    
    # Initialize and run agent
    agent = SentimentAgent()
    sentiment_df = agent.run()
    
    if sentiment_df.empty:
        log.warning("No sentiment data generated")
        return
    
    # Display sample results
    log.info("\n" + "=" * 60)
    log.info("SAMPLE DAILY SENTIMENT SCORES")
    log.info("=" * 60)
    
    print(sentiment_df.head(10).to_string())
    
    log.info("\n" + "=" * 60)
    log.info("SENTIMENT STATISTICS")
    log.info("=" * 60)
    
    print(sentiment_df[['avg_sentiment', 'sentiment_std', 'article_count']].describe().to_string())
    
    # Show sentiment distribution by stock
    log.info("\n" + "=" * 60)
    log.info("AVERAGE SENTIMENT BY STOCK (Top 10)")
    log.info("=" * 60)
    
    avg_by_stock = sentiment_df.groupby('stock_symbol')['avg_sentiment'].mean().sort_values(ascending=False)
    print(avg_by_stock.head(10).to_string())
    
    log.info("\n" + "=" * 60)
    log.info("✓ SENTIMENT AGENT TEST COMPLETE")
    log.info("=" * 60)

if __name__ == "__main__":
    main()