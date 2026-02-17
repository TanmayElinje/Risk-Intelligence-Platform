"""
RAG Agent - Retrieval-Augmented Generation for explainable insights
"""
import os
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
import json
from pathlib import Path

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from backend.utils import log, load_config, load_dataframe, ensure_dir

class NewsRAGAgent:
    """
    Agent responsible for RAG-based news analysis and explanation generation
    """
    
    def __init__(self):
        """Initialize RAG Agent"""
        self.config = load_config()
        self.agent_config = self.config['agents']['rag']
        
        log.info("Initializing RAG Agent...")
        
        # Initialize embeddings model
        self._init_embeddings()
        
        # Initialize LLM
        self._init_llm()
        
        # Vector store will be initialized when data is loaded
        self.vector_store = None
        
        log.info("✓ RAG Agent initialized")
    
    def _init_embeddings(self):
        """Initialize embedding model"""
        log.info(f"Loading embedding model: {self.agent_config['embedding_model']}")
        
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.agent_config['embedding_model'],
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            log.info("✓ Embedding model loaded")
        except Exception as e:
            log.error(f"Failed to load embedding model: {str(e)}")
            raise
    
    def _init_llm(self):
        """Initialize LLM for generation. Tries Gemini first, falls back to Ollama."""
        llm_config = self.agent_config['llm']
        
        # Try Groq first (if API key is available)
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key:
            try:
                from backend.services.groq_client import GroqLLM
                self.llm = GroqLLM(model="llama-3.3-70b-versatile", temperature=0.3)
                # Test connection
                test = self.llm.invoke("Reply with just the word OK")
                if test and "Error" not in test:
                    log.info("✓ Groq LLM connected successfully")
                    return
                else:
                    log.warning(f"Groq test failed: {test}")
                    self.llm = None
            except Exception as e:
                log.warning(f"Groq not available: {e}")
                self.llm = None

        # Fall back to Ollama
        if llm_config['provider'] == 'ollama':
            log.info(f"Initializing Ollama LLM: {llm_config['model']}")
            
            try:
                self.llm = Ollama(
                    model=llm_config['model'],
                    temperature=0.3,
                    base_url="http://localhost:11434"
                )
                
                # Test connection
                test_response = self.llm.invoke("Hello")
                log.info("✓ Ollama LLM connected successfully")
                
            except Exception as e:
                log.warning(f"Ollama not available: {str(e)}")
                log.warning("RAG explanations will use template-based approach")
                self.llm = None
        else:
            log.warning("No LLM provider available, using template-based approach")
            self.llm = None
    
    def load_news_data(self) -> pd.DataFrame:
        """
        Load news data with sentiment
        
        Returns:
            DataFrame with news articles
        """
        log.info("Loading news data for RAG...")
        
        # Try to load news with sentiment first
        sentiment_path = f"{self.config['paths']['data_processed']}/news_with_sentiment.csv"
        
        try:
            news_df = load_dataframe(sentiment_path, format='csv')
            log.info(f"Loaded {len(news_df)} news articles with sentiment")
            return news_df
        except FileNotFoundError:
            log.warning("No news data found")
            return pd.DataFrame()
    
    def chunk_documents(self, news_df: pd.DataFrame) -> List[Document]:
        """
        Chunk news articles into smaller documents
        
        Args:
            news_df: DataFrame with news articles
            
        Returns:
            List of Document objects
        """
        log.info("Chunking documents...")
        
        if news_df.empty:
            log.warning("No documents to chunk")
            return []
        
        # Initialize text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.agent_config['chunk_size'],
            chunk_overlap=self.agent_config['chunk_overlap'],
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        documents = []
        
        for idx, row in news_df.iterrows():
            # Combine headline and description
            text = f"{row.get('headline', '')} {row.get('description', '')}"
            
            if not text.strip():
                continue
            
            # Split text into chunks
            chunks = text_splitter.split_text(text)
            
            for chunk in chunks:
                # Create metadata
                metadata = {
                    'source': row.get('source', 'Unknown'),
                    'stock_symbol': row.get('stock_symbol', 'GENERAL'),
                    'published_date': str(row.get('published_date', '')),
                    'url': row.get('url', ''),
                    'sentiment_label': row.get('sentiment_label', 'neutral'),
                    'sentiment_score': float(row.get('sentiment_score', 0.0)),
                    'headline': row.get('headline', '')
                }
                
                # Create document
                doc = Document(
                    page_content=chunk,
                    metadata=metadata
                )
                
                documents.append(doc)
        
        log.info(f"✓ Created {len(documents)} document chunks from {len(news_df)} articles")
        return documents
    
    def build_vector_store(self, documents: List[Document]) -> FAISS:
        """
        Build FAISS vector store from documents
        
        Args:
            documents: List of Document objects
            
        Returns:
            FAISS vector store
        """
        log.info("Building FAISS vector store...")
        
        if not documents:
            log.warning("No documents to index")
            return None
        
        try:
            # Create FAISS index
            vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
            
            log.info(f"✓ Vector store built with {len(documents)} documents")
            return vector_store
            
        except Exception as e:
            log.error(f"Failed to build vector store: {str(e)}")
            return None
    
    def save_vector_store(self, vector_store: FAISS):
        """
        Save vector store to disk
        
        Args:
            vector_store: FAISS vector store
        """
        if vector_store is None:
            log.warning("No vector store to save")
            return
        
        vector_db_path = self.config['paths']['vector_db']
        ensure_dir(vector_db_path)
        
        save_path = f"{vector_db_path}/faiss_index"
        
        try:
            vector_store.save_local(save_path)
            log.info(f"✓ Vector store saved to {save_path}")
        except Exception as e:
            log.error(f"Failed to save vector store: {str(e)}")
    
    def load_vector_store(self) -> Optional[FAISS]:
        """
        Load vector store from disk
        
        Returns:
            FAISS vector store or None
        """
        vector_db_path = self.config['paths']['vector_db']
        load_path = f"{vector_db_path}/faiss_index"
        
        if not Path(load_path).exists():
            log.warning("No saved vector store found")
            return None
        
        try:
            vector_store = FAISS.load_local(
                load_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            log.info(f"✓ Vector store loaded from {load_path}")
            return vector_store
        except Exception as e:
            log.error(f"Failed to load vector store: {str(e)}")
            return None
    
    def retrieve_documents(
        self,
        query: str,
        stock_symbol: Optional[str] = None,
        k: int = None
    ) -> List[Document]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query
            stock_symbol: Filter by stock symbol
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        if self.vector_store is None:
            log.warning("Vector store not initialized")
            return []
        
        if k is None:
            k = self.agent_config['top_k']
        
        try:
            # Create search kwargs
            search_kwargs = {'k': k * 2}  # Get more initially for filtering
            
            # Search
            docs = self.vector_store.similarity_search(query, **search_kwargs)
            
            # Filter by stock symbol if provided
            if stock_symbol:
                docs = [doc for doc in docs if doc.metadata.get('stock_symbol') == stock_symbol]
            
            # Limit to k results
            docs = docs[:k]
            
            log.info(f"Retrieved {len(docs)} documents for query: '{query}'")
            return docs
            
        except Exception as e:
            log.error(f"Document retrieval failed: {str(e)}")
            return []
    
    def generate_explanation(
        self,
        query: str,
        stock_symbol: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Generate explanation for a query using RAG
        
        Args:
            query: User query
            stock_symbol: Stock symbol to focus on
            
        Returns:
            Dictionary with explanation and sources
        """
        log.info(f"Generating explanation for: '{query}'")
        
        # Retrieve relevant documents
        docs = self.retrieve_documents(query, stock_symbol)
        
        if not docs:
            return {
                'query': query,
                'explanation': "No relevant information found in the news database.",
                'sources': [],
                'confidence': 0.0
            }
        
        # Generate explanation
        if self.llm is not None:
            explanation = self._generate_with_llm(query, docs, stock_symbol)
        else:
            explanation = self._generate_with_template(query, docs, stock_symbol)
        
        # Extract sources
        sources = self._extract_sources(docs)
        
        return {
            'query': query,
            'stock_symbol': stock_symbol,
            'explanation': explanation,
            'sources': sources,
            'num_sources': len(sources),
            'confidence': min(len(docs) / self.agent_config['top_k'], 1.0)
        }
    
    def _generate_with_llm(
        self,
        query: str,
        docs: List[Document],
        stock_symbol: Optional[str]
    ) -> str:
        """
        Generate explanation using LLM
        
        Args:
            query: User query
            docs: Retrieved documents
            stock_symbol: Stock symbol
            
        Returns:
            Generated explanation
        """
        # Create context from documents
        context = "\n\n".join([
            f"Source: {doc.metadata.get('source', 'Unknown')} ({doc.metadata.get('published_date', 'Unknown date')})\n"
            f"Sentiment: {doc.metadata.get('sentiment_label', 'neutral')}\n"
            f"Content: {doc.page_content}"
            for doc in docs
        ])
        
        # Create prompt
        prompt_template = """You are a financial risk analyst. Based on the following news articles, provide a clear and concise explanation.

Stock: {stock_symbol}
Question: {query}

News Articles:
{context}

Provide a professional analysis that:
1. Summarizes the key points from the news
2. Explains the risk factors or opportunities
3. Maintains objectivity and cites specific information
4. Keeps the response under 200 words

Analysis:"""
        
        prompt = prompt_template.format(
            stock_symbol=stock_symbol or "General Market",
            query=query,
            context=context
        )
        
        try:
            response = self.llm.invoke(prompt)
            return response.strip()
        except Exception as e:
            log.error(f"LLM generation failed: {str(e)}")
            return self._generate_with_template(query, docs, stock_symbol)
    
    def _generate_with_template(
        self,
        query: str,
        docs: List[Document],
        stock_symbol: Optional[str]
    ) -> str:
        """
        Generate explanation using template (fallback)
        
        Args:
            query: User query
            docs: Retrieved documents
            stock_symbol: Stock symbol
            
        Returns:
            Template-based explanation
        """
        # Count sentiment
        sentiments = [doc.metadata.get('sentiment_label', 'neutral') for doc in docs]
        positive = sentiments.count('positive')
        negative = sentiments.count('negative')
        neutral = sentiments.count('neutral')
        
        # Build explanation
        symbol_text = f"for {stock_symbol}" if stock_symbol else ""
        
        explanation = f"Based on {len(docs)} recent news articles {symbol_text}:\n\n"
        
        if negative > positive:
            explanation += f"⚠️ **Negative sentiment detected** ({negative} negative articles):\n"
        elif positive > negative:
            explanation += f"✓ **Positive sentiment detected** ({positive} positive articles):\n"
        else:
            explanation += f"📊 **Mixed sentiment** ({positive} positive, {negative} negative, {neutral} neutral):\n"
        
        # Add key headlines
        explanation += "\nKey headlines:\n"
        for i, doc in enumerate(docs[:3], 1):
            headline = doc.metadata.get('headline', doc.page_content[:100])
            sentiment = doc.metadata.get('sentiment_label', 'neutral')
            explanation += f"{i}. [{sentiment.upper()}] {headline}\n"
        
        return explanation
    
    def _extract_sources(self, docs: List[Document]) -> List[Dict]:
        """
        Extract source information from documents
        
        Args:
            docs: List of documents
            
        Returns:
            List of source dictionaries
        """
        sources = []
        seen_urls = set()
        
        for doc in docs:
            url = doc.metadata.get('url', '')
            
            # Skip duplicates
            if url in seen_urls:
                continue
            
            seen_urls.add(url)
            
            sources.append({
                'headline': doc.metadata.get('headline', ''),
                'source': doc.metadata.get('source', 'Unknown'),
                'url': url,
                'published_date': doc.metadata.get('published_date', ''),
                'sentiment': doc.metadata.get('sentiment_label', 'neutral'),
                'sentiment_score': doc.metadata.get('sentiment_score', 0.0)
            })
        
        return sources
    
    def run(self) -> Optional[FAISS]:
        """
        Run the complete RAG agent pipeline
        
        Returns:
            FAISS vector store
        """
        log.info("=" * 60)
        log.info("STARTING RAG AGENT")
        log.info("=" * 60)
        
        # Load news data
        news_df = self.load_news_data()
        
        if news_df.empty:
            log.warning("No news data available for RAG")
            return None
        
        # Chunk documents
        documents = self.chunk_documents(news_df)
        
        if not documents:
            log.warning("No documents created")
            return None
        
        # Build vector store
        self.vector_store = self.build_vector_store(documents)
        
        # Save vector store
        if self.vector_store:
            self.save_vector_store(self.vector_store)
        
        log.info("=" * 60)
        log.info("✓ RAG AGENT COMPLETED")
        log.info("=" * 60)
        
        return self.vector_store