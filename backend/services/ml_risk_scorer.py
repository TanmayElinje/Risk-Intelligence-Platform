"""
ML Risk Scorer — Replaces manual weighted formula with trained XGBoost model
backend/services/ml_risk_scorer.py

Uses the trained model from notebooks/01_risk_classification_model.ipynb
to compute risk scores based on 34 engineered features.
Falls back to manual formula if model files are missing.
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from backend.utils import log

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')


class MLRiskScorer:
    """Score stocks using the trained XGBoost volatility risk model."""

    def __init__(self):
        self.model = None
        self.feature_cols = None
        self.shap_explanations = None
        self.vol_forecasts = None
        self._load_artifacts()

    def _load_artifacts(self):
        """Load trained model, feature list, and SHAP explanations."""
        try:
            import joblib
            model_path = os.path.join(MODEL_DIR, 'risk_classifier.joblib')
            features_path = os.path.join(MODEL_DIR, 'feature_list.joblib')
            shap_path = os.path.join(MODEL_DIR, 'shap_explanations.json')
            vol_path = os.path.join(MODEL_DIR, 'vol_forecasts.json')

            if os.path.exists(model_path) and os.path.exists(features_path):
                self.model = joblib.load(model_path)
                self.feature_cols = joblib.load(features_path)
                log.info(f"ML Risk Model loaded: {len(self.feature_cols)} features")
            else:
                log.warning("ML model files not found — will use manual scoring")

            if os.path.exists(shap_path):
                with open(shap_path) as f:
                    self.shap_explanations = json.load(f)
                log.info(f"SHAP explanations loaded: {len(self.shap_explanations)} stocks")

            if os.path.exists(vol_path):
                with open(vol_path) as f:
                    self.vol_forecasts = json.load(f)
                log.info(f"Volatility forecasts loaded: {len(self.vol_forecasts)} stocks")

        except Exception as e:
            log.error(f"Error loading ML artifacts: {e}")
            self.model = None

    @property
    def is_ml_available(self):
        return self.model is not None and self.feature_cols is not None

    def compute_features(self, df, spy_returns=None):
        """
        Compute all 34 features for a single stock DataFrame.
        Input: df with columns [date, open, high, low, close, volume]
        """
        df = df.sort_values('date').copy()
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']

        # Daily returns
        df['daily_return'] = close.pct_change()

        # Volatility
        df['volatility_21d'] = df['daily_return'].rolling(21).std() * np.sqrt(252)
        df['volatility_63d'] = df['daily_return'].rolling(63).std() * np.sqrt(252)

        # Momentum
        df['return_5d'] = close.pct_change(5)
        df['return_10d'] = close.pct_change(10)
        df['return_21d'] = close.pct_change(21)
        df['return_63d'] = close.pct_change(63)

        # RSI
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-10)
        df['rsi_14'] = 100 - (100 / (1 + rs))

        # MACD
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        df['macd_line'] = ema_12 - ema_26
        df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd_line'] - df['macd_signal']

        # Bollinger Bands
        sma_20 = close.rolling(20).mean()
        std_20 = close.rolling(20).std()
        bb_upper = sma_20 + 2 * std_20
        bb_lower = sma_20 - 2 * std_20
        df['bb_width'] = (bb_upper - bb_lower) / (sma_20 + 1e-10)
        df['bb_position'] = (close - bb_lower) / (bb_upper - bb_lower + 1e-10)

        # Volume ratio
        df['volume_ratio'] = volume / (volume.rolling(50).mean() + 1e-10)

        # Max drawdown (trailing 63d)
        rolling_max = close.rolling(63, min_periods=1).max()
        drawdown = (close - rolling_max) / (rolling_max + 1e-10)
        df['max_drawdown_63d'] = drawdown.rolling(63, min_periods=1).min()

        # Beta vs SPY
        if spy_returns is not None:
            df = df.merge(spy_returns[['date', 'spy_return']], on='date', how='left')
            cov = df['daily_return'].rolling(63).cov(df['spy_return'])
            var = df['spy_return'].rolling(63).var()
            df['beta_63d'] = cov / (var + 1e-10)
        else:
            df['beta_63d'] = 1.0

        # Distance from 52w high/low
        high_252 = high.rolling(252, min_periods=63).max()
        low_252 = low.rolling(252, min_periods=63).min()
        df['dist_from_52w_high'] = (close - high_252) / (high_252 + 1e-10)
        df['dist_from_52w_low'] = (close - low_252) / (low_252 + 1e-10)

        # ATR
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
        df['beta_vol_interaction'] = df['beta_63d'] * df['volatility_21d']

        return df

    def score_stocks_from_shap(self):
        """
        Use pre-computed SHAP explanation scores as risk scores.
        These were computed with the full 5yr training pipeline,
        so they are more calibrated than live predictions on 2yr data.
        """
        if not self.shap_explanations:
            return pd.DataFrame()
        
        results = []
        for symbol, exp in self.shap_explanations.items():
            prob = exp['risk_probability']
            level = 'High' if prob > 0.6 else 'Medium' if prob > 0.3 else 'Low'
            drivers = f"↑ {exp['risk_drivers_up']} | ↓ {exp['risk_drivers_down']}"
            
            vol_forecast = None
            vol_signal = None
            if self.vol_forecasts and symbol in self.vol_forecasts:
                vf = self.vol_forecasts[symbol]
                vol_forecast = vf.get('garch_forecast_30d')
                vol_signal = vf.get('signal')
            
            results.append({
                'symbol': symbol,
                'risk_score': prob,
                'risk_level': level,
                'risk_drivers': drivers,
                'volatility_21d': None,
                'max_drawdown': None,
                'liquidity_risk': None,
                'vol_forecast': vol_forecast,
                'vol_signal': vol_signal,
            })
        
        result_df = pd.DataFrame(results)
        result_df['risk_rank'] = result_df['risk_score'].rank(ascending=False, method='min').astype(int)
        result_df = result_df.sort_values('risk_rank')
        
        log.info(f"SHAP-based scoring: {len(result_df)} stocks — "
                 f"High: {(result_df['risk_level']=='High').sum()}, "
                 f"Medium: {(result_df['risk_level']=='Medium').sum()}, "
                 f"Low: {(result_df['risk_level']=='Low').sum()}")
        
        return result_df

    def score_stocks(self, market_data_df, spy_df=None):
        """
        Score all stocks using the ML model.

        Args:
            market_data_df: DataFrame with columns [symbol, date, open, high, low, close, volume]
            spy_df: Optional SPY data for beta calculation

        Returns:
            DataFrame with [symbol, risk_score, risk_level, risk_rank, risk_drivers, ...]
        """
        if not self.is_ml_available:
            log.warning("ML model not available, returning empty")
            return pd.DataFrame()

        # Prepare SPY returns
        spy_returns = None
        if spy_df is not None and not spy_df.empty:
            spy_returns = spy_df[['date', 'close']].copy()
            spy_returns['spy_return'] = spy_returns['close'].pct_change()

        symbols = market_data_df['symbol'].unique()
        all_featured = []

        for symbol in symbols:
            sdf = market_data_df[market_data_df['symbol'] == symbol].copy()
            if len(sdf) < 100:
                continue
            sdf = self.compute_features(sdf, spy_returns)
            sdf['symbol_col'] = symbol
            all_featured.append(sdf)

        if not all_featured:
            return pd.DataFrame()

        featured = pd.concat(all_featured, ignore_index=True)

        # Cross-sectional ranks
        for feat in ['volatility_21d', 'return_21d', 'beta_63d', 'volume_ratio']:
            col = f'{feat}_rank'
            if feat in featured.columns:
                featured[col] = featured.groupby('date')[feat].rank(pct=True)

        # Market regime (use SPY volatility)
        if spy_returns is not None:
            spy_vol = spy_returns.copy()
            spy_vol['spy_vol_21d'] = spy_vol['spy_return'].rolling(21).std() * np.sqrt(252)
            spy_vol['spy_return_21d'] = spy_vol['close'].pct_change(21)
            spy_vol['high_vol_regime'] = (spy_vol['spy_vol_21d'] > spy_vol['spy_vol_21d'].rolling(252).quantile(0.75)).astype(int)
            featured = featured.merge(spy_vol[['date', 'spy_vol_21d', 'spy_return_21d', 'high_vol_regime']], on='date', how='left')
        else:
            featured['spy_vol_21d'] = 0.15
            featured['spy_return_21d'] = 0.0
            featured['high_vol_regime'] = 0

        # Get latest features per stock
        latest = featured.sort_values('date').groupby('symbol_col').last()

        # Check which features are available
        available_features = [f for f in self.feature_cols if f in latest.columns]
        missing_features = [f for f in self.feature_cols if f not in latest.columns]

        if missing_features:
            log.warning(f"Missing features: {missing_features}")
            for f in missing_features:
                latest[f] = 0.0

        # Fill NaN
        X = latest[self.feature_cols].fillna(0)

        # Predict
        risk_probs = self.model.predict_proba(X)[:, 1]

        # Build result
        results = []
        for i, symbol in enumerate(latest.index):
            prob = float(risk_probs[i])
            level = 'High' if prob > 0.6 else 'Medium' if prob > 0.3 else 'Low'

            # Get SHAP explanation if available
            drivers = "ML model prediction"
            if self.shap_explanations and symbol in self.shap_explanations:
                exp = self.shap_explanations[symbol]
                drivers = f"↑ {exp['risk_drivers_up']} | ↓ {exp['risk_drivers_down']}"

            # Get volatility forecast if available
            vol_forecast = None
            vol_signal = None
            if self.vol_forecasts and symbol in self.vol_forecasts:
                vf = self.vol_forecasts[symbol]
                vol_forecast = vf.get('garch_forecast_30d')
                vol_signal = vf.get('signal')

            row_data = latest.loc[symbol]
            results.append({
                'symbol': symbol,
                'risk_score': prob,
                'risk_level': level,
                'risk_drivers': drivers,
                'volatility_21d': float(row_data.get('volatility_21d', 0)) if pd.notna(row_data.get('volatility_21d')) else None,
                'max_drawdown': float(row_data.get('max_drawdown_63d', 0)) if pd.notna(row_data.get('max_drawdown_63d')) else None,
                'liquidity_risk': float(row_data.get('volume_ratio', 1)) if pd.notna(row_data.get('volume_ratio')) else None,
                'vol_forecast': vol_forecast,
                'vol_signal': vol_signal,
            })

        result_df = pd.DataFrame(results)
        result_df['risk_rank'] = result_df['risk_score'].rank(ascending=False, method='min').astype(int)
        result_df = result_df.sort_values('risk_rank')

        log.info(f"ML scored {len(result_df)} stocks — High: {(result_df['risk_level']=='High').sum()}, "
                 f"Medium: {(result_df['risk_level']=='Medium').sum()}, Low: {(result_df['risk_level']=='Low').sum()}")

        return result_df

    def get_stock_explanation(self, symbol):
        """Get SHAP-based explanation for a specific stock."""
        if self.shap_explanations and symbol in self.shap_explanations:
            return self.shap_explanations[symbol]
        return None

    def get_vol_forecast(self, symbol):
        """Get volatility forecast for a specific stock."""
        if self.vol_forecasts and symbol in self.vol_forecasts:
            return self.vol_forecasts[symbol]
        return None