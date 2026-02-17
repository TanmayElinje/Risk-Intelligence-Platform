"""
Watchlist API Routes - Phase 3.1
backend/api/watchlist_routes.py
"""
from flask import Blueprint, request, jsonify
from backend.database import DatabaseService
from backend.database.models import Watchlist, WatchlistStock, Stock
from backend.utils import log
from backend.utils.auth import get_current_user, require_auth
from datetime import datetime
from sqlalchemy import text

watchlist_bp = Blueprint('watchlist', __name__, url_prefix='/api/watchlist')


@watchlist_bp.route('', methods=['GET'])
@require_auth
def get_user_watchlist():
    """
    Get user's default watchlist with all stocks
    
    Returns:
        {
            "watchlist": {...},
            "stocks": [...]
        }
    """
    try:
        user = get_current_user()
        
        with DatabaseService() as db:
            # Get or create default watchlist
            watchlist = db.db.query(Watchlist).filter(
                Watchlist.user_id == user.id,
                Watchlist.is_default == True
            ).first()
            
            if not watchlist:
                # Create default watchlist
                watchlist = Watchlist(
                    user_id=user.id,
                    name="My Watchlist",
                    is_default=True
                )
                db.db.add(watchlist)
                db.db.commit()
                db.db.refresh(watchlist)
            
            # Get all stocks in watchlist with risk scores using SQLAlchemy ORM
            from backend.database.models import RiskScore
            
            stocks_data = []
            for ws in watchlist.stocks:
                stock = ws.stock
                
                # Get latest risk score using ORM
                latest_risk = db.db.query(RiskScore).filter(
                    RiskScore.stock_id == stock.id
                ).order_by(RiskScore.date.desc()).first()
                
                stocks_data.append({
                    'id': ws.id,
                    'stock_id': stock.id,
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'sector': stock.sector,
                    'risk_score': float(latest_risk.risk_score) if latest_risk and latest_risk.risk_score else None,
                    'risk_level': latest_risk.risk_level if latest_risk else None,
                    'added_at': ws.added_at.isoformat() if ws.added_at else None,
                    'notes': ws.notes
                })
            
            return jsonify({
                'watchlist': {
                    'id': watchlist.id,
                    'name': watchlist.name,
                    'description': watchlist.description,
                    'stock_count': len(stocks_data)
                },
                'stocks': stocks_data
            }), 200
            
    except Exception as e:
        log.error(f"Error getting watchlist: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to get watchlist',
            'message': str(e)
        }), 500


@watchlist_bp.route('/add', methods=['POST'])
@require_auth
def add_to_watchlist():
    """
    Add a stock to user's watchlist
    
    Request body:
        {
            "symbol": "AAPL",
            "notes": "Optional notes"
        }
    
    Returns:
        {
            "message": "Stock added to watchlist",
            "watchlist_stock": {...}
        }
    """
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data.get('symbol'):
            return jsonify({'error': 'Stock symbol is required'}), 400
        
        symbol = data['symbol'].upper()
        notes = data.get('notes', '')
        
        with DatabaseService() as db:
            # Get stock
            stock = db.db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                return jsonify({'error': f'Stock {symbol} not found'}), 404
            
            # Get or create default watchlist
            watchlist = db.db.query(Watchlist).filter(
                Watchlist.user_id == user.id,
                Watchlist.is_default == True
            ).first()
            
            if not watchlist:
                watchlist = Watchlist(
                    user_id=user.id,
                    name="My Watchlist",
                    is_default=True
                )
                db.db.add(watchlist)
                db.db.commit()
                db.db.refresh(watchlist)
            
            # Check if already in watchlist
            existing = db.db.query(WatchlistStock).filter(
                WatchlistStock.watchlist_id == watchlist.id,
                WatchlistStock.stock_id == stock.id
            ).first()
            
            if existing:
                return jsonify({
                    'error': f'{symbol} is already in your watchlist'
                }), 409
            
            # Add to watchlist
            watchlist_stock = WatchlistStock(
                watchlist_id=watchlist.id,
                stock_id=stock.id,
                notes=notes,
                added_at=datetime.utcnow()
            )
            
            db.db.add(watchlist_stock)
            db.db.commit()
            db.db.refresh(watchlist_stock)
            
            log.info(f"User {user.username} added {symbol} to watchlist")
            
            return jsonify({
                'message': f'{symbol} added to watchlist',
                'watchlist_stock': watchlist_stock.to_dict()
            }), 201
            
    except Exception as e:
        log.error(f"Error adding to watchlist: {str(e)}")
        return jsonify({
            'error': 'Failed to add to watchlist',
            'message': str(e)
        }), 500


