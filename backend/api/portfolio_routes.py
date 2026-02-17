"""
Portfolio API Routes
backend/api/portfolio_routes.py

Tracks user stock holdings, buy/sell transactions, and portfolio performance.
Uses the same auth and DB patterns as watchlist_routes.py.
"""
from flask import Blueprint, request, jsonify
from backend.database import DatabaseService
from backend.database.models import (
    PortfolioHolding, PortfolioTransaction, Stock, MarketData, RiskScore
)
from backend.utils import log
from backend.utils.auth import get_current_user, require_auth
from datetime import datetime
from sqlalchemy import desc, func

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/portfolio')


# ==================== GET PORTFOLIO ====================

@portfolio_bp.route('', methods=['GET'])
@require_auth
def get_portfolio():
    """
    Get user's portfolio with all holdings and summary.
    Enriches each holding with current price from latest market data
    and risk score from the risk_scores table.

    Returns:
        {
            "holdings": [...],
            "summary": {
                "total_value": ...,
                "total_cost": ...,
                "total_gain_loss": ...,
                "total_gain_loss_pct": ...,
                "holdings_count": ...
            }
        }
    """
    try:
        user = get_current_user()

        with DatabaseService() as db:
            holdings = db.db.query(PortfolioHolding).filter(
                PortfolioHolding.user_id == user.id
            ).order_by(PortfolioHolding.symbol).all()

            portfolio_data = []
            total_value = 0
            total_cost = 0

            for holding in holdings:
                # Try to get actual current price from market data
                stock = db.db.query(Stock).filter(
                    Stock.symbol == holding.symbol
                ).first()

                current_price = float(holding.purchase_price)  # fallback

                if stock:
                    # Get latest closing price
                    latest_market = db.db.query(MarketData).filter(
                        MarketData.stock_id == stock.id
                    ).order_by(MarketData.date.desc()).first()

                    if latest_market and latest_market.close:
                        current_price = float(latest_market.close)

                    # Get latest risk score
                    latest_risk = db.db.query(RiskScore).filter(
                        RiskScore.stock_id == stock.id
                    ).order_by(RiskScore.date.desc()).first()
                else:
                    latest_risk = None

                quantity = float(holding.quantity)
                purchase_price = float(holding.purchase_price)
                current_value = quantity * current_price
                cost_basis = quantity * purchase_price
                gain_loss = current_value - cost_basis
                gain_loss_pct = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0

                total_value += current_value
                total_cost += cost_basis

                portfolio_data.append({
                    **holding.to_dict(),
                    'current_price': round(current_price, 2),
                    'current_value': round(current_value, 2),
                    'cost_basis': round(cost_basis, 2),
                    'gain_loss': round(gain_loss, 2),
                    'gain_loss_pct': round(gain_loss_pct, 2),
                    'risk_score': float(latest_risk.risk_score) if latest_risk and latest_risk.risk_score else None,
                    'risk_level': latest_risk.risk_level if latest_risk else None,
                    'stock_name': stock.name if stock else None,
                    'sector': stock.sector if stock else None,
                })

            total_gain_loss = total_value - total_cost
            total_gain_loss_pct = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0

            return jsonify({
                'holdings': portfolio_data,
                'summary': {
                    'total_value': round(total_value, 2),
                    'total_cost': round(total_cost, 2),
                    'total_gain_loss': round(total_gain_loss, 2),
                    'total_gain_loss_pct': round(total_gain_loss_pct, 2),
                    'holdings_count': len(holdings),
                }
            }), 200

    except Exception as e:
        log.error(f"Error getting portfolio: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to get portfolio',
            'message': str(e)
        }), 500


# ==================== ADD HOLDING ====================

