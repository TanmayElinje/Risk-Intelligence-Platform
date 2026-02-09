"""
Test RAG Agent
"""
from backend.utils import log
from backend.agents import NewsRAGAgent

def main():
    """Test RAG agent"""
    log.info("=" * 60)
    log.info("TESTING RAG AGENT")
    log.info("=" * 60)
    
    # Initialize agent
    agent = NewsRAGAgent()
    
    # Build vector store
    vector_store = agent.run()
    
    if vector_store is None:
        log.warning("Vector store not created")
        return
    
    # Test queries
    test_queries = [
        ("Why is AAPL risk high?", "AAPL"),
        ("What are the latest developments for MSFT?", "MSFT"),
        ("General market sentiment", None),
    ]
    
    log.info("\n" + "=" * 60)
    log.info("TESTING QUERY & RETRIEVAL")
    log.info("=" * 60)
    
    for query, symbol in test_queries:
        log.info(f"\nQuery: '{query}' (Stock: {symbol or 'All'})")
        log.info("-" * 60)
        
        result = agent.generate_explanation(query, symbol)
        
        log.info(f"Explanation:\n{result['explanation']}\n")
        log.info(f"Sources found: {result['num_sources']}")
        log.info(f"Confidence: {result['confidence']:.2f}")
        
        if result['sources']:
            log.info("\nTop sources:")
            for i, source in enumerate(result['sources'][:3], 1):
                log.info(f"{i}. {source['headline']} ({source['sentiment']})")
    
    log.info("\n" + "=" * 60)
    log.info("✓ RAG AGENT TEST COMPLETE")
    log.info("=" * 60)

if __name__ == "__main__":
    main()