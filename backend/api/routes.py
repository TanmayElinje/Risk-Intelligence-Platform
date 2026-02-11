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
    """Query RAG system for explanations"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        stock_symbol = data.get('stock_symbol')
        
        # Get RAG agent
        rag_agent = get_rag_agent()
        
        if rag_agent is None or rag_agent.vector_store is None:
            return jsonify({
                'query': query,
                'stock_symbol': stock_symbol,
                'explanation': 'The RAG knowledge base is currently being initialized. Please try again in a moment.',
                'sources': [],
                'num_sources': 0,
                'confidence': 0.0
            }), 200
        
        # Generate explanation
        result = rag_agent.generate_explanation(query, stock_symbol)
        
        # Ensure all required fields
        response_data = {
            'query': result.get('query', query),
            'stock_symbol': result.get('stock_symbol', stock_symbol),
            'explanation': result.get('explanation', 'No explanation available'),
            'sources': result.get('sources', []),
            'num_sources': result.get('num_sources', 0),
            'confidence': result.get('confidence', 0.0)
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        log.error(f"Error in query_rag: {str(e)}")
        return jsonify({
            'query': data.get('query', ''),
            'stock_symbol': data.get('stock_symbol'),
            'explanation': f"I encountered an error while processing your question. Error: {str(e)}",
            'sources': [],
            'num_sources': 0,
            'confidence': 0.0
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