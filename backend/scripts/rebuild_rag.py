"""
Rebuild RAG Vector Store from real news articles
backend/scripts/rebuild_rag.py

Usage: python -m backend.scripts.rebuild_rag
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.agents.rag_agent import NewsRAGAgent
from backend.database import DatabaseService
from backend.database.models import NewsArticle, Stock
from backend.utils import log
from langchain.schema import Document

def main():
    log.info("Rebuilding RAG vector store from real news articles...")

    agent = NewsRAGAgent()

    with DatabaseService() as db:
        news_query = db.db.query(NewsArticle).join(Stock).all()
        log.info(f"Found {len(news_query)} articles in database")

        if not news_query:
            log.error("No articles found! Run news fetcher first.")
            return

        documents = []
        for article in news_query:
            headline = article.headline or ""
            description = article.description or ""
            content = article.content or ""
            
            # Use full content if available, otherwise headline + description
            if content and len(content) > 100:
                doc_text = headline + "\n" + content
            else:
                doc_text = headline + "\n" + description

            metadata = {
                "source": article.source or "Unknown",
                "stock_symbol": article.stock.symbol if article.stock else "GENERAL",
                "date": str(article.published_date) if article.published_date else "",
                "sentiment": article.sentiment_label or "neutral",
                "url": article.url or "",
            }
            documents.append(Document(
                page_content=doc_text,
                metadata=metadata,
            ))

        log.info(f"Built {len(documents)} documents for vector store")

    # Build vector store
    vector_store = agent.build_vector_store(documents)

    if vector_store:
        agent.save_vector_store(vector_store)
        log.info("✓ RAG vector store rebuilt and saved successfully!")
    else:
        log.error("Failed to build vector store")


if __name__ == "__main__":
    main()