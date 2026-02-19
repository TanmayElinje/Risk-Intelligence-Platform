"""
ML Model Retrain Script
backend/scripts/retrain_ml_model.py

Retrains the XGBoost risk classifier, recomputes SHAP explanations,
and regenerates volatility forecasts. Same pipeline as the notebooks
but automated for periodic retraining.

Usage:
    python -m backend.scripts.retrain_ml_model

Run weekly or monthly to keep scores calibrated to current market conditions.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import joblib
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

# Add project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
os.makedirs(MODEL_DIR, exist_ok=True)


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


# ============================================================
# STEP 1: Download data
# ============================================================
def download_data(symbols):
    import yfinance as yf
    
    log(f"Downloading 5yr data for {len(symbols)} stocks + SPY...")
    all_tickers = symbols + ['SPY']
    raw = yf.download(all_tickers, period='5y', interval='1d', group_by='ticker', auto_adjust=True)
    
    stock_records = []
    spy_records = []
    for symbol in all_tickers:
        try:
            df = raw[symbol].dropna(subset=['Close']).reset_index()
            df['symbol'] = symbol
            df.columns = [c.lower() if c != 'symbol' else c for c in df.columns]
            row = df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]
            if symbol == 'SPY':
                spy_records.append(row)
            else:
                stock_records.append(row)
        except:
            pass
    
    stock_data = pd.concat(stock_records, ignore_index=True)
    stock_data['date'] = pd.to_datetime(stock_data['date'])
    stock_data = stock_data.sort_values(['symbol', 'date']).reset_index(drop=True)
    
    spy_data = pd.concat(spy_records, ignore_index=True)
    spy_data['date'] = pd.to_datetime(spy_data['date'])
    spy_data['spy_return'] = spy_data['close'].pct_change()
    
    log(f"Downloaded {len(stock_data):,} stock rows, {stock_data.symbol.nunique()} stocks")
    return stock_data, spy_data


# ============================================================
# STEP 2: Feature engineering (34 features)
# ============================================================
def compute_features(df):
    df = df.sort_values('date').copy()
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    
    df['daily_return'] = close.pct_change()
    df['volatility_21d'] = df['daily_return'].rolling(21).std() * np.sqrt(252)
    df['volatility_63d'] = df['daily_return'].rolling(63).std() * np.sqrt(252)
    df['return_5d'] = close.pct_change(5)
    df['return_10d'] = close.pct_change(10)
    df['return_21d'] = close.pct_change(21)
    df['return_63d'] = close.pct_change(63)
    
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-10)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    df['macd_line'] = ema_12 - ema_26
    df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
    df['macd_histogram'] = df['macd_line'] - df['macd_signal']
    
    sma_20 = close.rolling(20).mean()
    std_20 = close.rolling(20).std()
    bb_upper = sma_20 + 2 * std_20
    bb_lower = sma_20 - 2 * std_20
    df['bb_width'] = (bb_upper - bb_lower) / (sma_20 + 1e-10)
    df['bb_position'] = (close - bb_lower) / (bb_upper - bb_lower + 1e-10)
    
    df['volume_ratio'] = volume / (volume.rolling(50).mean() + 1e-10)
    
    rolling_max = close.rolling(63, min_periods=1).max()
    drawdown = (close - rolling_max) / (rolling_max + 1e-10)
    df['max_drawdown_63d'] = drawdown.rolling(63, min_periods=1).min()
    
    high_252 = high.rolling(252, min_periods=63).max()
    low_252 = low.rolling(252, min_periods=63).min()
    df['dist_from_52w_high'] = (close - high_252) / (high_252 + 1e-10)
    df['dist_from_52w_low'] = (close - low_252) / (low_252 + 1e-10)
    
    tr = pd.DataFrame({
        'hl': high - low,
        'hc': abs(high - close.shift(1)),
        'lc': abs(low - close.shift(1))
    }).max(axis=1)
    df['atr_14'] = tr.rolling(14).mean() / (close + 1e-10)
    
    # v2 features
    df['vol_change'] = df['volatility_21d'] - df['volatility_63d']
    df['momentum_reversal'] = df['return_5d'] - df['return_21d']
    df['return_vol_adj'] = df['return_21d'] / (df['volatility_21d'] + 1e-10)
    df['rsi_overbought'] = (df['rsi_14'] > 70).astype(int)
    df['rsi_oversold'] = (df['rsi_14'] < 30).astype(int)
    df['down_day'] = (df['daily_return'] < 0).astype(int)
    df['down_volume_ratio'] = (df['down_day'] * df['volume']).rolling(21).sum() / (df['volume'].rolling(21).sum() + 1e-10)
    sma_10 = close.rolling(10).mean()
    sma_50 = close.rolling(50).mean()
    df['sma_cross'] = (sma_10 - sma_50) / (sma_50 + 1e-10)
    df['consec_down'] = df['daily_return'].lt(0).rolling(10).sum()
    df['beta_vol_interaction'] = df.get('beta_63d', 1.0) * df['volatility_21d']
    
    return df


def engineer_all_features(stock_data, spy_data):
    log("Computing features for all stocks...")
    
    feature_cols = [
        'volatility_21d', 'volatility_63d', 'return_5d', 'return_10d',
        'return_21d', 'return_63d', 'rsi_14', 'macd_line', 'macd_signal',
        'macd_histogram', 'bb_width', 'bb_position', 'volume_ratio',
        'max_drawdown_63d', 'beta_63d', 'dist_from_52w_high', 'dist_from_52w_low',
        'atr_14', 'vol_change', 'momentum_reversal', 'return_vol_adj',
        'rsi_overbought', 'rsi_oversold', 'down_volume_ratio', 'sma_cross',
        'consec_down', 'beta_vol_interaction',
        'volatility_21d_rank', 'return_21d_rank', 'beta_63d_rank', 'volume_ratio_rank',
        'spy_vol_21d', 'spy_return_21d', 'high_vol_regime'
    ]
    
    # Merge SPY returns
    stock_data = stock_data.merge(spy_data[['date', 'spy_return']], on='date', how='left')
    
    all_dfs = []
    for symbol in stock_data['symbol'].unique():
        sdf = stock_data[stock_data['symbol'] == symbol].copy()
        sdf = compute_features(sdf)
        
        # Beta
        cov = sdf['daily_return'].rolling(63).cov(sdf['spy_return'])
        var = sdf['spy_return'].rolling(63).var()
        sdf['beta_63d'] = cov / (var + 1e-10)
        sdf['beta_vol_interaction'] = sdf['beta_63d'] * sdf['volatility_21d']
        
        all_dfs.append(sdf)
    
    featured = pd.concat(all_dfs, ignore_index=True)
    
    # Cross-sectional ranks
    for feat in ['volatility_21d', 'return_21d', 'beta_63d', 'volume_ratio']:
        featured[f'{feat}_rank'] = featured.groupby('date')[feat].rank(pct=True)
    
    # Market regime
    spy_vol = spy_data.copy()
    spy_vol['spy_vol_21d'] = spy_vol['close'].pct_change().rolling(21).std() * np.sqrt(252)
    spy_vol['spy_return_21d'] = spy_vol['close'].pct_change(21)
    spy_vol['high_vol_regime'] = (spy_vol['spy_vol_21d'] > spy_vol['spy_vol_21d'].rolling(252).quantile(0.75)).astype(int)
    
    featured = featured.merge(
        spy_vol[['date', 'spy_vol_21d', 'spy_return_21d', 'high_vol_regime']],
        on='date', how='left'
    )
    
    featured = featured.dropna(subset=feature_cols)
    log(f"Features computed: {len(featured):,} rows, {featured.symbol.nunique()} stocks, {len(feature_cols)} features")
    
    return featured, feature_cols


# ============================================================
# STEP 3: Create target + train/test split
# ============================================================
def create_target(featured, feature_cols):
    log("Creating volatility target...")
    
    # Forward 21-day realized vol
    def add_forward_vol(g):
        g = g.sort_values('date')
        log_ret = np.log(g['close'] / g['close'].shift(1))
        fwd_vol = log_ret.rolling(21).std().shift(-21) * np.sqrt(252)
        g['forward_vol_21d'] = fwd_vol
        return g
    
    featured = featured.groupby('symbol', group_keys=False).apply(add_forward_vol)
    featured = featured.dropna(subset=['forward_vol_21d'] + feature_cols)
    
    # Top 30% = high volatility
    threshold = featured.groupby('date')['forward_vol_21d'].transform(lambda x: x.quantile(0.70))
    featured['target'] = (featured['forward_vol_21d'] >= threshold).astype(int)
    
    # Time-series split
    split_date = featured['date'].quantile(0.78)  # ~78% train
    train = featured[featured['date'] <= split_date]
    test = featured[featured['date'] > split_date]
    
    X_train = train[feature_cols]
    y_train = train['target']
    X_test = test[feature_cols]
    y_test = test['target']
    
    log(f"Train: {len(train):,} ({y_train.mean():.1%} positive) | Test: {len(test):,} ({y_test.mean():.1%} positive)")
    log(f"Train: {train['date'].min().date()} to {train['date'].max().date()}")
    log(f"Test:  {test['date'].min().date()} to {test['date'].max().date()}")
    
    return X_train, y_train, X_test, y_test, featured


# ============================================================
# STEP 4: Train XGBoost
# ============================================================
def train_model(X_train, y_train, X_test, y_test):
    from xgboost import XGBClassifier
    from sklearn.metrics import roc_auc_score, f1_score, classification_report
    from sklearn.model_selection import TimeSeriesSplit, cross_val_score
    
    log("Training XGBoost...")
    
    pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    
    model = XGBClassifier(
        n_estimators=500, max_depth=5, learning_rate=0.03,
        scale_pos_weight=pos_weight,
        min_child_weight=20, subsample=0.7, colsample_bytree=0.6,
        gamma=1, reg_alpha=0.5, reg_lambda=1.5,
        random_state=42, eval_metric='auc', verbosity=0
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_pred_proba)
    f1 = f1_score(y_test, (y_pred_proba > 0.5).astype(int))
    
    log(f"Test AUC-ROC: {auc:.4f}")
    log(f"Test F1:      {f1:.4f}")
    
    # Cross-validation
    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = cross_val_score(model, X_train, y_train, cv=tscv, scoring='roc_auc')
    log(f"CV AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    
    print(classification_report(y_test, (y_pred_proba > 0.5).astype(int), target_names=['Normal', 'High Vol']))
    
    return model, auc, f1, cv_scores


# ============================================================
# STEP 5: SHAP explanations
# ============================================================
def compute_shap(model, featured, feature_cols):
    import shap
    
    log("Computing SHAP explanations...")
    
    explainer = shap.TreeExplainer(model)
    
    # Latest features per stock
    latest = featured.sort_values('date').groupby('symbol').last()[feature_cols]
    shap_values = explainer.shap_values(latest)
    risk_probs = model.predict_proba(latest)[:, 1]
    
    explanations = {}
    for i, symbol in enumerate(latest.index):
        prob = float(risk_probs[i])
        sv = shap_values[i]
        
        feat_shap = sorted(zip(feature_cols, sv), key=lambda x: x[1], reverse=True)
        top_up = [(f, v) for f, v in feat_shap if v > 0][:3]
        top_down = [(f, v) for f, v in feat_shap if v < 0][-3:]
        
        explanations[symbol] = {
            'risk_probability': prob,
            'risk_level': 'High' if prob > 0.6 else 'Medium' if prob > 0.3 else 'Low',
            'shap_base': float(explainer.expected_value),
            'risk_drivers_up': ', '.join([f'{f} (+{v:.3f})' for f, v in top_up]) if top_up else 'none',
            'risk_drivers_down': ', '.join([f'{f} ({v:.3f})' for f, v in top_down]) if top_down else 'none',
            'top_features': {f: float(v) for f, v in feat_shap[:5]},
        }
    
    log(f"SHAP computed for {len(explanations)} stocks")
    return explanations, explainer


# ============================================================
# STEP 6: Volatility forecasts (GARCH)
# ============================================================
def compute_vol_forecasts(stock_data):
    from arch import arch_model
    
    log("Computing GARCH volatility forecasts...")
    
    forecasts = {}
    for symbol in stock_data['symbol'].unique():
        try:
            sdf = stock_data[stock_data['symbol'] == symbol].sort_values('date')
            log_ret = np.log(sdf['close'] / sdf['close'].shift(1)).dropna()
            
            current_vol = log_ret.rolling(21).std().iloc[-1] * np.sqrt(252)
            
            scaled = log_ret * 100
            am = arch_model(scaled, vol='Garch', p=1, q=1, dist='normal', rescale=False)
            res = am.fit(disp='off', show_warning=False)
            fc = res.forecast(horizon=30)
            avg_var = fc.variance.values[-1].mean()
            garch_vol = np.sqrt(avg_var) / 100 * np.sqrt(252)
            
            change = garch_vol - current_vol
            signal = '↑ INCREASING' if change > 0.02 else '↓ DECREASING' if change < -0.02 else '→ STABLE'
            
            forecasts[symbol] = {
                'current_vol': float(current_vol),
                'garch_forecast_30d': float(garch_vol),
                'vol_change': float(change),
                'signal': signal,
            }
        except:
            pass
    
    log(f"GARCH forecasts for {len(forecasts)} stocks")
    return forecasts


# ============================================================
# STEP 7: Save all artifacts
# ============================================================
def save_artifacts(model, feature_cols, explanations, forecasts, auc, f1, cv_scores, X_train, X_test):
    log("Saving model artifacts...")
    
    joblib.dump(model, os.path.join(MODEL_DIR, 'risk_classifier.joblib'))
    joblib.dump(feature_cols, os.path.join(MODEL_DIR, 'feature_list.joblib'))
    
    with open(os.path.join(MODEL_DIR, 'shap_explanations.json'), 'w') as f:
        json.dump(explanations, f, indent=2)
    
    with open(os.path.join(MODEL_DIR, 'vol_forecasts.json'), 'w') as f:
        json.dump(forecasts, f, indent=2)
    
    metadata = {
        'model_name': 'XGBoost Risk Classifier',
        'target': 'high_vol_regime (top 30% forward 21d vol)',
        'n_features': len(feature_cols),
        'features': feature_cols,
        'auc_roc': float(auc),
        'f1': float(f1),
        'cv_auc_mean': float(cv_scores.mean()),
        'cv_auc_std': float(cv_scores.std()),
        'train_samples': int(len(X_train)),
        'test_samples': int(len(X_test)),
        'train_date_range': [str(X_train.index[0]), str(X_train.index[-1])],
        'test_date_range': [str(X_test.index[0]), str(X_test.index[-1])],
        'retrained_at': datetime.now().isoformat(),
    }
    
    with open(os.path.join(MODEL_DIR, 'model_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    log(f"✓ All artifacts saved to {MODEL_DIR}")
    
    # Print summary
    sorted_stocks = sorted(explanations.items(), key=lambda x: x[1]['risk_probability'], reverse=True)
    high = sum(1 for _, v in sorted_stocks if v['risk_level'] == 'High')
    med = sum(1 for _, v in sorted_stocks if v['risk_level'] == 'Medium')
    low = sum(1 for _, v in sorted_stocks if v['risk_level'] == 'Low')
    
    print(f"\n{'='*60}")
    print(f"  RETRAIN COMPLETE")
    print(f"{'='*60}")
    print(f"  AUC-ROC:    {auc:.4f}")
    print(f"  CV AUC:     {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"  F1:         {f1:.4f}")
    print(f"  High Risk:  {high}")
    print(f"  Medium:     {med}")
    print(f"  Low Risk:   {low}")
    print(f"{'='*60}")
    print(f"  Top 5 Riskiest:")
    for sym, exp in sorted_stocks[:5]:
        print(f"    {sym:6s} {exp['risk_probability']:.3f} ({exp['risk_level']})")
    print(f"{'='*60}")


# ============================================================
# MAIN
# ============================================================
def main():
    from backend.utils import load_config
    config = load_config()
    symbols = config['stocks']['symbols']
    
    print(f"\n{'='*60}")
    print(f"  ML MODEL RETRAIN PIPELINE")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 1. Download
    stock_data, spy_data = download_data(symbols)
    
    # 2. Features
    featured, feature_cols = engineer_all_features(stock_data, spy_data)
    
    # 3. Target + split
    X_train, y_train, X_test, y_test, featured = create_target(featured, feature_cols)
    
    # 4. Train
    model, auc, f1, cv_scores = train_model(X_train, y_train, X_test, y_test)
    
    # 5. SHAP
    explanations, _ = compute_shap(model, featured, feature_cols)
    
    # 6. GARCH
    forecasts = compute_vol_forecasts(stock_data)
    
    # 7. Save
    save_artifacts(model, feature_cols, explanations, forecasts, auc, f1, cv_scores, X_train, X_test)


if __name__ == '__main__':
    main()