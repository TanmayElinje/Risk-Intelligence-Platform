"""
Sentiment Agent - Analyze news sentiment using FinBERT
Now analyzes full article content instead of just headlines
"""
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import pandas as pd
from datetime import datetime, timedelta
from backend.utils import log
from backend.database import DatabaseService
from backend.database.models import NewsArticle, SentimentScore

class SentimentAgent:
    """
    Analyze news sentiment with FinBERT using full article content
    """
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.load_model()
    
    def load_model(self):
        """Load pre-trained FinBERT model"""
        try:
            log.info(f"Loading FinBERT model on {self.device}...")
            
            model_name = "ProsusAI/finbert"
            self.tokenizer = BertTokenizer.from_pretrained(model_name)
            self.model = BertForSequenceClassification.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            
            log.info("✓ FinBERT model loaded successfully")
            
        except Exception as e:
            log.error(f"Error loading FinBERT model: {str(e)}")
            raise
    
    def analyze_text(self, text: str, max_length: int = 512) -> dict:
        """
        Analyze sentiment of text using FinBERT
        
        Args:
            text: Text to analyze (headline or full content)
            max_length: Max tokens (FinBERT limit is 512)
        
        Returns:
            dict with label, score, confidence
        """
        if not text or len(text.strip()) < 10:
            return {
                'label': 'neutral',
                'score': 0.0,
                'confidence': 0.0
            }
        
        try:
            # Truncate if too long (take first max_length tokens worth of text)
            # Roughly 4 chars per token
            if len(text) > max_length * 4:
                text = text[:max_length * 4]
            
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=max_length,
                padding=True
            ).to(self.device)
            
            # Get prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Get label and confidence
            confidence, predicted_class = torch.max(predictions, dim=1)
            
            labels = ['positive', 'negative', 'neutral']
            sentiment_label = labels[predicted_class.item()]
            
            # Convert to score (-1 to 1)
            if sentiment_label == 'positive':
                sentiment_score = predictions[0][0].item()
            elif sentiment_label == 'negative':
                sentiment_score = -predictions[0][1].item()
            else:
                sentiment_score = 0.0
            
            return {
                'label': sentiment_label,
                'score': sentiment_score,
                'confidence': confidence.item()
            }
            
        except Exception as e:
            log.error(f"Error analyzing sentiment: {str(e)}")
            return {
                'label': 'neutral',
                'score': 0.0,
                'confidence': 0.0
            }
    
    def analyze_article_enhanced(self, article: NewsArticle) -> dict:
        """
        Enhanced sentiment analysis using BOTH headline and full content
        
        Weights:
        - Headline: 40% (more impactful, what people read first)
        - Content: 60% (more comprehensive, full context)
        """
        try:
            # Analyze headline
            headline_sentiment = self.analyze_text(article.headline)
            
            # Analyze full content (if available)
            if article.content and len(article.content) > 100:
                content_sentiment = self.analyze_text(article.content, max_length=512)
                
                # Weighted average
                final_score = (
                    headline_sentiment['score'] * 0.4 +
                    content_sentiment['score'] * 0.6
                )
                final_confidence = (
                    headline_sentiment['confidence'] * 0.4 +
                    content_sentiment['confidence'] * 0.6
                )
                
                # Determine final label
                if final_score > 0.1:
                    final_label = 'positive'
                elif final_score < -0.1:
                    final_label = 'negative'
                else:
                    final_label = 'neutral'
                
                log.info(f"  Headline: {headline_sentiment['label']} ({headline_sentiment['score']:.3f})")
                log.info(f"  Content: {content_sentiment['label']} ({content_sentiment['score']:.3f})")
                log.info(f"  Final: {final_label} ({final_score:.3f})")
                
            else:
                # No content, use headline only
                final_label = headline_sentiment['label']
                final_score = headline_sentiment['score']
                final_confidence = headline_sentiment['confidence']
                
                log.info(f"  Headline only: {final_label} ({final_score:.3f})")
            
            return {
                'label': final_label,
                'score': final_score,
                'confidence': final_confidence
            }
            
        except Exception as e:
            log.error(f"Error in enhanced analysis: {str(e)}")
            return headline_sentiment if 'headline_sentiment' in locals() else {
                'label': 'neutral',
                'score': 0.0,
                'confidence': 0.0
            }
    
    def process(self):
        """
        Process new articles that don't have sentiment yet
        """
        log.info("=" * 60)
        log.info("SENTIMENT AGENT - Analyzing News Sentiment")
        log.info("Using enhanced analysis: Headline (40%) + Content (60%)")
        log.info("=" * 60)
        
        try:
            with DatabaseService() as db:
                # Get articles without sentiment
                new_articles = db.db.query(NewsArticle).filter(
                    NewsArticle.sentiment_label == None
                ).all()
                
                if not new_articles:
                    log.info("No new articles to analyze")
                    
                    # Get recent sentiment for return
                    sentiment_data = db.get_recent_sentiment(days=30)
                    log.info(f"✓ Found {len(sentiment_data)} daily sentiment records")
                    return sentiment_data
                
                log.info(f"Found {len(new_articles)} articles without sentiment")
                log.info(f"Analyzing {len(new_articles)} new articles...")
                
                analyzed_count = 0
                
                for article in new_articles:
                    try:
                        log.info(f"\nAnalyzing: {article.headline[:60]}...")
                        
                        # Enhanced analysis
                        result = self.analyze_article_enhanced(article)
                        
                        # Update article
                        article.sentiment_label = result['label']
                        article.sentiment_score = result['score']
                        article.sentiment_confidence = result['confidence']
                        
                        analyzed_count += 1
                        
                    except Exception as e:
                        log.error(f"Error analyzing article {article.id}: {str(e)}")
                        continue
                
                # Commit all updates
                db.db.commit()
                log.info(f"\n✓ Analyzed {analyzed_count} articles")
                
                # Aggregate daily sentiment
                self._aggregate_daily_sentiment(db)
                
                # Return recent sentiment data
                sentiment_data = db.get_recent_sentiment(days=30)
                
                log.info("=" * 60)
                log.info(f"✓ SENTIMENT AGENT COMPLETED - {len(sentiment_data)} daily records")
                log.info("=" * 60)
                
                return sentiment_data
                
        except Exception as e:
            log.error(f"Error in sentiment processing: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _aggregate_daily_sentiment(self, db):
        """Aggregate sentiment scores by stock and date"""
        log.info("\nAggregating daily sentiment scores...")
        
        try:
            # Get all articles with sentiment
            articles = db.db.query(NewsArticle).filter(
                NewsArticle.sentiment_label != None
            ).all()
            
            # Group by stock and date
            sentiment_by_stock_date = {}
            
            for article in articles:
                if not article.stock_id:
                    continue
                
                date = article.published_date.date() if article.published_date else datetime.now().date()
                key = (article.stock_id, date)
                
                if key not in sentiment_by_stock_date:
                    sentiment_by_stock_date[key] = []
                
                sentiment_by_stock_date[key].append(article.sentiment_score)
            
            # Calculate averages and save
            saved_count = 0
            
            for (stock_id, date), scores in sentiment_by_stock_date.items():
                avg_sentiment = sum(scores) / len(scores)
                
                # Check if exists
                existing = db.db.query(SentimentScore).filter(
                    SentimentScore.stock_id == stock_id,
                    SentimentScore.date == date
                ).first()
                
                if existing:
                    existing.avg_sentiment = avg_sentiment
                    existing.article_count = len(scores)
                else:
                    sentiment_score = SentimentScore(
                        stock_id=stock_id,
                        date=date,
                        avg_sentiment=avg_sentiment,
                        article_count=len(scores)
                    )
                    db.db.add(sentiment_score)
                    saved_count += 1
            
            db.db.commit()
            log.info(f"✓ Aggregated sentiment for {len(sentiment_by_stock_date)} stock-date combinations")
            
        except Exception as e:
            log.error(f"Error aggregating sentiment: {str(e)}")

def main():
    """Test sentiment agent"""
    try:
        agent = SentimentAgent()
        sentiment_data = agent.process()
        
        if sentiment_data is not None and not sentiment_data.empty:
            print(f"\nSentiment data shape: {sentiment_data.shape}")
            print(f"\nRecent sentiment:")
            print(sentiment_data.head(10))
            log.info("=" * 60)
            log.info("✓ SENTIMENT AGENT COMPLETED SUCCESSFULLY")
            log.info("=" * 60)
        else:
            log.error("Sentiment agent failed")
    except Exception as e:
        log.error(f"Sentiment agent failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()