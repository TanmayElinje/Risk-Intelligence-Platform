"""
Refresh Real Data Script
backend/scripts/refresh_real_data.py

Replaces dummy data with real stock data from Yahoo Finance.
Uses yf.download() for bulk fetching (fast, single request).

Usage:
    python -m backend.scripts.refresh_real_data
    python -m backend.scripts.refresh_real_data --period 6mo
    python -m backend.scripts.refresh_real_data --symbols AAPL,MSFT,GOOGL
    python -m backend.scripts.refresh_real_data --with-metadata
"""
import sys
import os
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.scrapers.yfinance_collector import YFinanceCollector
from backend.database import DatabaseService
from backend.database.models import SessionLocal, Stock, MarketData
from backend.utils import log, load_config
import pandas as pd


def refresh_stock_metadata(symbols, collector):
    """Step 1 (optional): Update stock names from Yahoo Finance fast_info"""
    log.info("=" * 60)
    log.info("STEP 1: REFRESHING STOCK METADATA (fast_info)")
    log.info("=" * 60)

    db = SessionLocal()
    updated = 0

    infos = collector.get_multiple_stock_info(symbols)

    for info in infos:
        symbol = info['symbol']
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if stock:
            if info.get('name') and info['name'] != symbol:
                stock.name = info['name']
            if info.get('sector') and info['sector'] != 'Unknown':
                stock.sector = info['sector']
            if info.get('industry') and info['industry'] != 'Unknown':
                stock.industry = info['industry']
            updated += 1
        else:
            new_stock = Stock(
                symbol=symbol,
                name=info.get('name', symbol),
                sector=info.get('sector', 'Unknown'),
                industry=info.get('industry', 'Unknown'),
                is_active=True,
            )
            db.add(new_stock)
            updated += 1

    db.commit()
    db.close()
    log.info(f"✓ Updated metadata for {updated} stocks")


def refresh_market_data(symbols, collector, period="1y"):
    """Step 2: Fetch real OHLCV data via yf.download() and replace in database"""
    log.info("=" * 60)
    log.info("STEP 2: FETCHING REAL MARKET DATA (yf.download)")
    log.info("=" * 60)

    data = collector.get_multiple_stocks(symbols, period=period)
    if data.empty:
        log.error("No market data fetched! Check your internet connection.")
        return False

    db = SessionLocal()
    inserted = 0
    deleted_total = 0

    for symbol in data['symbol'].unique():
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            # Auto-create stock entry
            stock = Stock(symbol=symbol, name=symbol, sector='Unknown', industry='Unknown', is_active=True)
            db.add(stock)
            db.commit()
            db.refresh(stock)

        # Delete old dummy data
        deleted = db.query(MarketData).filter(MarketData.stock_id == stock.id).delete()
        deleted_total += deleted

        symbol_data = data[data['symbol'] == symbol]
        for _, row in symbol_data.iterrows():
            md = MarketData(
                stock_id=stock.id,
                date=row['Date'].date() if hasattr(row['Date'], 'date') else row['Date'],
                open=float(row['Open']) if pd.notna(row.get('Open')) else None,
                high=float(row['High']) if pd.notna(row.get('High')) else None,
                low=float(row['Low']) if pd.notna(row.get('Low')) else None,
                close=float(row['Close']) if pd.notna(row.get('Close')) else None,
                volume=int(row['Volume']) if pd.notna(row.get('Volume')) else None,
            )
            db.add(md)
            inserted += 1

        db.commit()

    db.close()
    log.info(f"✓ Deleted {deleted_total} old records, inserted {inserted} new records")
    return True