@portfolio_bp.route('', methods=['POST'])
@require_auth
def add_holding():
    """
    Add a stock holding to user's portfolio.
    If the symbol already exists, averages the purchase price.

    Request body:
        {
            "symbol": "AAPL",
            "quantity": 10,
            "purchase_price": 150.00,
            "purchase_date": "2024-01-15",  (optional)
            "notes": "Long-term hold"        (optional)
        }

    Returns:
        {
            "message": "Holding added successfully",
            "holding": {...}
        }
    """
    try:
        user = get_current_user()
        data = request.get_json()

        symbol = data.get('symbol')
        quantity = data.get('quantity')
        purchase_price = data.get('purchase_price')
        purchase_date = data.get('purchase_date')
        notes = data.get('notes', '')

        if not all([symbol, quantity, purchase_price]):
            return jsonify({'error': 'Missing required fields: symbol, quantity, purchase_price'}), 400

        try:
            quantity = float(quantity)
            purchase_price = float(purchase_price)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid quantity or price'}), 400

        if quantity <= 0 or purchase_price <= 0:
            return jsonify({'error': 'Quantity and price must be positive'}), 400

        symbol = symbol.upper().strip()

        with DatabaseService() as db:
            # Check if holding already exists for this user+symbol
            existing = db.db.query(PortfolioHolding).filter(
                PortfolioHolding.user_id == user.id,
                PortfolioHolding.symbol == symbol
            ).first()

            if existing:
                # Average the purchase price
                old_qty = float(existing.quantity)
                old_price = float(existing.purchase_price)
                total_quantity = old_qty + quantity
                total_cost = (old_qty * old_price) + (quantity * purchase_price)
                avg_price = total_cost / total_quantity

                existing.quantity = total_quantity
                existing.purchase_price = avg_price
                existing.updated_at = datetime.utcnow()
                if notes:
                    existing.notes = notes

                holding = existing
            else:
                # Create new holding
                holding = PortfolioHolding(
                    user_id=user.id,
                    symbol=symbol,
                    quantity=quantity,
                    purchase_price=purchase_price,
                    purchase_date=datetime.fromisoformat(purchase_date) if purchase_date else datetime.utcnow(),
                    notes=notes
                )
                db.db.add(holding)

            # Record the transaction
            transaction = PortfolioTransaction(
                user_id=user.id,
                symbol=symbol,
                transaction_type='BUY',
                quantity=quantity,
                price=purchase_price,
                transaction_date=datetime.fromisoformat(purchase_date) if purchase_date else datetime.utcnow(),
                notes=notes
            )
            db.db.add(transaction)

            db.db.commit()
            db.db.refresh(holding)

            log.info(f"User {user.username} added {quantity} shares of {symbol} at ${purchase_price}")

            return jsonify({
                'message': 'Holding added successfully',
                'holding': holding.to_dict()
            }), 201

    except Exception as e:
        log.error(f"Error adding holding: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to add holding',
            'message': str(e)
        }), 500


# ==================== UPDATE HOLDING ====================

@portfolio_bp.route('/<int:holding_id>', methods=['PUT'])
@require_auth
def update_holding(holding_id):
    """
    Update a portfolio holding.

    Request body (all optional):
        {
            "quantity": 15,
            "purchase_price": 155.00,
            "notes": "Updated notes"
        }

    Returns:
        {
            "message": "Holding updated successfully",
            "holding": {...}
        }
    """
    try:
        user = get_current_user()

        with DatabaseService() as db:
            holding = db.db.query(PortfolioHolding).filter(
                PortfolioHolding.id == holding_id,
                PortfolioHolding.user_id == user.id
            ).first()

            if not holding:
                return jsonify({'error': 'Holding not found'}), 404

            data = request.get_json()

            if 'quantity' in data:
                holding.quantity = float(data['quantity'])
            if 'purchase_price' in data:
                holding.purchase_price = float(data['purchase_price'])
            if 'notes' in data:
                holding.notes = data['notes']

            holding.updated_at = datetime.utcnow()
            db.db.commit()
            db.db.refresh(holding)

            log.info(f"User {user.username} updated holding {holding.symbol}")

            return jsonify({
                'message': 'Holding updated successfully',
                'holding': holding.to_dict()
            }), 200

    except Exception as e:
        log.error(f"Error updating holding: {str(e)}")
        return jsonify({
            'error': 'Failed to update holding',
            'message': str(e)
        }), 500


