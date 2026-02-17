"""
News Fetcher using Yahoo Finance Search API + Full Article Scraping
backend/scrapers/news_fetcher.py

Uses yf.Search(symbol, news_count=10) which is more reliable than ticker.news.
Scrapes full article content from each URL via requests + BeautifulSoup.
"""
import yfinance as yf
import requests
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
from backend.utils import log
from backend.database.models import SessionLocal, Stock, NewsArticle, SentimentScore


class NewsFetcher:
    """Fetch real news from Yahoo Finance Search API and scrape full content"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

    def _scrape_article_content(self, url, timeout=10):
        """
        Scrape full article text from a URL using requests + BeautifulSoup.
        """
        if not url or 'example.com' in url:
            return ''

        try:
            resp = self.session.get(url, timeout=timeout, allow_redirects=True)
            if resp.status_code != 200:
                return ''

            soup = BeautifulSoup(resp.content, 'lxml')

            # Remove unwanted elements
            for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'form']):
                tag.decompose()

            content = ''

            # Strategy 1: <article> tag
            article_tag = soup.find('article')
            if article_tag:
                paragraphs = article_tag.find_all('p')
                content = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

            # Strategy 2: Common article selectors
            if not content or len(content) < 100:
                for selector in [
                    'div.caas-body',           # Yahoo Finance
                    'div.article-body',
                    'div.story-body',
                    'div.article-content',
                    'div.entry-content',
                    'div.post-content',
                    'div[itemprop="articleBody"]',
                    'div.content-body',
                    'main',
                ]:
                    el = soup.select_one(selector)
                    if el:
                        paragraphs = el.find_all('p')
                        candidate = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        if len(candidate) > len(content):
                            content = candidate

            # Strategy 3: All <p> tags in body (fallback)
            if not content or len(content) < 100:
                body = soup.find('body')
                if body:
                    paragraphs = body.find_all('p')
                    content = ' '.join(
                        p.get_text(strip=True) for p in paragraphs
                        if len(p.get_text(strip=True)) > 40
                    )

            content = re.sub(r'\s+', ' ', content).strip()

            # Truncate very long articles
            if len(content) > 5000:
                content = content[:5000] + '...'

            return content

        except Exception as e:
            log.debug(f"Could not scrape {url}: {e}")
            return ''

    def fetch_news_for_symbol(self, symbol, news_count=8, scrape_content=True):
        """
        Fetch news for a stock using yf.Search() API.
        This is more reliable than ticker.news and less prone to rate limits.

        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            news_count: Number of articles to fetch
            scrape_content: Whether to scrape full article text

        Returns:
            List of article dicts
        """
        try:
            search = yf.Search(symbol, news_count=news_count)
            news = search.news

            if not news:
                return []

            articles = []
            for item in news:
                article = {
                    'symbol': symbol,
                    'headline': item.get('title', ''),
                    'description': item.get('summary', '') or item.get('description', '') or '',
                    'url': item.get('link', '') or item.get('url', '') or '',
                    'source': item.get('publisher', '') or item.get('source', 'Yahoo Finance'),
                    'published_date': None,
                    'content': '',
                    'thumbnail': '',
                }

                # Parse thumbnail
                thumb = item.get('thumbnail')
                if isinstance(thumb, dict):
                    resolutions = thumb.get('resolutions', [])
                    if resolutions:
                        article['thumbnail'] = resolutions[0].get('url', '')

                # Parse publish time
                pub_time = item.get('providerPublishTime') or item.get('publishedDate')
                if pub_time:
                    if isinstance(pub_time, (int, float)):
                        article['published_date'] = datetime.fromtimestamp(pub_time)
                    elif isinstance(pub_time, str):
                        try:
                            article['published_date'] = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                        except Exception:
                            article['published_date'] = datetime.utcnow()
                else:
                    article['published_date'] = datetime.utcnow()

                if article['headline']:
                    articles.append(article)

            # Scrape full content for each article
            if scrape_content and articles:
                for i, article in enumerate(articles):
                    if article['url']:
                        content = self._scrape_article_content(article['url'])
                        if content:
                            article['content'] = content
                        else:
                            article['content'] = article.get('description', '')
                    # Small delay between scrapes
                    if i < len(articles) - 1:
                        time.sleep(0.3)

            return articles

        except Exception as e:
            log.warning(f"Failed to fetch news for {symbol}: {e}")
            return []

    def fetch_all_news(self, symbols, scrape_content=True, delay=1.5, news_per_stock=8):
        """
        Fetch news for all stocks with rate limiting and full content scraping.

        Args:
            symbols: List of ticker symbols
            scrape_content: Whether to scrape full article content
            delay: Seconds between stock requests
            news_per_stock: Number of articles per stock

        Returns:
            List of all article dicts
        """
        all_articles = []
        stocks_with_news = 0

        log.info(f"Fetching news for {len(symbols)} stocks (scrape_content={scrape_content})...")

        for i, symbol in enumerate(symbols):
            articles = self.fetch_news_for_symbol(symbol, news_count=news_per_stock, scrape_content=scrape_content)
            if articles:
                all_articles.extend(articles)
                content_count = sum(1 for a in articles if a.get('content') and len(a['content']) > 100)
                log.info(f"  {symbol}: {len(articles)} articles ({content_count} with full content)")
                stocks_with_news += 1
            else:
                log.info(f"  {symbol}: no news")

            # Rate limiting between stocks
            if (i + 1) < len(symbols):
                time.sleep(delay)

            # Progress
            if (i + 1) % 10 == 0:
                log.info(f"  Progress: {i + 1}/{len(symbols)} stocks ({len(all_articles)} articles total)")

        log.info(f"✓ Fetched {len(all_articles)} articles for {stocks_with_news}/{len(symbols)} stocks")
        return all_articles

    def save_articles_to_db(self, articles):
        """
        Save fetched articles to the database, skipping duplicates by URL.
        """
        db = SessionLocal()
        saved = 0
        skipped = 0

        for article in articles:
            # Skip if URL already exists
            if article.get('url'):
                exists = db.query(NewsArticle).filter(
                    NewsArticle.url == article['url']
                ).first()
                if exists:
                    skipped += 1
                    continue

            # Get stock_id
            stock = db.query(Stock).filter(Stock.symbol == article['symbol']).first()
            stock_id = stock.id if stock else None

            news = NewsArticle(
                stock_id=stock_id,
                source=article.get('source', 'Yahoo Finance'),
                headline=article['headline'],
                description=article.get('description', ''),
                content=article.get('content', '') or article.get('description', ''),
                url=article.get('url', ''),
                published_date=article.get('published_date'),
                top_image=article.get('thumbnail', ''),
                sentiment_label=None,
                sentiment_score=None,
                sentiment_confidence=None,
            )
            db.add(news)
            saved += 1

        db.commit()
        db.close()

        log.info(f"✓ Saved {saved} new articles ({skipped} duplicates skipped)")
        return saved

    def clear_old_synthetic_news(self):
        """Remove old synthetic/dummy news articles from the database"""
        db = SessionLocal()

        deleted = db.query(NewsArticle).filter(
            (NewsArticle.source == 'Synthetic') |
            (NewsArticle.url.like('%example.com%'))
        ).delete(synchronize_session='fetch')

        if deleted > 0:
            db.query(SentimentScore).delete()
            log.info(f"✓ Cleared {deleted} synthetic articles and old sentiment scores")

        db.commit()
        db.close()
        return deleted

    def run_sentiment_analysis(self):
        """Run FinBERT sentiment analysis on articles without sentiment yet."""
        try:
            from backend.agents.sentiment_agent import SentimentAgent
            agent = SentimentAgent()
            result = agent.process()
            return result
        except Exception as e:
            log.error(f"Sentiment analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return None