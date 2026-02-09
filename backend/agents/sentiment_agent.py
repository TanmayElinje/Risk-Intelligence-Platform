"""
Sentiment Agent - Analyzes news sentiment using FinBERT
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import re
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from backend.utils import log, load_config, load_dataframe, save_dataframe, ensure_dir

class SentimentAgent:
    """
    Agent responsible for computing sentiment scores from news
    """
    
    def __init__(self):
        """Initialize Sentiment Agent"""
        self.config = load_config()
        self.agent_config = self.config['agents']['sentiment']
        
        # Initialize FinBERT model
        log.info("Loading FinBERT model...")
        self.model_name = self.agent_config['model']
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            # Create sentiment analysis pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1,
                max_length=self.agent_config['max_length'],
                truncation=True
            )
            
            log.info(f"✓ FinBERT model loaded: {self.model_name}")
            log.info(f"Device: {'GPU' if torch.cuda.is_available() else 'CPU'}")
            
        except Exception as e:
            log.warning(f"Failed to load FinBERT: {str(e)}")
            log.warning("Falling back to rule-based sentiment (VADER)")
            self.use_finbert = False
            self._init_vader()
        else:
            self.use_finbert = True
    
    def _init_vader(self):
        """Initialize VADER as fallback"""
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        self.vader = SentimentIntensityAnalyzer()
        log.info("✓ VADER sentiment analyzer initialized (fallback)")
    
    def load_news_data(self) -> pd.DataFrame:
        """
        Load news data
        
        Returns:
            DataFrame with news articles
        """
        log.info("Loading news data...")
        
        news_path = f"{self.config['paths']['data_raw']}/news_data.parquet"
        
        try:
            news_df = load_dataframe(news_path, format='parquet')
            log.info(f"Loaded {len(news_df)} news articles")
            return news_df
        except FileNotFoundError:
            log.warning("No news data found, generating synthetic news for testing")
            return self._generate_synthetic_news()
    
    def _generate_synthetic_news(self) -> pd.DataFrame:
        """
        Generate synthetic news for testing when real news is unavailable
        
        Returns:
            DataFrame with synthetic news
        """
        log.info("Generating synthetic news data...")
        
        from datetime import datetime, timedelta
        
        # Get stock symbols
        stocks = self.config['stocks']['symbols'][:10]  # First 10 stocks
        
        # Positive, neutral, and negative news templates
        positive_news = [
            "{symbol} reports strong quarterly earnings, beating analyst expectations",
            "{symbol} announces strategic partnership with major tech company",
            "{symbol} stock surges on positive market sentiment and strong guidance",
            "{symbol} launches innovative new product, analysts bullish on growth",
            "{symbol} receives upgrade from major investment bank",
        ]
        
        neutral_news = [
            "{symbol} maintains steady performance in quarterly report",
            "{symbol} announces regular dividend payment to shareholders",
            "{symbol} updates investors on ongoing business operations",
            "{symbol} holds annual shareholder meeting, no major announcements",
            "Analysts maintain neutral rating on {symbol} stock",
        ]
        
        negative_news = [
            "{symbol} faces regulatory scrutiny, stock under pressure",
            "{symbol} misses earnings expectations, shares decline",
            "{symbol} announces layoffs amid cost-cutting measures",
            "{symbol} stock drops on weak guidance and market concerns",
            "{symbol} faces increased competition, market share concerns",
        ]
        
        news_items = []
        end_date = datetime.now()
        
        for i in range(100):
            # Random stock
            symbol = np.random.choice(stocks)
            
            # Random date in last 30 days
            date = end_date - timedelta(days=np.random.randint(0, 30))
            
            # Random sentiment category
            sentiment_type = np.random.choice(['positive', 'neutral', 'negative'], p=[0.3, 0.4, 0.3])
            
            if sentiment_type == 'positive':
                headline = np.random.choice(positive_news).format(symbol=symbol.replace('.BO', ''))
            elif sentiment_type == 'neutral':
                headline = np.random.choice(neutral_news).format(symbol=symbol.replace('.BO', ''))
            else:
                headline = np.random.choice(negative_news).format(symbol=symbol.replace('.BO', ''))
            
            news_items.append({
                'source': 'Synthetic',
                'headline': headline,
                'description': headline,
                'url': f'http://example.com/news/{i}',
                'published_date': date,
                'stock_symbol': symbol,
                'scraped_at': datetime.now()
            })
        
        news_df = pd.DataFrame(news_items)
        log.info(f"Generated {len(news_df)} synthetic news articles")
        
        return news_df
    
    def clean_text(self, text: str) -> str:
        """
        Clean and preprocess text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Truncate to max length
        max_chars = self.agent_config['max_length'] * 4  # Rough estimate
        text = text[:max_chars]
        
        return text.strip()
    
    def analyze_sentiment_finbert(self, texts: List[str]) -> List[Dict]:
        """
        Analyze sentiment using FinBERT
        
        Args:
            texts: List of text strings
            
        Returns:
            List of sentiment dictionaries
        """
        if not texts:
            return []
        
        batch_size = self.agent_config['batch_size']
        results = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                batch_results = self.sentiment_pipeline(batch)
                
                # Convert to our format
                for result in batch_results:
                    # FinBERT outputs: positive, negative, neutral
                    label = result['label'].lower()
                    score = result['score']
                    
                    # Convert to our scoring system
                    if label == 'positive':
                        sentiment_score = score
                    elif label == 'negative':
                        sentiment_score = -score
                    else:  # neutral
                        sentiment_score = 0.0
                    
                    results.append({
                        'label': label,
                        'score': score,
                        'sentiment_score': sentiment_score
                    })
                    
            except Exception as e:
                log.warning(f"Batch sentiment analysis failed: {str(e)}")
                # Fill with neutral sentiment
                for _ in batch:
                    results.append({
                        'label': 'neutral',
                        'score': 0.5,
                        'sentiment_score': 0.0
                    })
        
        return results
    
    def analyze_sentiment_vader(self, texts: List[str]) -> List[Dict]:
        """
        Analyze sentiment using VADER (fallback)
        
        Args:
            texts: List of text strings
            
        Returns:
            List of sentiment dictionaries
        """
        results = []
        
        for text in texts:
            try:
                scores = self.vader.polarity_scores(text)
                compound = scores['compound']
                
                # Classify
                if compound >= 0.05:
                    label = 'positive'
                    score = scores['pos']
                elif compound <= -0.05:
                    label = 'negative'
                    score = scores['neg']
                else:
                    label = 'neutral'
                    score = scores['neu']
                
                results.append({
                    'label': label,
                    'score': score,
                    'sentiment_score': compound
                })
                
            except Exception as e:
                log.warning(f"VADER sentiment failed: {str(e)}")
                results.append({
                    'label': 'neutral',
                    'score': 0.5,
                    'sentiment_score': 0.0
                })
        
        return results
    
    def compute_sentiment(self, news_df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute sentiment for all news articles
        
        Args:
            news_df: DataFrame with news articles
            
        Returns:
            DataFrame with sentiment scores
        """
        log.info("=" * 60)
        log.info("COMPUTING SENTIMENT SCORES")
        log.info("=" * 60)
        
        if news_df.empty:
            log.warning("No news data to analyze")
            return pd.DataFrame()
        
        # Clean text
        log.info("Cleaning text...")
        news_df['clean_text'] = news_df['headline'].fillna('') + ' ' + news_df['description'].fillna('')
        news_df['clean_text'] = news_df['clean_text'].apply(self.clean_text)
        
        # Remove empty texts
        news_df = news_df[news_df['clean_text'].str.len() > 0].copy()
        
        if news_df.empty:
            log.warning("No valid text after cleaning")
            return pd.DataFrame()
        
        log.info(f"Analyzing sentiment for {len(news_df)} articles...")
        
        # Analyze sentiment
        texts = news_df['clean_text'].tolist()
        
        if self.use_finbert:
            sentiment_results = self.analyze_sentiment_finbert(texts)
        else:
            sentiment_results = self.analyze_sentiment_vader(texts)
        
        # Add results to dataframe
        news_df['sentiment_label'] = [r['label'] for r in sentiment_results]
        news_df['sentiment_confidence'] = [r['score'] for r in sentiment_results]
        news_df['sentiment_score'] = [r['sentiment_score'] for r in sentiment_results]
        
        log.info("✓ Sentiment analysis complete")
        log.info(f"Positive: {(news_df['sentiment_label'] == 'positive').sum()}")
        log.info(f"Neutral: {(news_df['sentiment_label'] == 'neutral').sum()}")
        log.info(f"Negative: {(news_df['sentiment_label'] == 'negative').sum()}")
        
        return news_df
    
    def aggregate_daily_sentiment(self, news_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate sentiment scores per stock per day
        
        Args:
            news_df: DataFrame with sentiment scores
            
        Returns:
            DataFrame with daily aggregated sentiment
        """
        log.info("Aggregating daily sentiment per stock...")
        
        if news_df.empty:
            return pd.DataFrame()
        
        # Convert published_date to date only
        news_df['date'] = pd.to_datetime(news_df['published_date']).dt.date
        
        # Aggregate by stock and date
        daily_sentiment = news_df.groupby(['stock_symbol', 'date']).agg({
            'sentiment_score': ['mean', 'std', 'count'],
            'sentiment_label': lambda x: x.value_counts().to_dict()
        }).reset_index()
        
        # Flatten column names
        daily_sentiment.columns = ['stock_symbol', 'date', 'avg_sentiment', 'sentiment_std', 'article_count', 'sentiment_distribution']
        
        # Fill NaN std with 0
        daily_sentiment['sentiment_std'] = daily_sentiment['sentiment_std'].fillna(0)
        
        log.info(f"✓ Aggregated to {len(daily_sentiment)} stock-day combinations")
        
        return daily_sentiment
    
    def save_sentiment(self, sentiment_df: pd.DataFrame, filename: str = "sentiment_scores.csv"):
        """
        Save sentiment scores to file
        
        Args:
            sentiment_df: DataFrame with sentiment scores
            filename: Output filename
        """
        ensure_dir(self.config['paths']['data_processed'])
        filepath = f"{self.config['paths']['data_processed']}/{filename}"
        save_dataframe(sentiment_df, filepath, format='csv')
        log.info(f"✓ Saved sentiment scores to {filepath}")
    
    def run(self) -> pd.DataFrame:
        """
        Run the complete sentiment analysis pipeline
        
        Returns:
            DataFrame with sentiment scores
        """
        log.info("Starting Sentiment Agent...")
        
        # Load news
        news_df = self.load_news_data()
        
        if news_df.empty:
            log.warning("No news data available, skipping sentiment analysis")
            return pd.DataFrame()
        
        # Compute sentiment
        news_with_sentiment = self.compute_sentiment(news_df)
        
        # Aggregate daily
        daily_sentiment = self.aggregate_daily_sentiment(news_with_sentiment)
        
        # Save results
        if not daily_sentiment.empty:
            self.save_sentiment(daily_sentiment)
        
        # Also save detailed news with sentiment
        if not news_with_sentiment.empty:
            detailed_path = f"{self.config['paths']['data_processed']}/news_with_sentiment.csv"
            save_dataframe(news_with_sentiment, detailed_path, format='csv')
            log.info(f"✓ Saved detailed news sentiment to {detailed_path}")
        
        log.info("Sentiment Agent completed successfully")
        return daily_sentiment