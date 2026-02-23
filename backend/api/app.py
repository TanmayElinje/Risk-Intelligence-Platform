"""
Flask API Application with WebSocket support
Includes:
  - Startup pipeline (refresh data on launch)
  - Daily scheduled refresh (configurable time)
"""
from flask import Flask, request, jsonify
from backend.utils import log, load_config
from backend.websocket.socket_manager import socket_manager
from dotenv import load_dotenv
import os

# Load .env file early
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

# ============================================================
# Daily refresh schedule time (24hr format, local time)
# Change this to set when the daily refresh runs
DAILY_REFRESH_HOUR = 8    # 8:00 AM
DAILY_REFRESH_MINUTE = 0  # :00
# ============================================================


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    config = load_config()
    
    # Manual CORS handler for OPTIONS requests
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({"status": "ok"})
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
            return response, 200
    
    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        return response
    
    # Initialize WebSocket
    socket_manager.init_app(app)
    
    # Register Blueprint routes
    from backend.api.routes import api_bp
    from backend.api.auth_routes import auth_bp
    from backend.api.watchlist_routes import watchlist_bp
    from backend.api.portfolio_routes import portfolio_bp
    from backend.api.email_routes import email_bp
    from backend.api.advanced_analytics_routes import advanced_bp
    from backend.api.backtest_routes import backtest_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp)
    app.register_blueprint(watchlist_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(advanced_bp)
    app.register_blueprint(backtest_bp)
    
    log.info("Flask app created successfully")
    log.info("CORS enabled (manual handlers)")
    log.info("WebSocket enabled")
    log.info("API routes registered")
    
    return app


def run_data_pipeline():
    """
    Full data refresh pipeline:
    1. Fetch market data from Yahoo Finance
    2. Fetch news + run FinBERT sentiment
    3. Rebuild RAG vector store
    4. Run ML risk scoring (SHAP-based)
    5. Generate alerts
    """
    try:
        log.info("=" * 60)
        log.info("DATA PIPELINE — Refreshing all data...")
        log.info("=" * 60)
        
        from backend.scripts.refresh_real_data import (
            refresh_market_data, refresh_news_and_sentiment
        )
        from backend.scrapers.yfinance_collector import YFinanceCollector
        
        config = load_config()
        symbols = config['stocks']['symbols']
        collector = YFinanceCollector()
        
        # Step 1: Market data
        log.info("[1/4] Fetching latest market data...")
        refresh_market_data(symbols, collector, period='1y')
        
        # Step 2: News + sentiment
        log.info("[2/4] Fetching latest news + sentiment...")
        try:
            refresh_news_and_sentiment(symbols)
        except Exception as e:
            log.warning(f"News refresh failed (non-fatal): {e}")
        
        # Step 3: Rebuild RAG
        log.info("[3/4] Rebuilding RAG vector store...")
        try:
            from backend.scripts.rebuild_rag import main as rebuild_rag
            rebuild_rag()
        except Exception as e:
            log.warning(f"RAG rebuild failed (non-fatal): {e}")
        
        # Step 4: ML risk scores + alerts
        log.info("[4/4] Running ML risk scoring + alerts...")
        from backend.main import main as run_pipeline
        run_pipeline()
        
        log.info("=" * 60)
        log.info("✓ DATA PIPELINE COMPLETE")
        log.info("=" * 60)
        
    except Exception as e:
        log.error(f"Data pipeline error: {e}")
        import traceback
        traceback.print_exc()


def run_startup_pipeline():
    """Run data pipeline on startup in a background thread."""
    import threading
    
    thread = threading.Thread(target=run_data_pipeline, daemon=True)
    thread.start()
    log.info("Startup pipeline running in background...")


def start_daily_scheduler():
    """
    Schedule the data pipeline to run daily at the configured time.
    Uses APScheduler if available, falls back to a simple threading timer.
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            run_data_pipeline,
            trigger=CronTrigger(
                hour=DAILY_REFRESH_HOUR,
                minute=DAILY_REFRESH_MINUTE,
            ),
            id='daily_data_refresh',
            name='Daily data refresh pipeline',
            replace_existing=True,
        )
        scheduler.start()
        log.info(f"Daily scheduler started — pipeline runs at {DAILY_REFRESH_HOUR:02d}:{DAILY_REFRESH_MINUTE:02d} every day")
        
    except ImportError:
        log.warning("APScheduler not installed — using simple timer fallback")
        log.warning("Install with: pip install apscheduler")
        _start_simple_scheduler()


def _start_simple_scheduler():
    """Fallback: simple threading-based daily scheduler."""
    import threading
    from datetime import datetime, timedelta
    
    def _schedule_loop():
        while True:
            now = datetime.now()
            target = now.replace(
                hour=DAILY_REFRESH_HOUR,
                minute=DAILY_REFRESH_MINUTE,
                second=0,
                microsecond=0,
            )
            # If target time already passed today, schedule for tomorrow
            if target <= now:
                target += timedelta(days=1)
            
            wait_seconds = (target - now).total_seconds()
            log.info(f"Next scheduled refresh: {target.strftime('%Y-%m-%d %H:%M')} ({wait_seconds/3600:.1f}h from now)")
            
            import time
            time.sleep(wait_seconds)
            
            log.info("Scheduled daily refresh triggered!")
            run_data_pipeline()
    
    thread = threading.Thread(target=_schedule_loop, daemon=True)
    thread.start()
    log.info(f"Simple daily scheduler started — pipeline runs at {DAILY_REFRESH_HOUR:02d}:{DAILY_REFRESH_MINUTE:02d} every day")


def run_server(host='0.0.0.0', port=5000, debug=True):
    """Run the Flask server with WebSocket support"""
    app = create_app()
    
    # Auto-refresh data on startup
    run_startup_pipeline()
    
    # Schedule daily refresh
    start_daily_scheduler()
    
    log.info("=" * 60)
    log.info("STARTING FLASK API SERVER WITH WEBSOCKET")
    log.info(f"Daily refresh scheduled at {DAILY_REFRESH_HOUR:02d}:{DAILY_REFRESH_MINUTE:02d}")
    log.info("=" * 60)
    log.info(f"Host: {host}")
    log.info(f"Port: {port}")
    log.info(f"Debug: {debug}")
    log.info("=" * 60)
    
    # Use SocketIO run instead of app.run
    socket_manager.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server()