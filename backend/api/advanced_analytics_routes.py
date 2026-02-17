"""
Advanced Analytics API Routes
backend/api/advanced_analytics_routes.py

Provides endpoints for:
- Correlation matrix between stocks
- Monte Carlo simulation for price projection
- Value at Risk (VaR) and Expected Shortfall
- Portfolio optimization (min variance, max sharpe)
"""
from flask import Blueprint, request, jsonify
from backend.database import DatabaseService
from backend.database.models import Stock, MarketData, PortfolioHolding
from backend.utils import log
from backend.utils.auth import get_current_user, require_auth
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

advanced_bp = Blueprint('advanced', __name__, url_prefix='/api/advanced')


# ==================== CORRELATION MATRIX ====================

@advanced_bp.route('/correlation', methods=['GET'])
@require_auth
def get_correlation_matrix():
    """
    Compute correlation matrix of daily returns for tracked stocks.

    Query params:
        days (int): Lookback period, default 90
        symbols (str): Comma-separated symbols, default all stocks

    Returns:
        {
            "symbols": ["AAPL", "MSFT", ...],
            "matrix": [[1.0, 0.85, ...], [0.85, 1.0, ...], ...],
            "days": 90
        }
    """
    try:
        days = request.args.get('days', 90, type=int)
        symbols_param = request.args.get('symbols', '')

        with DatabaseService() as db:
            if symbols_param:
                symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
            else:
                # Get all active stocks
                stocks = db.get_all_stocks(active_only=True)
                symbols = [s.symbol for s in stocks]

            if len(symbols) < 2:
                return jsonify({'error': 'Need at least 2 stocks for correlation'}), 400

            # Fetch market data for all symbols
            cutoff_date = datetime.now().date() - timedelta(days=days)
            price_data = {}

            for symbol in symbols:
                stock = db.db.query(Stock).filter(Stock.symbol == symbol).first()
                if not stock:
                    continue

                records = db.db.query(MarketData).filter(
                    MarketData.stock_id == stock.id,
                    MarketData.date >= cutoff_date
                ).order_by(MarketData.date).all()

                if records:
                    dates = [r.date for r in records]
                    closes = [float(r.close) if r.close else None for r in records]
                    price_data[symbol] = pd.Series(closes, index=dates)

            if len(price_data) < 2:
                return jsonify({'error': 'Insufficient price data for correlation'}), 404

            # Build DataFrame and compute returns
            df = pd.DataFrame(price_data).dropna()
            if len(df) < 10:
                return jsonify({'error': 'Insufficient overlapping data points'}), 404

            returns = df.pct_change().dropna()
            corr_matrix = returns.corr()

            # Convert to serializable format
            valid_symbols = list(corr_matrix.columns)
            matrix = corr_matrix.values.tolist()

            # Round values
            matrix = [[round(v, 4) for v in row] for row in matrix]

            return jsonify({
                'symbols': valid_symbols,
                'matrix': matrix,
                'days': days,
                'data_points': len(returns),
            }), 200

    except Exception as e:
        log.error(f"Error computing correlation: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== MONTE CARLO SIMULATION ====================

@advanced_bp.route('/monte-carlo/<symbol>', methods=['GET'])
@require_auth
def monte_carlo_simulation(symbol):
    """
    Run Monte Carlo simulation for a stock's future price.

    Query params:
        days (int): Historical lookback for volatility, default 90
        simulations (int): Number of simulation paths, default 500
        forecast_days (int): Days to project forward, default 30

    Returns:
        {
            "symbol": "AAPL",
            "current_price": 185.50,
            "simulations": {
                "percentile_5": [...],
                "percentile_25": [...],
                "percentile_50": [...],
                "percentile_75": [...],
                "percentile_95": [...],
            },
            "final_prices": {
                "min": ..., "p5": ..., "p25": ..., "median": ...,
                "p75": ..., "p95": ..., "max": ..., "mean": ...
            },
            "forecast_days": 30,
            "dates": [...]
        }
    """
    try:
        symbol = symbol.upper()
        days = request.args.get('days', 90, type=int)
        num_sims = request.args.get('simulations', 500, type=int)
        forecast_days = request.args.get('forecast_days', 30, type=int)

        # Cap simulations to prevent overload
        num_sims = min(num_sims, 2000)
        forecast_days = min(forecast_days, 252)

        with DatabaseService() as db:
            stock = db.db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                return jsonify({'error': f'Stock {symbol} not found'}), 404

            cutoff_date = datetime.now().date() - timedelta(days=days)
            records = db.db.query(MarketData).filter(
                MarketData.stock_id == stock.id,
                MarketData.date >= cutoff_date
            ).order_by(MarketData.date).all()

            if len(records) < 20:
                return jsonify({'error': f'Insufficient data for {symbol} (need 20+ days)'}), 404

            closes = np.array([float(r.close) for r in records if r.close])
            returns = np.diff(np.log(closes))

            mu = returns.mean()
            sigma = returns.std()
            current_price = closes[-1]

            # Run simulations using geometric Brownian motion
            np.random.seed(42)
            simulated_paths = np.zeros((num_sims, forecast_days + 1))
            simulated_paths[:, 0] = current_price

            for t in range(1, forecast_days + 1):
                z = np.random.standard_normal(num_sims)
                simulated_paths[:, t] = simulated_paths[:, t - 1] * np.exp(
                    (mu - 0.5 * sigma ** 2) + sigma * z
                )

            # Compute percentiles at each time step
            percentiles = {}
            for p, label in [(5, 'percentile_5'), (25, 'percentile_25'), (50, 'percentile_50'),
                             (75, 'percentile_75'), (95, 'percentile_95')]:
                vals = np.percentile(simulated_paths, p, axis=0)
                percentiles[label] = [round(float(v), 2) for v in vals]

            # Final price distribution
            final_prices = simulated_paths[:, -1]

            # Generate forecast dates
            last_date = records[-1].date
            forecast_dates = []
            d = last_date
            for i in range(forecast_days + 1):
                forecast_dates.append(d.isoformat())
                d += timedelta(days=1)
                # Skip weekends
                while d.weekday() >= 5:
                    d += timedelta(days=1)

            return jsonify({
                'symbol': symbol,
                'current_price': round(float(current_price), 2),
                'simulations': percentiles,
                'final_prices': {
                    'min': round(float(np.min(final_prices)), 2),
                    'p5': round(float(np.percentile(final_prices, 5)), 2),
                    'p25': round(float(np.percentile(final_prices, 25)), 2),
                    'median': round(float(np.median(final_prices)), 2),
                    'p75': round(float(np.percentile(final_prices, 75)), 2),
                    'p95': round(float(np.percentile(final_prices, 95)), 2),
                    'max': round(float(np.max(final_prices)), 2),
                    'mean': round(float(np.mean(final_prices)), 2),
                },
                'forecast_days': forecast_days,
                'num_simulations': num_sims,
                'dates': forecast_dates,
                'annual_volatility': round(float(sigma * np.sqrt(252)), 4),
                'daily_drift': round(float(mu), 6),
            }), 200

    except Exception as e:
        log.error(f"Error in Monte Carlo for {symbol}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== VALUE AT RISK (VaR) ====================

@advanced_bp.route('/var', methods=['GET'])
@require_auth
def get_value_at_risk():
    """
    Compute Value at Risk (VaR) and Expected Shortfall for stocks or portfolio.

    Query params:
        symbols (str): Comma-separated symbols, default uses portfolio
        days (int): Historical lookback, default 90
        confidence (float): Confidence level, default 0.95
        horizon (int): VaR time horizon in days, default 1
        portfolio_value (float): Total portfolio value for dollar VaR, default 100000

    Returns:
        {
            "stocks": [
                {
                    "symbol": "AAPL",
                    "var_pct": -0.0234,
                    "var_dollar": -2340.00,
                    "es_pct": -0.0356,
                    "es_dollar": -3560.00,
                    "annual_volatility": 0.2834,
                    "daily_volatility": 0.0179,
                    "sharpe_ratio": 0.85
                }, ...
            ],
            "portfolio": {
                "var_pct": ...,
                "var_dollar": ...,
                "es_pct": ...,
                "es_dollar": ...,
            },
            "confidence": 0.95,
            "horizon": 1
        }
    """
    try:
        symbols_param = request.args.get('symbols', '')
        days = request.args.get('days', 90, type=int)
        confidence = request.args.get('confidence', 0.95, type=float)
        horizon = request.args.get('horizon', 1, type=int)
        portfolio_value = request.args.get('portfolio_value', 100000, type=float)

        user = get_current_user()

        with DatabaseService() as db:
            if symbols_param:
                symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
            else:
                # Use portfolio holdings
                holdings = db.db.query(PortfolioHolding).filter(
                    PortfolioHolding.user_id == user.id
                ).all()
                if holdings:
                    symbols = [h.symbol for h in holdings]
                else:
                    # Fall back to top 10 risk stocks
                    stocks = db.get_all_stocks(active_only=True)
                    symbols = [s.symbol for s in stocks[:10]]

            cutoff_date = datetime.now().date() - timedelta(days=days)
            stock_results = []
            all_returns = {}

            for symbol in symbols:
                stock = db.db.query(Stock).filter(Stock.symbol == symbol).first()
                if not stock:
                    continue

                records = db.db.query(MarketData).filter(
                    MarketData.stock_id == stock.id,
                    MarketData.date >= cutoff_date
                ).order_by(MarketData.date).all()

                if len(records) < 20:
                    continue

                closes = np.array([float(r.close) for r in records if r.close])
                returns = np.diff(closes) / closes[:-1]
                all_returns[symbol] = returns

                # Historical VaR
                sorted_returns = np.sort(returns)
                var_index = int(len(sorted_returns) * (1 - confidence))
                var_pct = float(sorted_returns[var_index])

                # Expected Shortfall (avg of returns worse than VaR)
                es_returns = sorted_returns[:var_index + 1]
                es_pct = float(np.mean(es_returns)) if len(es_returns) > 0 else var_pct

                # Scale to horizon
                var_pct_scaled = var_pct * np.sqrt(horizon)
                es_pct_scaled = es_pct * np.sqrt(horizon)

                # Volatility and Sharpe
                daily_vol = float(np.std(returns))
                annual_vol = daily_vol * np.sqrt(252)
                mean_return = float(np.mean(returns))
                sharpe = (mean_return * 252) / annual_vol if annual_vol > 0 else 0

                # Per-stock allocation (equal weight if no portfolio)
                weight = 1.0 / len(symbols)
                stock_value = portfolio_value * weight

                stock_results.append({
                    'symbol': symbol,
                    'var_pct': round(var_pct_scaled, 6),
                    'var_dollar': round(var_pct_scaled * stock_value, 2),
                    'es_pct': round(es_pct_scaled, 6),
                    'es_dollar': round(es_pct_scaled * stock_value, 2),
                    'annual_volatility': round(annual_vol, 4),
                    'daily_volatility': round(daily_vol, 6),
                    'sharpe_ratio': round(sharpe, 4),
                    'mean_daily_return': round(mean_return, 6),
                })

            # Portfolio-level VaR (if multiple stocks)
            portfolio_var = None
            if len(all_returns) >= 2:
                # Build returns DataFrame
                ret_df = pd.DataFrame(all_returns).dropna()
                if len(ret_df) > 10:
                    # Equal-weight portfolio returns
                    weights = np.ones(len(ret_df.columns)) / len(ret_df.columns)
                    port_returns = ret_df.values @ weights

                    sorted_port = np.sort(port_returns)
                    var_idx = int(len(sorted_port) * (1 - confidence))
                    port_var = float(sorted_port[var_idx]) * np.sqrt(horizon)
                    port_es_returns = sorted_port[:var_idx + 1]
                    port_es = float(np.mean(port_es_returns)) * np.sqrt(horizon) if len(port_es_returns) > 0 else port_var

                    portfolio_var = {
                        'var_pct': round(port_var, 6),
                        'var_dollar': round(port_var * portfolio_value, 2),
                        'es_pct': round(port_es, 6),
                        'es_dollar': round(port_es * portfolio_value, 2),
                        'diversification_benefit': round(
                            1 - abs(port_var) / sum(abs(s['var_pct']) * (1.0 / len(symbols)) for s in stock_results), 4
                        ) if stock_results else 0,
                    }

            return jsonify({
                'stocks': stock_results,
                'portfolio': portfolio_var,
                'confidence': confidence,
                'horizon': horizon,
                'portfolio_value': portfolio_value,
                'days_analyzed': days,
            }), 200

    except Exception as e:
        log.error(f"Error computing VaR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== PORTFOLIO OPTIMIZATION ====================

@advanced_bp.route('/optimize', methods=['GET'])
@require_auth
def optimize_portfolio():
    """
    Simple portfolio optimization using mean-variance approach.
    Computes the minimum variance and maximum Sharpe ratio portfolios.

    Query params:
        symbols (str): Comma-separated symbols (default: portfolio holdings)
        days (int): Historical lookback, default 180
        risk_free_rate (float): Annual risk-free rate, default 0.05

    Returns:
        {
            "symbols": [...],
            "min_variance": { "weights": {...}, "return": ..., "volatility": ..., "sharpe": ... },
            "max_sharpe": { "weights": {...}, "return": ..., "volatility": ..., "sharpe": ... },
            "current_equal_weight": { ... },
            "efficient_frontier": [{ "return": ..., "volatility": ... }, ...]
        }
    """
    try:
        symbols_param = request.args.get('symbols', '')
        days = request.args.get('days', 180, type=int)
        risk_free_rate = request.args.get('risk_free_rate', 0.05, type=float)

        user = get_current_user()

        with DatabaseService() as db:
            if symbols_param:
                symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
            else:
                holdings = db.db.query(PortfolioHolding).filter(
                    PortfolioHolding.user_id == user.id
                ).all()
                if holdings:
                    symbols = [h.symbol for h in holdings]
                else:
                    stocks = db.get_all_stocks(active_only=True)
                    symbols = [s.symbol for s in stocks[:10]]

            if len(symbols) < 2:
                return jsonify({'error': 'Need at least 2 stocks for optimization'}), 400

            cutoff_date = datetime.now().date() - timedelta(days=days)
            price_data = {}

            for symbol in symbols:
                stock = db.db.query(Stock).filter(Stock.symbol == symbol).first()
                if not stock:
                    continue
                records = db.db.query(MarketData).filter(
                    MarketData.stock_id == stock.id,
                    MarketData.date >= cutoff_date
                ).order_by(MarketData.date).all()
                if records:
                    price_data[symbol] = pd.Series(
                        [float(r.close) for r in records if r.close],
                        index=[r.date for r in records if r.close]
                    )

            if len(price_data) < 2:
                return jsonify({'error': 'Insufficient data for optimization'}), 404

            df = pd.DataFrame(price_data).dropna()
            if len(df) < 30:
                return jsonify({'error': 'Need at least 30 overlapping data points'}), 404

            returns = df.pct_change().dropna()
            valid_symbols = list(returns.columns)
            n = len(valid_symbols)

            mean_returns = returns.mean().values * 252  # annualized
            cov_matrix = returns.cov().values * 252      # annualized
            daily_rf = risk_free_rate / 252

            # Monte Carlo optimization (random portfolios)
            num_portfolios = 5000
            results = np.zeros((num_portfolios, 3 + n))  # return, vol, sharpe, weights...

            np.random.seed(42)
            for i in range(num_portfolios):
                w = np.random.random(n)
                w /= w.sum()

                port_return = np.dot(w, mean_returns)
                port_vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
                port_sharpe = (port_return - risk_free_rate) / port_vol if port_vol > 0 else 0

                results[i, 0] = port_return
                results[i, 1] = port_vol
                results[i, 2] = port_sharpe
                results[i, 3:] = w

            # Find min variance and max sharpe
            min_var_idx = np.argmin(results[:, 1])
            max_sharpe_idx = np.argmax(results[:, 2])

            def build_portfolio_result(idx):
                weights = {valid_symbols[j]: round(float(results[idx, 3 + j]), 4) for j in range(n)}
                return {
                    'weights': weights,
                    'annual_return': round(float(results[idx, 0]), 4),
                    'annual_volatility': round(float(results[idx, 1]), 4),
                    'sharpe_ratio': round(float(results[idx, 2]), 4),
                }

            # Equal weight portfolio
            eq_w = np.ones(n) / n
            eq_ret = np.dot(eq_w, mean_returns)
            eq_vol = np.sqrt(np.dot(eq_w.T, np.dot(cov_matrix, eq_w)))
            eq_sharpe = (eq_ret - risk_free_rate) / eq_vol if eq_vol > 0 else 0

            # Efficient frontier points (sample from results)
            sorted_by_vol = results[results[:, 1].argsort()]
            step = max(1, len(sorted_by_vol) // 50)
            frontier = []
            for i in range(0, len(sorted_by_vol), step):
                frontier.append({
                    'annual_return': round(float(sorted_by_vol[i, 0]), 4),
                    'annual_volatility': round(float(sorted_by_vol[i, 1]), 4),
                })

            return jsonify({
                'symbols': valid_symbols,
                'min_variance': build_portfolio_result(min_var_idx),
                'max_sharpe': build_portfolio_result(max_sharpe_idx),
                'equal_weight': {
                    'weights': {s: round(1.0 / n, 4) for s in valid_symbols},
                    'annual_return': round(float(eq_ret), 4),
                    'annual_volatility': round(float(eq_vol), 4),
                    'sharpe_ratio': round(float(eq_sharpe), 4),
                },
                'efficient_frontier': frontier,
                'days_analyzed': days,
                'risk_free_rate': risk_free_rate,
            }), 200

    except Exception as e:
        log.error(f"Error in portfolio optimization: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
