"""
API Routes
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import pandas as pd
from backend.utils import log, load_config, load_dataframe
from backend.agents import NewsRAGAgent

# Create blueprint
api_bp = Blueprint('api', __name__)

# Initialize RAG agent (lazy loading)
_rag_agent = None

def get_rag_agent():
    """Get or initialize RAG agent"""
    global _rag_agent
    if _rag_agent is None:
        try:
            _rag_agent = NewsRAGAgent()
            _rag_agent.vector_store = _rag_agent.load_vector_store()
            log.info("RAG agent initialized for API")
        except Exception as e:
            log.error(f"Failed to initialize RAG agent: {str(e)}")
            _rag_agent = None
    return _rag_agent

def load_risk_scores():
    """Load risk scores"""
    config = load_config()
    path = f"{config['paths']['data_processed']}/risk_scores.csv"
    try:
        return load_dataframe(path, format='csv')
    except:
        return pd.DataFrame()

def load_alerts():
    """Load alerts"""
    config = load_config()
    path = f"{config['paths']['data_processed']}/alerts.csv"
    try:
        return load_dataframe(path, format='csv')
    except:
        return pd.DataFrame()

def load_sentiment():
    """Load sentiment scores"""
    config = load_config()
    path = f"{config['paths']['data_processed']}/sentiment_scores.csv"
    try:
        return load_dataframe(path, format='csv')
    except:
        return pd.DataFrame()

def load_market_features():
    """Load market features"""
    config = load_config()
    path = f"{config['paths']['features']}/market_features.parquet"
    try:
        return load_dataframe(path, format='parquet')
    except:
        return pd.DataFrame()

def load_risk_history():
    """Load risk history"""
    config = load_config()
    path = f"{config['paths']['data_processed']}/risk_history.csv"
    try:
        df = load_dataframe(path, format='csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except:
        return pd.DataFrame()

# ============================================
# ROUTES
# ============================================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Risk Intelligence API'
    })

@api_bp.route('/risk-scores', methods=['GET'])
def get_risk_scores():
    """
    Get all risk scores
    
    Query params:
        - risk_level: Filter by risk level (Low, Medium, High)
        - limit: Limit number of results
    """
    try:
        risk_df = load_risk_scores()
        
        if risk_df.empty:
            return jsonify({'error': 'No risk data available'}), 404
        
        # Filter by risk level if specified
        risk_level = request.args.get('risk_level')
        if risk_level:
            risk_df = risk_df[risk_df['risk_level'] == risk_level]
        
        # Limit results if specified
        limit = request.args.get('limit', type=int)
        if limit:
            risk_df = risk_df.head(limit)
        
        # Convert to dict
        data = risk_df.to_dict(orient='records')
        
        return jsonify({
            'count': len(data),
            'data': data
        })
        
    except Exception as e:
        log.error(f"Error in get_risk_scores: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stock/<symbol>', methods=['GET'])
def get_stock_details(symbol):
    """
    Get detailed information for a specific stock
    
    Params:
        symbol: Stock symbol (e.g., AAPL)
    """
    try:
        # Get risk score
        risk_df = load_risk_scores()
        stock_risk = risk_df[risk_df['symbol'] == symbol]
        
        if stock_risk.empty:
            return jsonify({'error': f'Stock {symbol} not found'}), 404
        
        stock_data = stock_risk.iloc[0].to_dict()
        
        # Get sentiment history
        sentiment_df = load_sentiment()
        if not sentiment_df.empty:
            stock_sentiment = sentiment_df[sentiment_df['stock_symbol'] == symbol]
            stock_data['sentiment_history'] = stock_sentiment.to_dict(orient='records')
        
        # Get recent alerts
        alerts_df = load_alerts()
        if not alerts_df.empty:
            stock_alerts = alerts_df[alerts_df['symbol'] == symbol]
            stock_data['recent_alerts'] = stock_alerts.tail(5).to_dict(orient='records')
        
        # Get risk history
        history_df = load_risk_history()
        if not history_df.empty:
            stock_history = history_df[history_df['symbol'] == symbol]
            stock_data['risk_history'] = stock_history.tail(30).to_dict(orient='records')
        
        return jsonify(stock_data)
        
    except Exception as e:
        log.error(f"Error in get_stock_details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """
    Get recent alerts
    
    Query params:
        - limit: Number of alerts to return (default: 20)
        - severity: Filter by severity (HIGH, MEDIUM)
    """
    try:
        alerts_df = load_alerts()
        
        if alerts_df.empty:
            return jsonify({'count': 0, 'data': []})
        
        # Filter by severity if specified
        severity = request.args.get('severity')
        if severity:
            alerts_df = alerts_df[alerts_df['severity'] == severity.upper()]
        
        # Sort by timestamp
        if 'timestamp' in alerts_df.columns:
            alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp'])
            alerts_df = alerts_df.sort_values('timestamp', ascending=False)
        
        # Limit results
        limit = request.args.get('limit', default=20, type=int)
        alerts_df = alerts_df.head(limit)
        
        data = alerts_df.to_dict(orient='records')
        
        return jsonify({
            'count': len(data),
            'data': data
        })
        
    except Exception as e:
        log.error(f"Error in get_alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sentiment-trends', methods=['GET'])
def get_sentiment_trends():
    """
    Get sentiment trends over time
    
    Query params:
        - symbol: Filter by stock symbol
        - days: Number of days to include (default: 30)
    """
    try:
        sentiment_df = load_sentiment()
        
        if sentiment_df.empty:
            return jsonify({'count': 0, 'data': []})
        
        # Filter by symbol if specified
        symbol = request.args.get('symbol')
        if symbol:
            sentiment_df = sentiment_df[sentiment_df['stock_symbol'] == symbol]
        
        # Filter by date range
        days = request.args.get('days', default=30, type=int)
        sentiment_df['date'] = pd.to_datetime(sentiment_df['date'])
        cutoff_date = datetime.now() - timedelta(days=days)
        sentiment_df = sentiment_df[sentiment_df['date'] >= cutoff_date]
        
        # Sort by date
        sentiment_df = sentiment_df.sort_values('date')
        
        data = sentiment_df.to_dict(orient='records')
        
        return jsonify({
            'count': len(data),
            'data': data
        })
        
    except Exception as e:
        log.error(f"Error in get_sentiment_trends: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/query-rag', methods=['POST'])
def query_rag():
    """
    Query RAG system for explanations
    
    Body:
        {
            "query": "Why is AAPL risk high?",
            "stock_symbol": "AAPL"  (optional)
        }
    """
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
                'error': 'RAG system not available',
                'query': query,
                'explanation': 'The knowledge base is not currently available.'
            }), 503
        
        # Generate explanation
        result = rag_agent.generate_explanation(query, stock_symbol)
        
        return jsonify(result)
        
    except Exception as e:
        log.error(f"Error in query_rag: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/top-risks', methods=['GET'])
def get_top_risks():
    """
    Get top risky stocks
    
    Query params:
        - limit: Number of stocks to return (default: 10)
    """
    try:
        risk_df = load_risk_scores()
        
        if risk_df.empty:
            return jsonify({'error': 'No risk data available'}), 404
        
        # Get top risks
        limit = request.args.get('limit', default=10, type=int)
        top_risks = risk_df.head(limit)
        
        data = top_risks.to_dict(orient='records')
        
        return jsonify({
            'count': len(data),
            'data': data
        })
        
    except Exception as e:
        log.error(f"Error in get_top_risks: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/market-features/<symbol>', methods=['GET'])
def get_market_features(symbol):
    """
    Get historical market features for a stock
    
    Params:
        symbol: Stock symbol
    
    Query params:
        - days: Number of days to include (default: 90)
    """
    try:
        features_df = load_market_features()
        
        if features_df.empty:
            return jsonify({'error': 'No market data available'}), 404
        
        # Filter by symbol
        stock_features = features_df[features_df['symbol'] == symbol]
        
        if stock_features.empty:
            return jsonify({'error': f'Stock {symbol} not found'}), 404
        
        # Filter by date range
        days = request.args.get('days', default=90, type=int)
        stock_features = stock_features.sort_values('Date')
        stock_features = stock_features.tail(days)
        
        # Select relevant columns
        feature_cols = [
            'Date', 'Close', 'returns', 'volatility_21d', 'volatility_60d',
            'max_drawdown', 'beta', 'sharpe_ratio', 'atr_pct', 'liquidity_risk'
        ]
        available_cols = [col for col in feature_cols if col in stock_features.columns]
        stock_features = stock_features[available_cols]
        
        data = stock_features.to_dict(orient='records')
        
        return jsonify({
            'symbol': symbol,
            'count': len(data),
            'data': data
        })
        
    except Exception as e:
        log.error(f"Error in get_market_features: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get overall system statistics"""
    try:
        risk_df = load_risk_scores()
        alerts_df = load_alerts()
        sentiment_df = load_sentiment()
        
        stats = {
            'total_stocks': len(risk_df) if not risk_df.empty else 0,
            'high_risk_stocks': int((risk_df['risk_level'] == 'High').sum()) if not risk_df.empty else 0,
            'medium_risk_stocks': int((risk_df['risk_level'] == 'Medium').sum()) if not risk_df.empty else 0,
            'low_risk_stocks': int((risk_df['risk_level'] == 'Low').sum()) if not risk_df.empty else 0,
            'total_alerts': len(alerts_df) if not alerts_df.empty else 0,
            'avg_risk_score': float(risk_df['risk_score'].mean()) if not risk_df.empty else 0,
            'avg_sentiment': float(sentiment_df['avg_sentiment'].mean()) if not sentiment_df.empty else 0,
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        log.error(f"Error in get_stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/risk-history', methods=['GET'])
def get_risk_history():
    """
    Get risk history for trending
    
    Query params:
        - symbol: Filter by stock symbol
        - days: Number of days (default: 30)
    """
    try:
        history_df = load_risk_history()
        
        if history_df.empty:
            return jsonify({'count': 0, 'data': []})
        
        # Filter by symbol if specified
        symbol = request.args.get('symbol')
        if symbol:
            history_df = history_df[history_df['symbol'] == symbol]
        
        # Filter by days
        days = request.args.get('days', default=30, type=int)
        cutoff_date = datetime.now() - timedelta(days=days)
        history_df = history_df[history_df['timestamp'] >= cutoff_date]
        
        # Sort by timestamp
        history_df = history_df.sort_values('timestamp')
        
        data = history_df.to_dict(orient='records')
        
        return jsonify({
            'count': len(data),
            'data': data
        })
        
    except Exception as e:
        log.error(f"Error in get_risk_history: {str(e)}")
        return jsonify({'error': str(e)}), 500