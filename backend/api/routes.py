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
        chat_history = data.get('chat_history', [])
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
                        # Match uppercase tickers (word boundary)
                        query_words = set(re.findall(r'\b[A-Z]{2,5}\b', query))
                        for sym in all_symbols:
                            if sym in query_words:
                                detected_symbol = sym
                                break

                    # Also match common company names
                    if not detected_symbol:
                        name_map = {
                            'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL',
                            'alphabet': 'GOOGL', 'amazon': 'AMZN', 'meta': 'META',
                            'facebook': 'META', 'tesla': 'TSLA', 'nvidia': 'NVDA',
                            'netflix': 'NFLX', 'adobe': 'ADBE', 'salesforce': 'CRM',
                            'paypal': 'PYPL', 'shopify': 'SHOP', 'spotify': 'SPOT',
                            'uber': 'UBER', 'zoom': 'ZM', 'snowflake': 'SNOW',
                            'palantir': 'PLTR', 'coinbase': 'COIN', 'intel': 'INTC',
                            'amd': 'AMD', 'micron': 'MU', 'oracle': 'ORCL',
                            'ibm': 'IBM', 'cisco': 'CSCO', 'qualcomm': 'QCOM',
                            'workday': 'WDAY', 'crowdstrike': 'CRWD', 'datadog': 'DDOG',
                            'palo alto': 'PANW', 'servicenow': 'NOW', 'intuit': 'INTU',
                        }
                        for name, sym in name_map.items():
                            if name in query_lower and sym in all_symbols:
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
        system_prompt = """You are an expert financial analyst assistant. Answer the user's question helpfully.

You can answer questions about: stocks, markets, investing, trading, financial metrics, company news, risk analysis, portfolio management, mutual funds, ETFs, options, bonds, personal finance, SIP, compound interest, retirement planning, economic concepts, and anything related to finance.

When portfolio data or news articles are provided below, use them in your answer. Be specific with numbers and data.

Only refuse if the question is completely unrelated to finance (like cooking, movies, or sports). For everything else, answer helpfully."""

        user_message = query
        if data_context or news_context:
            user_message = f"""Question: {query}

{data_context}
{news_context}

Use the above data to answer the question. Be specific with numbers and stock symbols."""

        # Build conversation history string (last 4 exchanges max)
        history_str = ""
        if chat_history and len(chat_history) > 1:
            # Skip the system greeting and the current user message (last item)
            recent = chat_history[1:-1][-8:]  # Last 4 exchanges (8 messages)
            if recent:
                history_str = "\n--- Conversation History ---\n"
                for msg in recent:
                    role = "User" if msg.get('role') == 'user' else "Assistant"
                    content = msg.get('content', '')[:300]  # Truncate long messages
                    history_str += f"{role}: {content}\n"
                history_str += "--- End History ---\n"

        full_prompt = f"""{system_prompt}
{history_str}
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


@api_bp.route('/query-rag-stream', methods=['POST'])
def query_rag_stream():
    """
    Streaming version of the AI assistant.
    Returns Server-Sent Events (SSE) with tokens as they're generated.
    First event sends sources/metadata, then text tokens stream in, finally a [DONE] event.
    """
    from flask import Response, stream_with_context
    import json

    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'Query is required'}), 400

    query = data['query']
    stock_symbol = data.get('stock_symbol')
    chat_history = data.get('chat_history', [])
    query_lower = query.lower()

    def generate():
        try:
            rag_agent = get_rag_agent()
            if not rag_agent or not rag_agent.llm:
                yield f"data: {json.dumps({'type': 'error', 'content': 'AI assistant is initializing.'})}\n\n"
                return

            # ---- DETECT MULTIPLE SYMBOLS ----
            detected_symbols = []
            name_map = {
                'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL',
                'alphabet': 'GOOGL', 'amazon': 'AMZN', 'meta': 'META',
                'facebook': 'META', 'tesla': 'TSLA', 'nvidia': 'NVDA',
                'netflix': 'NFLX', 'adobe': 'ADBE', 'salesforce': 'CRM',
                'paypal': 'PYPL', 'shopify': 'SHOP', 'spotify': 'SPOT',
                'uber': 'UBER', 'zoom': 'ZM', 'snowflake': 'SNOW',
                'palantir': 'PLTR', 'coinbase': 'COIN', 'intel': 'INTC',
                'amd': 'AMD', 'micron': 'MU', 'oracle': 'ORCL',
                'ibm': 'IBM', 'cisco': 'CSCO', 'qualcomm': 'QCOM',
                'workday': 'WDAY', 'crowdstrike': 'CRWD', 'datadog': 'DDOG',
                'palo alto': 'PANW', 'servicenow': 'NOW', 'intuit': 'INTU',
            }

            try:
                with DatabaseService() as db:
                    risk_scores = db.get_latest_risk_scores()
                    sentiment_data = db.get_recent_sentiment(days=14)
                    all_symbols = risk_scores['symbol'].unique().tolist() if not risk_scores.empty else []

                    if stock_symbol:
                        detected_symbols = [stock_symbol]
                    else:
                        import re
                        # Detect uppercase tickers
                        query_words = set(re.findall(r'\b[A-Z]{2,5}\b', query))
                        for sym in all_symbols:
                            if sym in query_words:
                                detected_symbols.append(sym)

                        # Detect company names
                        for name, sym in name_map.items():
                            if name in query_lower and sym in all_symbols and sym not in detected_symbols:
                                detected_symbols.append(sym)
            except:
                risk_scores = pd.DataFrame()
                sentiment_data = pd.DataFrame()

            # ---- BUILD CONTEXT ----
            data_context = ""
            news_context = ""
            sources = []

            mentions_our_data = any(kw in query_lower for kw in [
                'highest risk', 'lowest risk', 'riskiest', 'safest',
                'risk score', 'risk rank', 'alert', 'watchlist',
                'our stocks', 'my stocks', 'my portfolio',
                'portfolio risk', 'risk summary', 'dashboard',
            ]) or len(detected_symbols) > 0

            if mentions_our_data and not risk_scores.empty:
                # Multi-stock data
                for sym in detected_symbols:
                    stock_row = risk_scores[risk_scores['symbol'] == sym]
                    if not stock_row.empty:
                        r = stock_row.iloc[0]
                        data_context += (
                            f"\n[Portfolio Data for {sym}]\n"
                            f"  Risk Score: {r['risk_score']:.3f} ({r.get('risk_level', 'N/A')})\n"
                            f"  Risk Rank: {r.get('risk_rank', 'N/A')} out of {len(risk_scores)}\n"
                            f"  Drivers: {r.get('risk_drivers', 'N/A')}\n"
                            f"  21d Volatility: {r.get('volatility_21d', 'N/A')}\n"
                            f"  Max Drawdown: {r.get('max_drawdown', 'N/A')}\n"
                        )

                    # Sentiment data for this stock
                    if not sentiment_data.empty:
                        stock_sent = sentiment_data[sentiment_data['stock_symbol'] == sym]
                        if not stock_sent.empty:
                            avg_sent = stock_sent['avg_sentiment'].mean()
                            article_count = stock_sent['article_count'].sum()
                            recent_sent = stock_sent.sort_values('date', ascending=False).head(3)
                            sent_trend = "improving" if recent_sent['avg_sentiment'].is_monotonic_increasing else \
                                         "declining" if recent_sent['avg_sentiment'].is_monotonic_decreasing else "mixed"
                            data_context += (
                                f"  Sentiment (last 14d): avg={avg_sent:.3f} ({'positive' if avg_sent > 0.1 else 'negative' if avg_sent < -0.1 else 'neutral'}), "
                                f"trend={sent_trend}, articles={int(article_count)}\n"
                            )

                # Ranking data
                if any(kw in query_lower for kw in ['highest risk', 'riskiest', 'lowest risk', 'safest', 'risk summary', 'risk overview', 'all stocks risk']):
                    top = risk_scores.nlargest(10, 'risk_score')
                    data_context += "\n[Top 10 Highest Risk Stocks]\n"
                    for _, r in top.iterrows():
                        data_context += f"  {r['symbol']}: {r['risk_score']:.3f} ({r.get('risk_level','')}) - {r.get('risk_drivers','')}\n"
                    bottom = risk_scores.nsmallest(5, 'risk_score')
                    data_context += "\n[Top 5 Lowest Risk Stocks]\n"
                    for _, r in bottom.iterrows():
                        data_context += f"  {r['symbol']}: {r['risk_score']:.3f} ({r.get('risk_level','')})\n"
                    data_context += f"\nTotal: {len(risk_scores)} | High: {len(risk_scores[risk_scores['risk_level']=='High'])} | Medium: {len(risk_scores[risk_scores['risk_level']=='Medium'])} | Low: {len(risk_scores[risk_scores['risk_level']=='Low'])}\n"

            # RAG news retrieval — for each detected symbol
            if rag_agent.vector_store and (detected_symbols or mentions_our_data):
                try:
                    search_query = query
                    for sym in detected_symbols[:3]:  # Limit to 3 stocks for news
                        docs = rag_agent.retrieve_documents(f"{sym} stock news", sym)
                        if docs:
                            if not news_context:
                                news_context = "\n[Recent News Articles]\n"
                            for doc in docs[:3]:
                                headline = doc.page_content.split('\n')[0][:150]
                                src = doc.metadata.get('source', 'Unknown')
                                sent = doc.metadata.get('sentiment', 'neutral')
                                news_context += f"  [{src}] {headline} (sentiment: {sent})\n"
                                sources.append({
                                    'headline': headline, 'source': src,
                                    'url': doc.metadata.get('url', ''), 'sentiment': sent,
                                })
                    # Also do a general query search if no stock-specific results
                    if not sources:
                        docs = rag_agent.retrieve_documents(query, None)
                        if docs:
                            news_context = "\n[Recent News Articles]\n"
                            for doc in docs[:5]:
                                headline = doc.page_content.split('\n')[0][:150]
                                src = doc.metadata.get('source', 'Unknown')
                                sent = doc.metadata.get('sentiment', 'neutral')
                                news_context += f"  [{src}] {headline} (sentiment: {sent})\n"
                                sources.append({
                                    'headline': headline, 'source': src,
                                    'url': doc.metadata.get('url', ''), 'sentiment': sent,
                                })
                except:
                    pass

            # Send sources metadata first
            yield f"data: {json.dumps({'type': 'meta', 'sources': sources, 'stock_symbol': detected_symbols[0] if detected_symbols else None})}\n\n"

            # ---- BUILD PROMPT ----
            system_prompt = """You are an expert financial analyst assistant. Answer the user's question helpfully.