def recompute_risk_scores():
    """Step 3: Recompute risk scores using real market data"""
    log.info("=" * 60)
    log.info("STEP 3: RECOMPUTING RISK SCORES")
    log.info("=" * 60)

    try:
        from backend.agents.market_agent import MarketDataAgent
        from backend.agents.risk_agent import RiskScoringAgent

        log.info("Computing market features...")
        features = MarketDataAgent().process()
        if features is None:
            log.error("Market feature computation failed")
            return False
        log.info(f"✓ Computed features for {len(features)} stocks")

        log.info("Computing risk scores...")
        risk_scores = RiskScoringAgent().process()
        if risk_scores is None:
            log.error("Risk score computation failed")
            return False
        log.info(f"✓ Computed risk scores for {len(risk_scores)} stocks")

        with DatabaseService() as db:
            db.save_risk_scores(risk_scores, upsert=True)
            log.info("✓ Risk scores saved to database")

            try:
                db.save_risk_history(risk_scores[['symbol', 'risk_score', 'risk_level']])
                log.info("✓ Risk history updated")
            except Exception as e:
                log.warning(f"Could not save risk history: {e}")

        return True

    except Exception as e:
        log.error(f"Error computing risk scores: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def refresh_news_and_sentiment(symbols):
    """Step 3b: Fetch real news from Yahoo Finance and run sentiment analysis"""
    log.info("=" * 60)
    log.info("STEP 3b: FETCHING REAL NEWS & SENTIMENT")
    log.info("=" * 60)

    try:
        from backend.scrapers.news_fetcher import NewsFetcher
        fetcher = NewsFetcher()

        # Clear old synthetic/dummy news
        deleted = fetcher.clear_old_synthetic_news()
        if deleted:
            log.info(f"Cleared {deleted} old synthetic articles")

        # Fetch real news from Yahoo Finance
        articles = fetcher.fetch_all_news(symbols, delay=1.0)

        if not articles:
            log.warning("No news articles fetched")
            return False

        # Save to database
        saved = fetcher.save_articles_to_db(articles)
        log.info(f"Saved {saved} new articles to database")

        # Run FinBERT sentiment analysis on new articles
        log.info("Running FinBERT sentiment analysis...")
        fetcher.run_sentiment_analysis()

        return True

    except Exception as e:
        log.error(f"News refresh failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def generate_alerts():
    """Step 4: Generate alerts based on new risk scores"""
    log.info("=" * 60)
    log.info("STEP 4: GENERATING ALERTS")
    log.info("=" * 60)

    try:
        from backend.agents.alert_agent import AlertAgent
        alerts = AlertAgent().process()
        if alerts is not None:
            log.info(f"✓ Generated {len(alerts)} alerts")
        return True
    except Exception as e:
        log.error(f"Error generating alerts: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Refresh stock data with real Yahoo Finance data')
    parser.add_argument('--period', type=str, default='1y',
                        help='Data period: 1mo, 3mo, 6mo, 1y, 2y (default: 1y)')
    parser.add_argument('--symbols', type=str, default='',
                        help='Comma-separated symbols (default: all from config)')
    parser.add_argument('--with-metadata', action='store_true',
                        help='Also refresh stock names/sectors (slower, may hit rate limits)')
    parser.add_argument('--skip-risk', action='store_true',
                        help='Skip risk score recomputation')
    parser.add_argument('--skip-news', action='store_true',
                        help='Skip news fetching and sentiment analysis')
    parser.add_argument('--skip-alerts', action='store_true',
                        help='Skip alert generation')

    args = parser.parse_args()

    log.info("=" * 60)
    log.info("REAL DATA REFRESH PIPELINE")
    log.info(f"Period: {args.period}")
    log.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)

    config = load_config()
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(',')]
    else:
        symbols = config['stocks']['symbols']

    log.info(f"Processing {len(symbols)} stocks: {', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''}")

    collector = YFinanceCollector()

    # Step 1: Metadata (optional — skipped by default to avoid rate limits)
    if args.with_metadata:
        try:
            refresh_stock_metadata(symbols, collector)
        except Exception as e:
            log.warning(f"Metadata refresh failed (non-fatal): {e}")
    else:
        log.info("Skipping metadata refresh (use --with-metadata to enable)")

    # Step 2: Market data (bulk download — fast)
    success = refresh_market_data(symbols, collector, period=args.period)
    if not success:
        log.error("Market data refresh failed! Aborting.")
        sys.exit(1)

    # Step 3: Risk scores
    if not args.skip_risk:
        recompute_risk_scores()
    else:
        log.info("Skipping risk score recomputation")

    # Step 3b: News + Sentiment
    if not args.skip_news:
        refresh_news_and_sentiment(symbols)
    else:
        log.info("Skipping news refresh")

    # Step 4: Alerts
    if not args.skip_alerts:
        generate_alerts()
    else:
        log.info("Skipping alert generation")

    log.info("=" * 60)
    log.info("✓ DATA REFRESH COMPLETE")
    log.info("=" * 60)

    # Print summary
    with DatabaseService() as db:
        risk_scores = db.get_latest_risk_scores()
        if not risk_scores.empty:
            high = len(risk_scores[risk_scores['risk_level'] == 'High'])
            medium = len(risk_scores[risk_scores['risk_level'] == 'Medium'])
            low = len(risk_scores[risk_scores['risk_level'] == 'Low'])
            print(f"\n{'='*40}")
            print(f"  SUMMARY")
            print(f"{'='*40}")
            print(f"  Stocks:      {len(risk_scores)}")
            print(f"  High Risk:   {high}")
            print(f"  Medium Risk: {medium}")
            print(f"  Low Risk:    {low}")
            print(f"  Avg Score:   {risk_scores['risk_score'].mean():.4f}")
            print(f"{'='*40}")


if __name__ == '__main__':
    main()