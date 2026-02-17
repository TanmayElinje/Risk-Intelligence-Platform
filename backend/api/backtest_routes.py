"""
Backtesting & Historical Analysis API Routes
backend/api/backtest_routes.py

Provides endpoints for:
- Strategy backtesting (buy & hold, risk-based, moving average crossover)
- Historical drawdown analysis
- Rolling performance metrics
- Return distribution analysis
- Period comparison
"""
from flask import Blueprint, request, jsonify
from backend.database import DatabaseService
from backend.database.models import Stock, MarketData, RiskScore
from backend.utils import log
from backend.utils.auth import get_current_user, require_auth
from datetime import datetime, timedelta
from sqlalchemy import func
import numpy as np
import pandas as pd

backtest_bp = Blueprint('backtest', __name__, url_prefix='/api/backtest')


# ==================== STRATEGY BACKTEST ====================

@backtest_bp.route('/run', methods=['POST'])
@require_auth
def run_backtest():
    """
    Run a backtest on historical data with a given strategy.

    Request body:
        {
            "symbol": "AAPL",
            "strategy": "buy_and_hold" | "risk_based" | "moving_average" | "mean_reversion",
            "start_days_ago": 365,
            "initial_capital": 10000,
            "params": {
                // strategy-specific params
                "short_window": 20,  // for moving_average
                "long_window": 50,
                "risk_threshold": 0.6,  // for risk_based
                "lookback": 20,  // for mean_reversion
                "z_entry": -1.0,
                "z_exit": 0.5
            }
        }

    Returns:
        {
            "symbol": "AAPL",
            "strategy": "buy_and_hold",
            "equity_curve": [{"date": ..., "equity": ..., "benchmark": ...}, ...],
            "trades": [{"date": ..., "action": "BUY"/"SELL", "price": ..., "shares": ...}, ...],
            "metrics": {
                "total_return": ...,
                "annual_return": ...,
                "max_drawdown": ...,
                "sharpe_ratio": ...,
                "win_rate": ...,
                "total_trades": ...,
                "benchmark_return": ...
            }
        }
    """
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'AAPL').upper()
        strategy = data.get('strategy', 'buy_and_hold')
        start_days = data.get('start_days_ago', 365)
        initial_capital = data.get('initial_capital', 10000)
        params = data.get('params', {})

        with DatabaseService() as db:
            stock = db.db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                return jsonify({'error': f'Stock {symbol} not found'}), 404

            cutoff = datetime.now().date() - timedelta(days=start_days)
            records = db.db.query(MarketData).filter(
                MarketData.stock_id == stock.id,
                MarketData.date >= cutoff
            ).order_by(MarketData.date).all()

            if len(records) < 30:
                return jsonify({'error': f'Insufficient data for {symbol} (need 30+ days)'}), 404

            dates = [r.date for r in records]
            closes = np.array([float(r.close) for r in records if r.close])
            volumes = np.array([int(r.volume) if r.volume else 0 for r in records])

            if len(closes) < 30:
                return jsonify({'error': 'Insufficient price data'}), 404

            # Also load risk scores if needed
            risk_data = {}
            if strategy == 'risk_based':
                from sqlalchemy import text
                risk_query = text("""
                    SELECT rs.date, rs.risk_score 
                    FROM risk_scores rs 
                    JOIN stocks s ON rs.stock_id = s.id 
                    WHERE s.symbol = :symbol 
                    ORDER BY rs.date
                """)
                risk_results = db.db.execute(risk_query, {'symbol': symbol}).fetchall()
                for row in risk_results:
                    risk_data[row[0]] = float(row[1]) if row[1] else 0.5

            # Run the appropriate strategy
            if strategy == 'buy_and_hold':
                result = _backtest_buy_and_hold(dates, closes, initial_capital)
            elif strategy == 'risk_based':
                threshold = params.get('risk_threshold', 0.6)
                result = _backtest_risk_based(dates, closes, initial_capital, risk_data, threshold)
            elif strategy == 'moving_average':
                short_w = params.get('short_window', 20)
                long_w = params.get('long_window', 50)
                result = _backtest_moving_average(dates, closes, initial_capital, short_w, long_w)
            elif strategy == 'mean_reversion':
                lookback = params.get('lookback', 20)
                z_entry = params.get('z_entry', -1.0)
                z_exit = params.get('z_exit', 0.5)
                result = _backtest_mean_reversion(dates, closes, initial_capital, lookback, z_entry, z_exit)
            else:
                return jsonify({'error': f'Unknown strategy: {strategy}'}), 400

            # Compute benchmark (buy and hold) for comparison
            benchmark = _backtest_buy_and_hold(dates, closes, initial_capital)

            # Merge benchmark into equity curve
            bench_map = {e['date']: e['equity'] for e in benchmark['equity_curve']}
            for point in result['equity_curve']:
                point['benchmark'] = bench_map.get(point['date'], initial_capital)

            # Add benchmark return to metrics
            result['metrics']['benchmark_return'] = benchmark['metrics']['total_return']

            result['symbol'] = symbol
            result['strategy'] = strategy
            result['initial_capital'] = initial_capital
            result['start_date'] = dates[0].isoformat()
            result['end_date'] = dates[-1].isoformat()
            result['data_points'] = len(closes)

            return jsonify(result), 200

    except Exception as e:
        log.error(f"Error in backtest: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def _compute_metrics(equity_curve_values, initial_capital, trades, trading_days=252):
    """Compute standard backtest performance metrics"""
    equity = np.array(equity_curve_values)
    total_return = (equity[-1] - initial_capital) / initial_capital
    n_days = len(equity)
    annual_return = (1 + total_return) ** (trading_days / max(n_days, 1)) - 1

    # Max drawdown
    peak = np.maximum.accumulate(equity)
    drawdown = (equity - peak) / peak
    max_drawdown = float(np.min(drawdown))

    # Daily returns for Sharpe
    daily_returns = np.diff(equity) / equity[:-1]
    sharpe = 0
    if len(daily_returns) > 1 and np.std(daily_returns) > 0:
        sharpe = (np.mean(daily_returns) * trading_days) / (np.std(daily_returns) * np.sqrt(trading_days))

    # Win rate from trades
    profits = []
    i = 0
    while i < len(trades) - 1:
        if trades[i]['action'] == 'BUY' and trades[i + 1]['action'] == 'SELL':
            profit = trades[i + 1]['price'] - trades[i]['price']
            profits.append(profit)
            i += 2
        else:
            i += 1

    win_rate = sum(1 for p in profits if p > 0) / max(len(profits), 1)

    # Volatility
    annual_vol = float(np.std(daily_returns) * np.sqrt(trading_days)) if len(daily_returns) > 1 else 0

    # Sortino (downside deviation)
    neg_returns = daily_returns[daily_returns < 0]
    downside_dev = float(np.std(neg_returns) * np.sqrt(trading_days)) if len(neg_returns) > 0 else 0
    sortino = float(np.mean(daily_returns) * trading_days / downside_dev) if downside_dev > 0 else 0

    return {
        'total_return': round(float(total_return), 4),
        'annual_return': round(float(annual_return), 4),
        'max_drawdown': round(float(max_drawdown), 4),
        'sharpe_ratio': round(float(sharpe), 4),
        'sortino_ratio': round(float(sortino), 4),
        'annual_volatility': round(float(annual_vol), 4),
        'win_rate': round(float(win_rate), 4),
        'total_trades': len(trades),
        'final_equity': round(float(equity[-1]), 2),
    }


def _backtest_buy_and_hold(dates, closes, capital):
    """Simple buy and hold strategy"""
    shares = capital / closes[0]
    equity_curve = []
    for i, (d, p) in enumerate(zip(dates, closes)):
        equity_curve.append({
            'date': d.isoformat(),
            'equity': round(float(shares * p), 2),
        })

    trades = [
        {'date': dates[0].isoformat(), 'action': 'BUY', 'price': round(float(closes[0]), 2), 'shares': round(float(shares), 4)},
    ]

    metrics = _compute_metrics([e['equity'] for e in equity_curve], capital, trades)
    return {'equity_curve': equity_curve, 'trades': trades, 'metrics': metrics}


def _backtest_risk_based(dates, closes, capital, risk_data, threshold):
    """
    Risk-based strategy:
    - Sell when risk score > threshold
    - Buy back when risk score < threshold
    """
    cash = capital
    shares = 0
    in_position = False
    equity_curve = []
    trades = []

    for i, (d, p) in enumerate(zip(dates, closes)):
        risk = risk_data.get(d, 0.5)

        if not in_position and risk < threshold:
            # Buy
            shares = cash / p
            cash = 0
            in_position = True
            trades.append({'date': d.isoformat(), 'action': 'BUY', 'price': round(float(p), 2),
                           'shares': round(float(shares), 4), 'risk_score': round(risk, 3)})
        elif in_position and risk >= threshold:
            # Sell
            cash = shares * p
            shares = 0
            in_position = False
            trades.append({'date': d.isoformat(), 'action': 'SELL', 'price': round(float(p), 2),
                           'shares': 0, 'risk_score': round(risk, 3)})

        equity = cash + shares * p
        equity_curve.append({'date': d.isoformat(), 'equity': round(float(equity), 2)})

    metrics = _compute_metrics([e['equity'] for e in equity_curve], capital, trades)
    return {'equity_curve': equity_curve, 'trades': trades, 'metrics': metrics}


def _backtest_moving_average(dates, closes, capital, short_window, long_window):
    """
    Moving average crossover strategy:
    - Buy when short MA crosses above long MA
    - Sell when short MA crosses below long MA
    """
    cash = capital
    shares = 0
    in_position = False
    equity_curve = []
    trades = []

    short_ma = pd.Series(closes).rolling(window=short_window).mean().values
    long_ma = pd.Series(closes).rolling(window=long_window).mean().values

    for i, (d, p) in enumerate(zip(dates, closes)):
        if i < long_window:
            equity_curve.append({'date': d.isoformat(), 'equity': round(float(capital), 2)})
            continue

        if not in_position and short_ma[i] > long_ma[i] and short_ma[i - 1] <= long_ma[i - 1]:
            # Golden cross - BUY
            shares = cash / p
            cash = 0
            in_position = True
            trades.append({'date': d.isoformat(), 'action': 'BUY', 'price': round(float(p), 2),
                           'shares': round(float(shares), 4)})
        elif in_position and short_ma[i] < long_ma[i] and short_ma[i - 1] >= long_ma[i - 1]:
            # Death cross - SELL
            cash = shares * p
            shares = 0
            in_position = False
            trades.append({'date': d.isoformat(), 'action': 'SELL', 'price': round(float(p), 2),
                           'shares': 0})

        equity = cash + shares * p
        equity_curve.append({'date': d.isoformat(), 'equity': round(float(equity), 2)})

    metrics = _compute_metrics([e['equity'] for e in equity_curve], capital, trades)
    # Add MA data for charting
    ma_data = []
    for i, d in enumerate(dates):
        ma_data.append({
            'date': d.isoformat(),
            'short_ma': round(float(short_ma[i]), 2) if not np.isnan(short_ma[i]) else None,
            'long_ma': round(float(long_ma[i]), 2) if not np.isnan(long_ma[i]) else None,
            'close': round(float(closes[i]), 2),
        })
    return {'equity_curve': equity_curve, 'trades': trades, 'metrics': metrics, 'ma_data': ma_data}


def _backtest_mean_reversion(dates, closes, capital, lookback, z_entry, z_exit):
    """
    Mean reversion strategy:
    - Buy when price Z-score < z_entry (oversold)
    - Sell when price Z-score > z_exit (reverted)
    """
    cash = capital
    shares = 0
    in_position = False
    equity_curve = []
    trades = []

    rolling_mean = pd.Series(closes).rolling(window=lookback).mean().values
    rolling_std = pd.Series(closes).rolling(window=lookback).std().values

    for i, (d, p) in enumerate(zip(dates, closes)):
        if i < lookback or np.isnan(rolling_std[i]) or rolling_std[i] == 0:
            equity_curve.append({'date': d.isoformat(), 'equity': round(float(capital), 2)})
            continue

        z_score = (p - rolling_mean[i]) / rolling_std[i]

        if not in_position and z_score < z_entry:
            # Oversold - BUY
            shares = cash / p
            cash = 0
            in_position = True
            trades.append({'date': d.isoformat(), 'action': 'BUY', 'price': round(float(p), 2),
                           'shares': round(float(shares), 4), 'z_score': round(float(z_score), 2)})
        elif in_position and z_score > z_exit:
            # Reverted - SELL
            cash = shares * p
            shares = 0
            in_position = False
            trades.append({'date': d.isoformat(), 'action': 'SELL', 'price': round(float(p), 2),
                           'shares': 0, 'z_score': round(float(z_score), 2)})

        equity = cash + shares * p
        equity_curve.append({'date': d.isoformat(), 'equity': round(float(equity), 2)})

    metrics = _compute_metrics([e['equity'] for e in equity_curve], capital, trades)
    return {'equity_curve': equity_curve, 'trades': trades, 'metrics': metrics}


# ==================== HISTORICAL ANALYSIS ====================

@backtest_bp.route('/historical-analysis/<symbol>', methods=['GET'])
@require_auth
def historical_analysis(symbol):
    """
    Comprehensive historical analysis for a stock.

    Query params:
        days (int): Lookback period, default 365

    Returns:
        {
            "symbol": "AAPL",
            "drawdown_analysis": { "drawdowns": [...], "current_drawdown": ..., "max_drawdown": ... },
            "rolling_metrics": [{ "date": ..., "return_30d": ..., "volatility_30d": ..., "sharpe_30d": ... }],
            "return_distribution": { "histogram": [...], "stats": { "mean": ..., "std": ..., "skew": ..., "kurtosis": ... } },
            "period_returns": { "1w": ..., "1m": ..., "3m": ..., "6m": ..., "1y": ... },
            "best_worst_days": { "best": [...], "worst": [...] }
        }
    """
    try:
        symbol = symbol.upper()
        days = request.args.get('days', 365, type=int)

        with DatabaseService() as db:
            stock = db.db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                return jsonify({'error': f'Stock {symbol} not found'}), 404

            cutoff = datetime.now().date() - timedelta(days=days)
            records = db.db.query(MarketData).filter(
                MarketData.stock_id == stock.id,
                MarketData.date >= cutoff
            ).order_by(MarketData.date).all()

            if len(records) < 30:
                return jsonify({'error': 'Insufficient data'}), 404

            dates = [r.date for r in records]
            closes = np.array([float(r.close) for r in records if r.close])
            daily_returns = np.diff(closes) / closes[:-1]

            # === Drawdown Analysis ===
            peak = np.maximum.accumulate(closes)
            drawdown_pct = (closes - peak) / peak
            max_dd = float(np.min(drawdown_pct))

            # Find drawdown periods
            drawdown_series = []
            in_dd = False
            dd_start = None
            for i in range(len(drawdown_pct)):
                if drawdown_pct[i] < -0.01 and not in_dd:
                    in_dd = True
                    dd_start = i
                elif drawdown_pct[i] >= -0.001 and in_dd:
                    in_dd = False
                    dd_depth = float(np.min(drawdown_pct[dd_start:i + 1]))
                    trough_idx = dd_start + np.argmin(drawdown_pct[dd_start:i + 1])
                    drawdown_series.append({
                        'start': dates[dd_start].isoformat(),
                        'trough': dates[trough_idx].isoformat(),
                        'recovery': dates[i].isoformat(),
                        'depth': round(dd_depth, 4),
                        'duration_days': (dates[i] - dates[dd_start]).days,
                    })

            # Sort by depth, keep worst 10
            drawdown_series.sort(key=lambda x: x['depth'])
            top_drawdowns = drawdown_series[:10]

            # Drawdown curve for charting
            drawdown_curve = [
                {'date': dates[i].isoformat(), 'drawdown': round(float(drawdown_pct[i]) * 100, 2)}
                for i in range(len(dates))
            ]

            # === Rolling Metrics (30-day) ===
            window = 30
            rolling_metrics = []
            for i in range(window, len(closes)):
                period_returns = daily_returns[i - window:i]
                r_mean = float(np.mean(period_returns))
                r_std = float(np.std(period_returns))
                r_total = float((closes[i] / closes[i - window]) - 1)
                r_sharpe = (r_mean * 252) / (r_std * np.sqrt(252)) if r_std > 0 else 0

                rolling_metrics.append({
                    'date': dates[i].isoformat(),
                    'return_30d': round(r_total * 100, 2),
                    'volatility_30d': round(r_std * np.sqrt(252) * 100, 2),
                    'sharpe_30d': round(float(r_sharpe), 2),
                })

            # === Return Distribution ===
            hist_counts, bin_edges = np.histogram(daily_returns * 100, bins=40)
            histogram = []
            for j in range(len(hist_counts)):
                histogram.append({
                    'bin': round(float((bin_edges[j] + bin_edges[j + 1]) / 2), 3),
                    'count': int(hist_counts[j]),
                })

            dist_stats = {
                'mean': round(float(np.mean(daily_returns) * 100), 4),
                'std': round(float(np.std(daily_returns) * 100), 4),
                'skew': round(float(pd.Series(daily_returns).skew()), 4),
                'kurtosis': round(float(pd.Series(daily_returns).kurtosis()), 4),
                'min': round(float(np.min(daily_returns) * 100), 4),
                'max': round(float(np.max(daily_returns) * 100), 4),
                'positive_days': int(np.sum(daily_returns > 0)),
                'negative_days': int(np.sum(daily_returns < 0)),
                'total_days': len(daily_returns),
            }

            # === Period Returns ===
            period_returns_map = {}
            for label, pd_days in [('1w', 5), ('1m', 21), ('3m', 63), ('6m', 126), ('1y', 252)]:
                if len(closes) > pd_days:
                    ret = (closes[-1] / closes[-pd_days - 1]) - 1
                    period_returns_map[label] = round(float(ret), 4)
                else:
                    period_returns_map[label] = None

            # === Best / Worst Days ===
            indexed_returns = [(dates[i + 1].isoformat(), round(float(daily_returns[i] * 100), 2)) for i in range(len(daily_returns))]
            sorted_returns = sorted(indexed_returns, key=lambda x: x[1])
            worst_days = [{'date': d, 'return_pct': r} for d, r in sorted_returns[:5]]
            best_days = [{'date': d, 'return_pct': r} for d, r in sorted_returns[-5:][::-1]]

            return jsonify({
                'symbol': symbol,
                'data_points': len(closes),
                'date_range': {'start': dates[0].isoformat(), 'end': dates[-1].isoformat()},
                'drawdown_analysis': {
                    'max_drawdown': round(max_dd, 4),
                    'current_drawdown': round(float(drawdown_pct[-1]), 4),
                    'top_drawdowns': top_drawdowns,
                    'drawdown_curve': drawdown_curve,
                },
                'rolling_metrics': rolling_metrics,
                'return_distribution': {
                    'histogram': histogram,
                    'stats': dist_stats,
                },
                'period_returns': period_returns_map,
                'best_worst_days': {
                    'best': best_days,
                    'worst': worst_days,
                },
            }), 200

    except Exception as e:
        log.error(f"Error in historical analysis for {symbol}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