You can answer questions about: stocks, markets, investing, trading, financial metrics, company news, risk analysis, portfolio management, mutual funds, ETFs, options, bonds, personal finance, SIP, compound interest, retirement planning, economic concepts, and anything related to finance.

When portfolio data or news articles are provided below, use them in your answer. Be specific with numbers and data.
When comparing stocks, present a clear side-by-side comparison using the data provided.
When sentiment data is available, mention the sentiment trend and what it means.

Only refuse if the question is completely unrelated to finance (like cooking, movies, or sports). For everything else, answer helpfully.

IMPORTANT: At the very end of your answer, on a new line, write exactly:
FOLLOW_UP: [suggestion 1] | [suggestion 2] | [suggestion 3]
These should be 3 short, relevant follow-up questions the user might want to ask next. Keep each under 50 characters."""

            user_message = query
            if data_context or news_context:
                user_message = f"Question: {query}\n{data_context}\n{news_context}\nUse the above data to answer. Be specific."

            history_str = ""
            if chat_history and len(chat_history) > 1:
                recent = chat_history[1:-1][-8:]
                if recent:
                    history_str = "\n--- Conversation History ---\n"
                    for msg in recent:
                        role = "User" if msg.get('role') == 'user' else "Assistant"
                        history_str += f"{role}: {msg.get('content', '')[:300]}\n"
                    history_str += "--- End History ---\n"

            full_prompt = f"{system_prompt}\n{history_str}\n{user_message}\n\nAnswer:"

            # ---- STREAM TOKENS ----
            full_response = ""
            for chunk in rag_agent.llm.stream(full_prompt):
                if chunk:
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            # Extract follow-up suggestions from response
            follow_ups = []
            if "FOLLOW_UP:" in full_response:
                parts = full_response.split("FOLLOW_UP:")
                if len(parts) > 1:
                    suggestions_str = parts[-1].strip()
                    follow_ups = [s.strip() for s in suggestions_str.split("|") if s.strip()][:3]

            yield f"data: {json.dumps({'type': 'done', 'follow_ups': follow_ups})}\n\n"

        except Exception as e:
            log.error(f"Streaming error: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': '*',
        }
    )

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