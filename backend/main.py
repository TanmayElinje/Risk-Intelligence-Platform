"""
Main Pipeline - Orchestrate all agents with PostgreSQL
"""
import sys
from backend.utils import log, load_config
from backend.database import DatabaseService
from backend.agents.market_agent import MarketDataAgent
from backend.agents.sentiment_agent import SentimentAgent
from backend.agents.risk_agent import RiskScoringAgent
from backend.agents.alert_agent import AlertAgent
from backend.agents.rag_agent import NewsRAGAgent

def step_1_collect_data():
    """Step 1: Data Collection (Skip - data already in DB)"""
    log.info("=" * 60)
    log.info("STEP 1: DATA COLLECTION")
    log.info("=" * 60)
    
    log.info("Skipping data collection - using existing database data")
    
    # Verify data exists in database
    with DatabaseService() as db:
        market_data = db.get_market_data(days=30)
        if market_data.empty:
            log.error("No market data found in database!")
            return False
        
        log.info(f"✓ Found {len(market_data)} market data records in database")
    
    return True

def step_2_compute_market_features():
    """Step 2: Compute market-based risk features"""
    log.info("=" * 60)
    log.info("STEP 2: MARKET FEATURE COMPUTATION")
    log.info("=" * 60)
    
    try:
        agent = MarketDataAgent()
        features = agent.process()
        
        if features is not None:
            log.info("✓ Market features computed")
            return True
        else:
            log.error("Market feature computation failed")
            return False
            
    except Exception as e:
        log.error(f"Error in market feature computation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def step_3_analyze_sentiment():
    """Step 3: Analyze news sentiment"""
    log.info("=" * 60)
    log.info("STEP 3: SENTIMENT ANALYSIS")
    log.info("=" * 60)
    
    try:
        agent = SentimentAgent()
        sentiment_data = agent.process()
        
        if sentiment_data is not None:
            log.info("✓ Sentiment analysis completed")
            return True
        else:
            log.error("Sentiment analysis failed")
            return False
            
    except Exception as e:
        log.error(f"Error in sentiment analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def step_4_build_rag_knowledge_base():
    """Step 4: Build RAG vector store"""
    log.info("=" * 60)
    log.info("STEP 4: RAG KNOWLEDGE BASE")
    log.info("=" * 60)
    
    try:
        agent = NewsRAGAgent()
        
        # Check if vector store already exists
        existing_store = agent.load_vector_store()
        if existing_store:
            log.info("✓ RAG vector store already exists and loaded")
            return True
        
        # Load news from database
        with DatabaseService() as db:
            from backend.database.models import NewsArticle, Stock
            
            log.info("Loading news articles from database...")
            news_query = db.db.query(NewsArticle).join(Stock).all()
            
            if not news_query:
                log.warning("No news articles found in database")
                return True  # Not a critical error
            
            # Convert to documents
            documents = []
            for article in news_query:
                doc_text = f"{article.headline}\n{article.description or ''}"
                metadata = {
                    'source': article.source or 'Unknown',
                    'symbol': article.stock.symbol if article.stock else 'GENERAL',
                    'date': article.published_date.isoformat() if article.published_date else '',
                    'sentiment': article.sentiment_label or 'neutral',
                    'url': article.url or ''
                }
                documents.append({'text': doc_text, 'metadata': metadata})
            
            log.info(f"Loaded {len(documents)} news articles")
        
        # Build vector store
        if documents:
            vector_store = agent.build_vector_store(documents)
            
            if vector_store:
                agent.save_vector_store(vector_store)
                log.info("✓ RAG knowledge base built and saved")
                return True
            else:
                log.error("Failed to build vector store")
                return False
        else:
            log.warning("No documents to build vector store")
            return True
            
    except Exception as e:
        log.error(f"Error in RAG knowledge base building: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def step_5_compute_risk_scores():
    """Step 5: Compute composite risk scores"""
    log.info("=" * 60)
    log.info("STEP 5: RISK SCORE COMPUTATION")
    log.info("=" * 60)
    
    try:
        agent = RiskScoringAgent()
        risk_scores = agent.process()
        
        if risk_scores is not None:
            log.info("✓ Risk scores computed and saved")
            return True
        else:
            log.error("Risk score computation failed")
            return False
            
    except Exception as e:
        log.error(f"Error in risk score computation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def step_6_generate_alerts():
    """Step 6: Generate and send alerts"""
    log.info("=" * 60)
    log.info("STEP 6: ALERT GENERATION")
    log.info("=" * 60)
    
    try:
        agent = AlertAgent()
        alerts = agent.process()
        
        if alerts is not None:
            log.info(f"✓ Generated {len(alerts)} alerts")
            return True
        else:
            log.error("Alert generation failed")
            return False
            
    except Exception as e:
        log.error(f"Error in alert generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main pipeline execution"""
    log.info("=" * 80)
    log.info("RISK INTELLIGENCE PLATFORM - MAIN PIPELINE")
    log.info("Now using PostgreSQL for data persistence")
    log.info("=" * 80)
    
    # Load configuration
    config = load_config()
    
    # Pipeline steps
    steps = [
        ("Data Collection", step_1_collect_data),
        ("Market Features", step_2_compute_market_features),
        ("Sentiment Analysis", step_3_analyze_sentiment),
        ("RAG Knowledge Base", step_4_build_rag_knowledge_base),
        ("Risk Scoring", step_5_compute_risk_scores),
        ("Alert Generation", step_6_generate_alerts),
    ]
    
    results = {}
    
    # Execute pipeline
    for step_name, step_func in steps:
        try:
            log.info(f"\n{'=' * 80}")
            log.info(f"Executing: {step_name}")
            log.info('=' * 80)
            success = step_func()
            results[step_name] = success
            
            if not success:
                log.error(f"Step '{step_name}' failed")
                # Continue on error for now
                continue
        except Exception as e:
            log.error(f"Unexpected error in {step_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            results[step_name] = False
    
    # Print summary
    log.info("\n" + "=" * 80)
    log.info("PIPELINE EXECUTION SUMMARY")
    log.info("=" * 80)
    
    for step_name, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        log.info(f"{step_name}: {status}")
    
    total_steps = len(results)
    successful_steps = sum(results.values())
    
    log.info("=" * 80)
    log.info(f"Completed: {successful_steps}/{total_steps} steps")
    
    if successful_steps == total_steps:
        log.info("✓ PIPELINE COMPLETED SUCCESSFULLY")
        log.info("=" * 80)
        return 0
    else:
        log.warning(f"✗ PIPELINE COMPLETED WITH {total_steps - successful_steps} ERROR(S)")
        log.info("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())