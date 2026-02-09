"""
Main orchestration script for Risk Intelligence Platform
"""
from backend.utils import log, load_config
from backend.pipelines.data_collection import DataCollectionPipeline
from backend.agents import MarketDataAgent, SentimentAgent, NewsRAGAgent, RiskScoringAgent, AlertAgent

def main():
    """
    Main execution pipeline
    """
    log.info("=" * 60)
    log.info("Financial Risk Intelligence Platform - Starting")
    log.info("=" * 60)
    
    config = load_config()
    log.info(f"Loaded configuration for {config['app']['name']} v{config['app']['version']}")
    
    # Step 1: Data Collection
    log.info("\n" + "=" * 60)
    log.info("STEP 1: DATA COLLECTION")
    log.info("=" * 60)
    
    pipeline = DataCollectionPipeline()
    data = pipeline.run_full_pipeline(use_synthetic=False)
    
    # Step 2: Market Feature Computation
    log.info("\n" + "=" * 60)
    log.info("STEP 2: MARKET FEATURE COMPUTATION")
    log.info("=" * 60)
    
    market_agent = MarketDataAgent()
    features_df = market_agent.run()
    
    # Step 3: Sentiment Analysis
    log.info("\n" + "=" * 60)
    log.info("STEP 3: SENTIMENT ANALYSIS")
    log.info("=" * 60)
    
    sentiment_agent = SentimentAgent()
    sentiment_df = sentiment_agent.run()
    
    # Step 4: RAG Knowledge Base
    log.info("\n" + "=" * 60)
    log.info("STEP 4: RAG KNOWLEDGE BASE")
    log.info("=" * 60)
    
    rag_agent = NewsRAGAgent()
    vector_store = rag_agent.run()
    
    # Step 5: Risk Scoring
    log.info("\n" + "=" * 60)
    log.info("STEP 5: RISK SCORING")
    log.info("=" * 60)
    
    risk_agent = RiskScoringAgent()
    risk_df = risk_agent.run()
    
    # Step 6: Alert Generation
    log.info("\n" + "=" * 60)
    log.info("STEP 6: ALERT GENERATION")
    log.info("=" * 60)
    
    alert_agent = AlertAgent()
    alerts = alert_agent.run()
    
    # Final Summary
    log.info("\n" + "=" * 70)
    log.info("PIPELINE EXECUTION SUMMARY")
    log.info("=" * 70)
    log.info(f"✓ Market data: {len(features_df)} rows processed")
    log.info(f"✓ Sentiment scores: {len(sentiment_df)} daily aggregates")
    log.info(f"✓ RAG documents indexed: {vector_store.index.ntotal if vector_store else 0}")
    log.info(f"✓ Risk scores computed: {len(risk_df)} stocks")
    log.info(f"✓ High risk stocks: {(risk_df['risk_level'] == 'High').sum()}")
    log.info(f"✓ Alerts generated: {len(alerts)}")
    log.info("=" * 70)
    
    log.info("\n" + "=" * 60)
    log.info("✅ PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
    log.info("=" * 60)

if __name__ == "__main__":
    main()