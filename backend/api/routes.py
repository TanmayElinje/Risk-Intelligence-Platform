"""
API Routes - Now using PostgreSQL
"""
from flask import Blueprint, jsonify, request
from backend.utils import log
from backend.database import DatabaseService
from backend.agents.rag_agent import NewsRAGAgent
from datetime import datetime, timedelta, date
import pandas as pd

api_bp = Blueprint('api', __name__)

# Global RAG agent (lazy loaded)
_rag_agent = None

def get_rag_agent():
    """Get or initialize RAG agent"""
    global _rag_agent
    
    if _rag_agent is None:
        try:
            log.info("Initializing RAG agent for API...")
            _rag_agent = NewsRAGAgent()
            _rag_agent.vector_store = _rag_agent.load_vector_store()
            
            if _rag_agent.vector_store:
                log.info(f"RAG agent initialized successfully")
            else:
                log.warning("RAG agent initialized but no vector store found")
                
        except Exception as e:
            log.error(f"Failed to initialize RAG agent: {str(e)}")
            _rag_agent = None
    
    return _rag_agent

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected'
    })

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    try:
        with DatabaseService() as db:
            risk_scores = db.get_latest_risk_scores()
            alerts = db.get_recent_alerts(limit=1000)
            
            if risk_scores.empty:
                return jsonify({'error': 'No data available'}), 404
            
            stats = {
                'total_stocks': len(risk_scores),
                'high_risk_stocks': len(risk_scores[risk_scores['risk_level'] == 'High']),
                'medium_risk_stocks': len(risk_scores[risk_scores['risk_level'] == 'Medium']),
                'low_risk_stocks': len(risk_scores[risk_scores['risk_level'] == 'Low']),
                'avg_risk_score': float(risk_scores['risk_score'].mean()),
                'avg_sentiment': float(risk_scores['avg_sentiment'].mean()) if 'avg_sentiment' in risk_scores.columns else 0,
                'total_alerts': len(alerts),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return jsonify(stats)
            
    except Exception as e:
        log.error(f"Error in get_stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/risk-scores', methods=['GET'])
def get_risk_scores():
    """Get all risk scores with optional filtering"""
    try:
        risk_level = request.args.get('risk_level')
        limit = request.args.get('limit', type=int)
        
        with DatabaseService() as db:
            risk_scores = db.get_latest_risk_scores()
            
            if risk_scores.empty:
                return jsonify({'error': 'No data available'}), 404
            
            # Filter by risk level
            if risk_level:
                risk_scores = risk_scores[risk_scores['risk_level'] == risk_level]
            
            # Limit results
            if limit:
                risk_scores = risk_scores.head(limit)
            
            # Convert to dict
            data = risk_scores.to_dict('records')
            
            # Convert numpy types to Python types
            for record in data:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                    elif isinstance(value, (pd.Timestamp, datetime)):
                        record[key] = value.isoformat()
            
            return jsonify({
                'count': len(data),
                'data': data
            })
            
    except Exception as e:
        log.error(f"Error in get_risk_scores: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stock/<symbol>', methods=['GET'])
def get_stock_details(symbol):
    """Get detailed information for a specific stock"""
    try:
        with DatabaseService() as db:
            # Get latest risk score
            risk_scores = db.get_latest_risk_scores()
            stock_risk = risk_scores[risk_scores['symbol'] == symbol]
            
            # FIX: Use .empty instead of boolean check
            if stock_risk.empty:
                return jsonify({'error': f'Stock {symbol} not found'}), 404
            
            stock_data = stock_risk.iloc[0].to_dict()
            
            # Convert all numpy/pandas types to Python types
            for key, value in stock_data.items():
                if pd.isna(value):
                    stock_data[key] = None
                elif isinstance(value, (pd.Timestamp, datetime)):
                    stock_data[key] = value.isoformat()
                elif hasattr(value, 'item'):  # numpy types
                    stock_data[key] = value.item()
            
            # Get market data (latest)
            market_data = db.get_market_data(symbol=symbol, days=365)
            if not market_data.empty:  # FIX: Added .empty
                latest_market = market_data.iloc[-1]
                stock_data['Close'] = float(latest_market['Close']) if pd.notna(latest_market['Close']) else None
                stock_data['Volume'] = int(latest_market['Volume']) if pd.notna(latest_market['Volume']) else None
            else:
                stock_data['Close'] = None
                stock_data['Volume'] = None
            
            # Get sentiment history
            sentiment_history = db.get_recent_sentiment(days=30)
            if not sentiment_history.empty:  # FIX: Added .empty
                sentiment_history = sentiment_history[sentiment_history['stock_symbol'] == symbol]
                sentiment_list = []
                for _, row in sentiment_history.iterrows():
                    sentiment_list.append({
                        'date': row['date'].isoformat() if isinstance(row['date'], (pd.Timestamp, datetime)) else str(row['date']),
                        'avg_sentiment': float(row['avg_sentiment']) if pd.notna(row['avg_sentiment']) else 0,
                        'article_count': int(row['article_count']) if pd.notna(row['article_count']) else 0
                    })
                stock_data['sentiment_history'] = sentiment_list
            else:
                stock_data['sentiment_history'] = []
            
            # Get risk history
            risk_history = db.get_risk_history(symbol=symbol, days=30)
            if not risk_history.empty:  # FIX: Added .empty
                risk_list = []
                for _, row in risk_history.iterrows():
                    risk_list.append({
                        'timestamp': row['timestamp'].isoformat() if isinstance(row['timestamp'], (pd.Timestamp, datetime)) else str(row['timestamp']),
                        'risk_score': float(row['risk_score']) if pd.notna(row['risk_score']) else None,
                        'risk_level': str(row['risk_level']) if pd.notna(row['risk_level']) else None
                    })
                stock_data['risk_history'] = risk_list
            else:
                stock_data['risk_history'] = []
            
            # Get recent alerts
            alerts = db.get_recent_alerts(limit=100)
            stock_alerts = [a for a in alerts if a['symbol'] == symbol]
            # Convert timestamps in alerts
            for alert in stock_alerts[:10]:
                if isinstance(alert.get('timestamp'), datetime):
                    alert['timestamp'] = alert['timestamp'].isoformat()
            stock_data['recent_alerts'] = stock_alerts[:10]
            
            return jsonify(stock_data)
            
    except Exception as e:
        log.error(f"Error in get_stock_details for {symbol}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get recent alerts with optional filtering"""
    try:
        severity = request.args.get('severity')
        limit = request.args.get('limit', 100, type=int)
        
        with DatabaseService() as db:
            alerts = db.get_recent_alerts(limit=limit)
            
            # Filter by severity
            if severity:
                alerts = [a for a in alerts if a['severity'] == severity]
            
            # Convert timestamps
            for alert in alerts:
                if isinstance(alert.get('timestamp'), datetime):
                    alert['timestamp'] = alert['timestamp'].isoformat()
            
            return jsonify({
                'count': len(alerts),
                'data': alerts
            })
            
    except Exception as e:
        log.error(f"Error in get_alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sentiment-trends', methods=['GET'])
def get_sentiment_trends():
    """Get sentiment trends over time"""
    try:
        symbol = request.args.get('symbol')
        days = request.args.get('days', 30, type=int)
        
        with DatabaseService() as db:
            sentiment_data = db.get_recent_sentiment(days=days)
            
            if symbol:
                sentiment_data = sentiment_data[sentiment_data['stock_symbol'] == symbol]
            
            data = sentiment_data.to_dict('records')
            
            # Convert dates
            for record in data:
                if isinstance(record.get('date'), datetime):
                    record['date'] = record['date'].isoformat()
            
            return jsonify({
                'count': len(data),
                'data': data
            })
            
    except Exception as e:
        log.error(f"Error in get_sentiment_trends: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/top-risks', methods=['GET'])
def get_top_risks():
    """Get top risky stocks"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        with DatabaseService() as db:
            risk_scores = db.get_latest_risk_scores()
            
            if risk_scores.empty:
                return jsonify({'error': 'No data available'}), 404
            
            # Get top risky stocks
            top_risks = risk_scores.head(limit)
            
            data = top_risks.to_dict('records')
            
            # Convert types
            for record in data:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
            
            return jsonify({
                'count': len(data),
                'data': data
            })
            
    except Exception as e:
        log.error(f"Error in get_top_risks: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/market-features/<symbol>', methods=['GET'])
def get_market_features(symbol):
    """Get historical market features for a stock"""
    try:
        days = request.args.get('days', 90, type=int)
        
        with DatabaseService() as db:
            # Use the new method with features
            market_data = db.get_market_data_with_features(symbol, days=days)
            
            if market_data.empty:
                return jsonify({'error': f'No data found for {symbol}'}), 404
            
            # Convert to records
            data = []
            for _, row in market_data.iterrows():
                record = {
                    'Date': row['Date'].isoformat() if isinstance(row['Date'], (datetime, pd.Timestamp, date)) else str(row['Date']),
                    'Close': float(row['Close']) if pd.notna(row['Close']) else None,
                    'Volume': int(row['Volume']) if pd.notna(row['Volume']) else None,
                    'volatility_21d': float(row['volatility_21d']) if pd.notna(row.get('volatility_21d')) else None,
                }
                data.append(record)
            
            return jsonify({
                'symbol': symbol,
                'count': len(data),
                'data': data
            })
            
    except Exception as e:
        log.error(f"Error in get_market_features: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/query-rag', methods=['POST'])
def query_rag():
    """
    AI Financial Assistant endpoint.
    Works like a proper financial chatbot — can answer any finance question.
    Enriches answers with real portfolio risk data and news when relevant.
    """
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400

        query = data['query']
        stock_symbol = data.get('stock_symbol')
        query_lower = query.lower()

        rag_agent = get_rag_agent()

        if not rag_agent or not rag_agent.llm:
            return jsonify({
                'query': query,
                'explanation': 'AI assistant is initializing. Please try again in a moment.',
                'sources': [], 'num_sources': 0, 'confidence': 0.0
            }), 200

        # ---- AUTO-DETECT STOCK SYMBOL FROM QUERY ----
        detected_symbol = stock_symbol
        all_symbols = []
        try:
            with DatabaseService() as db:
                risk_scores = db.get_latest_risk_scores()
                if not risk_scores.empty:
                    all_symbols = risk_scores['symbol'].unique().tolist()
                    if not detected_symbol:
                        import re
                        # Use word boundary matching to avoid false positives
                        # e.g., "mutual" should NOT match "MU"
                        query_words = set(re.findall(r'\b[A-Z]{2,5}\b', query))
                        for sym in all_symbols:
                            if sym in query_words:
                                detected_symbol = sym
                                break
        except:
            risk_scores = pd.DataFrame()

        # ---- BUILD OPTIONAL CONTEXT ----
        # Only add data context when the question is specifically about our tracked stocks
        data_context = ""
        news_context = ""
        sources = []

        # Be strict about when to inject portfolio data — only for direct stock/risk questions
        mentions_our_data = any(kw in query_lower for kw in [
            'highest risk', 'lowest risk', 'riskiest', 'safest',
            'risk score', 'risk rank', 'alert', 'watchlist',
            'our stocks', 'my stocks', 'my portfolio',
            'portfolio risk', 'risk summary', 'dashboard',
        ]) or detected_symbol is not None

        if mentions_our_data and not risk_scores.empty:
            # Stock-specific data
            if detected_symbol:
                stock_row = risk_scores[risk_scores['symbol'] == detected_symbol]
                if not stock_row.empty:
                    r = stock_row.iloc[0]
                    data_context += (
                        f"\n[Portfolio Data for {detected_symbol}]\n"
                        f"  Risk Score: {r['risk_score']:.3f} ({r.get('risk_level', 'N/A')})\n"
                        f"  Risk Rank: {r.get('risk_rank', 'N/A')} out of {len(risk_scores)}\n"
                        f"  Drivers: {r.get('risk_drivers', 'N/A')}\n"
                        f"  21d Volatility: {r.get('volatility_21d', 'N/A')}\n"
                        f"  Max Drawdown: {r.get('max_drawdown', 'N/A')}\n"
                        f"  Avg Sentiment: {r.get('avg_sentiment', 'N/A')}\n"
                    )

            # Risk ranking data
            # Risk ranking data — only when explicitly asking about rankings
            if any(kw in query_lower for kw in ['highest risk', 'riskiest', 'lowest risk', 'safest', 'risk summary', 'risk overview', 'all stocks risk']):
                top = risk_scores.nlargest(10, 'risk_score')
                data_context += "\n[Top 10 Highest Risk Stocks in Portfolio]\n"
                for _, r in top.iterrows():
                    data_context += f"  {r['symbol']}: {r['risk_score']:.3f} ({r.get('risk_level','')}) - {r.get('risk_drivers','')}\n"

                bottom = risk_scores.nsmallest(5, 'risk_score')
                data_context += "\n[Top 5 Lowest Risk Stocks]\n"
                for _, r in bottom.iterrows():
                    data_context += f"  {r['symbol']}: {r['risk_score']:.3f} ({r.get('risk_level','')})\n"

                data_context += f"\nTotal stocks: {len(risk_scores)} | "
                data_context += f"High: {len(risk_scores[risk_scores['risk_level']=='High'])} | "
                data_context += f"Medium: {len(risk_scores[risk_scores['risk_level']=='Medium'])} | "
                data_context += f"Low: {len(risk_scores[risk_scores['risk_level']=='Low'])}\n"

        # RAG news retrieval (only when relevant)
        if rag_agent.vector_store and (detected_symbol or mentions_our_data):
            try:
                docs = rag_agent.retrieve_documents(query, detected_symbol)
                if docs:
                    news_context = "\n[Recent News Articles]\n"
                    for i, doc in enumerate(docs[:5]):
                        headline = doc.page_content.split('\n')[0][:150]
                        src = doc.metadata.get('source', 'Unknown')
                        sent = doc.metadata.get('sentiment', 'neutral')
                        news_context += f"  {i+1}. [{src}] {headline} (sentiment: {sent})\n"
                        sources.append({
                            'headline': headline,
                            'source': src,
                            'url': doc.metadata.get('url', ''),
                            'sentiment': sent,
                        })
            except Exception as e:
                log.warning(f"RAG retrieval failed: {e}")

        # ---- BUILD PROMPT ----
        system_prompt = """You are an expert financial analyst and assistant. You have deep knowledge of:
- Stock markets, trading strategies, and investment analysis
- Financial metrics (P/E ratio, Sharpe ratio, beta, alpha, drawdown, volatility, etc.)
- Risk management and portfolio theory
- Financial news, market trends, and economic concepts
- Technical analysis and fundamental analysis
- Financial instruments (mutual funds, ETFs, options, bonds, derivatives, etc.)
- Personal finance (SIP, compound interest, retirement planning, tax planning)

Rules:
- ONLY answer questions related to finance, investing, markets, economics, and personal finance
- If the user asks about anything outside the financial domain (e.g., cooking, sports, movies, coding, general knowledge, health, etc.), respond ONLY with: "I'm a financial assistant and can only help with finance-related questions. Feel free to ask me about stocks, investments, markets, risk analysis, financial planning, or any other finance topic!"
- Do NOT attempt to answer non-financial questions, even partially
- If portfolio risk data or news articles are provided below, use them ONLY if directly relevant to the question
- Do NOT mention portfolio data, risk scores, or news articles unless the user specifically asked about them
- For general finance questions (definitions, calculations, concepts), answer purely from your knowledge
- For calculations, show your work step by step with correct math
- Be concise but thorough"""

        user_message = query
        if data_context or news_context:
            user_message = f"""Question: {query}

{data_context}
{news_context}

Use the above data to answer the question. Be specific with numbers and stock symbols."""

        full_prompt = f"""{system_prompt}

{user_message}

Answer:"""

        # ---- GENERATE ----
        try:
            explanation = rag_agent.llm.invoke(full_prompt).strip()
        except Exception as e:
            log.error(f"LLM generation failed: {e}")
            explanation = "I encountered an error generating a response. Please try again."

        return jsonify({
            'query': query,
            'stock_symbol': detected_symbol,
            'explanation': explanation,
            'sources': sources,
            'num_sources': len(sources),
            'confidence': 0.9 if data_context else (0.7 if sources else 0.5),
        }), 200

    except Exception as e:
        log.error(f"Error in query_rag: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'query': data.get('query', ''),
            'explanation': f"I encountered an error: {str(e)}",
            'sources': [], 'num_sources': 0, 'confidence': 0.0
        }), 200

@api_bp.route('/risk-history', methods=['GET'])
def get_risk_history():
    """Get risk history for trending"""
    try:
        symbol = request.args.get('symbol')
        days = request.args.get('days', 30, type=int)
        
        with DatabaseService() as db:
            risk_history = db.get_risk_history(symbol=symbol, days=days)
            
            data = risk_history.to_dict('records')
            
            # Convert timestamps
            for record in data:
                if isinstance(record.get('timestamp'), datetime):
                    record['timestamp'] = record['timestamp'].isoformat()
            
            return jsonify({
                'count': len(data),
                'data': data
            })
            
    except Exception as e:
        log.error(f"Error in get_risk_history: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==================== DATA REFRESH ENDPOINT ====================

@api_bp.route('/refresh-data', methods=['POST'])
def refresh_data():
    """
    Trigger a real data refresh from Yahoo Finance.
    Fetches fresh OHLCV data and recomputes risk scores.

    Request body (optional):
        {
            "period": "3mo",  // default "3mo"
            "symbols": ["AAPL", "MSFT"]  // default: all from config
        }
    """
    import threading

    data = request.get_json() or {}
    period = data.get('period', '3mo')
    symbols = data.get('symbols', None)

    def _run_refresh():
        try:
            from backend.scrapers.yfinance_collector import YFinanceCollector
            from backend.utils import load_config

            config = load_config()
            syms = symbols or config['stocks']['symbols']
            collector = YFinanceCollector()

            log.info(f"Starting data refresh for {len(syms)} stocks (period={period})")

            # Fetch market data
            market_data = collector.get_multiple_stocks(syms, period=period)
            if market_data.empty:
                log.error("Data refresh failed: no data from yfinance")
                return

            # Save to database
            from backend.database.models import SessionLocal, Stock, MarketData
            db = SessionLocal()

            inserted = 0
            for symbol in market_data['symbol'].unique():
                stock = db.query(Stock).filter(Stock.symbol == symbol).first()
                if not stock:
                    continue

                # Delete old data
                db.query(MarketData).filter(MarketData.stock_id == stock.id).delete()

                symbol_data = market_data[market_data['symbol'] == symbol]
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
            log.info(f"✓ Inserted {inserted} market data records")

            # Recompute risk scores
            try:
                from backend.agents.market_agent import MarketDataAgent
                from backend.agents.risk_agent import RiskScoringAgent

                features = MarketDataAgent().process()
                if features is not None:
                    risk_scores = RiskScoringAgent().process()
                    if risk_scores is not None:
                        with DatabaseService() as dbs:
                            dbs.save_risk_scores(risk_scores, upsert=True)
                        log.info(f"✓ Recomputed risk scores for {len(risk_scores)} stocks")
            except Exception as e:
                log.error(f"Risk recomputation failed: {e}")

            log.info("✓ Data refresh complete")

        except Exception as e:
            log.error(f"Data refresh error: {str(e)}")
            import traceback
            traceback.print_exc()

    # Run in background thread so API returns immediately
    thread = threading.Thread(target=_run_refresh, daemon=True)
    thread.start()

    return jsonify({
        'message': f'Data refresh started for {len(symbols) if symbols else "all"} stocks (period={period})',
        'status': 'running'
    }), 202