@watchlist_bp.route('/remove/<int:watchlist_stock_id>', methods=['DELETE'])
@require_auth
def remove_from_watchlist(watchlist_stock_id):
    """
    Remove a stock from watchlist
    
    Returns:
        {
            "message": "Stock removed from watchlist"
        }
    """
    try:
        user = get_current_user()
        
        with DatabaseService() as db:
            # Get watchlist stock
            ws = db.db.query(WatchlistStock).filter(
                WatchlistStock.id == watchlist_stock_id
            ).first()
            
            if not ws:
                return jsonify({'error': 'Watchlist item not found'}), 404
            
            # Verify ownership
            watchlist = db.db.query(Watchlist).filter(
                Watchlist.id == ws.watchlist_id
            ).first()
            
            if watchlist.user_id != user.id:
                return jsonify({'error': 'Unauthorized'}), 403
            
            symbol = ws.stock.symbol
            
            # Remove from watchlist
            db.db.delete(ws)
            db.db.commit()
            
            log.info(f"User {user.username} removed {symbol} from watchlist")
            
            return jsonify({
                'message': f'{symbol} removed from watchlist'
            }), 200
            
    except Exception as e:
        log.error(f"Error removing from watchlist: {str(e)}")
        return jsonify({
            'error': 'Failed to remove from watchlist',
            'message': str(e)
        }), 500


@watchlist_bp.route('/update/<int:watchlist_stock_id>', methods=['PUT'])
@require_auth
def update_watchlist_notes(watchlist_stock_id):
    """
    Update notes for a watchlist stock
    
    Request body:
        {
            "notes": "New notes"
        }
    
    Returns:
        {
            "message": "Notes updated",
            "watchlist_stock": {...}
        }
    """
    try:
        user = get_current_user()
        data = request.get_json()
        
        with DatabaseService() as db:
            # Get watchlist stock
            ws = db.db.query(WatchlistStock).filter(
                WatchlistStock.id == watchlist_stock_id
            ).first()
            
            if not ws:
                return jsonify({'error': 'Watchlist item not found'}), 404
            
            # Verify ownership
            watchlist = db.db.query(Watchlist).filter(
                Watchlist.id == ws.watchlist_id
            ).first()
            
            if watchlist.user_id != user.id:
                return jsonify({'error': 'Unauthorized'}), 403
            
            # Update notes
            ws.notes = data.get('notes', '')
            db.db.commit()
            db.db.refresh(ws)
            
            log.info(f"User {user.username} updated notes for {ws.stock.symbol}")
            
            return jsonify({
                'message': 'Notes updated',
                'watchlist_stock': ws.to_dict()
            }), 200
            
    except Exception as e:
        log.error(f"Error updating watchlist notes: {str(e)}")
        return jsonify({
            'error': 'Failed to update notes',
            'message': str(e)
        }), 500


@watchlist_bp.route('/check/<symbol>', methods=['GET'])
@require_auth
def check_in_watchlist(symbol):
    """
    Check if a stock is in user's watchlist
    
    Returns:
        {
            "in_watchlist": true/false,
            "watchlist_stock_id": 123 (if in watchlist)
        }
    """
    try:
        user = get_current_user()
        symbol = symbol.upper()
        
        with DatabaseService() as db:
            # Get stock
            stock = db.db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                return jsonify({
                    'in_watchlist': False
                }), 200
            
            # Get watchlist
            watchlist = db.db.query(Watchlist).filter(
                Watchlist.user_id == user.id,
                Watchlist.is_default == True
            ).first()
            
            if not watchlist:
                return jsonify({
                    'in_watchlist': False
                }), 200
            
            # Check if in watchlist
            ws = db.db.query(WatchlistStock).filter(
                WatchlistStock.watchlist_id == watchlist.id,
                WatchlistStock.stock_id == stock.id
            ).first()
            
            if ws:
                return jsonify({
                    'in_watchlist': True,
                    'watchlist_stock_id': ws.id,
                    'notes': ws.notes
                }), 200
            else:
                return jsonify({
                    'in_watchlist': False
                }), 200
            
    except Exception as e:
        log.error(f"Error checking watchlist: {str(e)}")
        return jsonify({
            'error': 'Failed to check watchlist',
            'message': str(e)
        }), 500