# ==================== DELETE HOLDING ====================

@portfolio_bp.route('/<int:holding_id>', methods=['DELETE'])
@require_auth
def delete_holding(holding_id):
    """
    Delete a portfolio holding.

    Returns:
        {
            "message": "Holding deleted successfully"
        }
    """
    try:
        user = get_current_user()

        with DatabaseService() as db:
            holding = db.db.query(PortfolioHolding).filter(
                PortfolioHolding.id == holding_id,
                PortfolioHolding.user_id == user.id
            ).first()

            if not holding:
                return jsonify({'error': 'Holding not found'}), 404

            symbol = holding.symbol
            db.db.delete(holding)
            db.db.commit()

            log.info(f"User {user.username} deleted holding {symbol}")

            return jsonify({
                'message': f'{symbol} removed from portfolio'
            }), 200

    except Exception as e:
        log.error(f"Error deleting holding: {str(e)}")
        return jsonify({
            'error': 'Failed to delete holding',
            'message': str(e)
        }), 500


# ==================== SELL HOLDING ====================

@portfolio_bp.route('/<int:holding_id>/sell', methods=['POST'])
@require_auth
def sell_holding(holding_id):
    """
    Sell shares from a holding (partial or full).

    Request body:
        {
            "quantity": 5,
            "price": 170.00,
            "notes": "Taking profits"  (optional)
        }

    Returns:
        {
            "message": "Stock sold successfully",
            "transaction": {...}
        }
    """
    try:
        user = get_current_user()

        with DatabaseService() as db:
            holding = db.db.query(PortfolioHolding).filter(
                PortfolioHolding.id == holding_id,
                PortfolioHolding.user_id == user.id
            ).first()

            if not holding:
                return jsonify({'error': 'Holding not found'}), 404

            data = request.get_json()
            quantity = float(data.get('quantity', 0))
            sell_price = float(data.get('price', 0))
            notes = data.get('notes', '')

            if quantity <= 0:
                return jsonify({'error': 'Quantity must be positive'}), 400

            if quantity > float(holding.quantity):
                return jsonify({
                    'error': f'Cannot sell {quantity} shares, you only have {float(holding.quantity)}'
                }), 400

            if sell_price <= 0:
                return jsonify({'error': 'Sell price must be positive'}), 400

            # Record sell transaction
            transaction = PortfolioTransaction(
                user_id=user.id,
                symbol=holding.symbol,
                transaction_type='SELL',
                quantity=quantity,
                price=sell_price,
                notes=notes
            )
            db.db.add(transaction)

            # Update or remove holding
            if quantity >= float(holding.quantity):
                db.db.delete(holding)
                log.info(f"User {user.username} sold all {holding.symbol}")
            else:
                holding.quantity = float(holding.quantity) - quantity
                holding.updated_at = datetime.utcnow()
                log.info(f"User {user.username} sold {quantity} shares of {holding.symbol}")

            db.db.commit()

            return jsonify({
                'message': 'Stock sold successfully',
                'transaction': transaction.to_dict()
            }), 200

    except Exception as e:
        log.error(f"Error selling holding: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to sell holding',
            'message': str(e)
        }), 500


# ==================== TRANSACTION HISTORY ====================

@portfolio_bp.route('/transactions', methods=['GET'])
@require_auth
def get_transactions():
    """
    Get user's transaction history.

    Returns:
        {
            "transactions": [...]
        }
    """
    try:
        user = get_current_user()

        with DatabaseService() as db:
            transactions = db.db.query(PortfolioTransaction).filter(
                PortfolioTransaction.user_id == user.id
            ).order_by(PortfolioTransaction.transaction_date.desc()).all()

            return jsonify({
                'transactions': [t.to_dict() for t in transactions]
            }), 200

    except Exception as e:
        log.error(f"Error getting transactions: {str(e)}")
        return jsonify({
            'error': 'Failed to get transactions',
            'message': str(e)
        }), 500
