"""
Risk Scoring Agent - Combines all signals into composite risk score
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta
from backend.utils import log, load_config, load_dataframe, save_dataframe, ensure_dir, normalize_score

class RiskScoringAgent:
    """
    Agent responsible for computing composite risk scores
    """
    
    def __init__(self):
        """Initialize Risk Scoring Agent"""
        self.config = load_config()
        self.agent_config = self.config['agents']['risk_scoring']
        self.weights = self.agent_config['weights']
        self.thresholds = self.agent_config['thresholds']
        
        log.info("Risk Scoring Agent initialized")
        log.info(f"Weights: {self.weights}")
        log.info(f"Thresholds: {self.thresholds}")
    
    def load_market_features(self) -> pd.DataFrame:
        """
        Load market features
        
        Returns:
            DataFrame with market features
        """
        log.info("Loading market features...")
        
        features_path = f"{self.config['paths']['features']}/market_features.parquet"
        
        try:
            features_df = load_dataframe(features_path, format='parquet')
            log.info(f"Loaded {len(features_df)} rows of market features")
            return features_df
        except FileNotFoundError:
            log.error("Market features not found")
            raise
    
    def load_sentiment_scores(self) -> pd.DataFrame:
        """
        Load sentiment scores
        
        Returns:
            DataFrame with sentiment scores
        """
        log.info("Loading sentiment scores...")
        
        sentiment_path = f"{self.config['paths']['data_processed']}/sentiment_scores.csv"
        
        try:
            sentiment_df = load_dataframe(sentiment_path, format='csv')
            log.info(f"Loaded {len(sentiment_df)} rows of sentiment scores")
            return sentiment_df
        except FileNotFoundError:
            log.warning("Sentiment scores not found, will use default values")
            return pd.DataFrame()
    
    def prepare_latest_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Get latest feature values per stock
        
        Args:
            features_df: DataFrame with all features
            
        Returns:
            DataFrame with latest values per stock
        """
        log.info("Extracting latest feature values...")
        
        # Sort by date and get latest for each stock
        features_df = features_df.sort_values(['symbol', 'Date'])
        latest_features = features_df.groupby('symbol').tail(1).copy()
        
        # Select relevant columns
        feature_cols = [
            'symbol', 'Date', 'Close',
            'volatility_21d', 'volatility_60d',
            'max_drawdown', 'beta', 'sharpe_ratio',
            'atr_pct', 'liquidity_risk'
        ]
        
        # Keep only existing columns
        available_cols = [col for col in feature_cols if col in latest_features.columns]
        latest_features = latest_features[available_cols].copy()
        
        log.info(f"✓ Extracted latest features for {len(latest_features)} stocks")
        return latest_features
    
    def merge_sentiment(
        self,
        features_df: pd.DataFrame,
        sentiment_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Merge sentiment scores with features
        
        Args:
            features_df: DataFrame with market features
            sentiment_df: DataFrame with sentiment scores
            
        Returns:
            Merged DataFrame
        """
        if sentiment_df.empty:
            log.warning("No sentiment data, using neutral sentiment")
            features_df['avg_sentiment'] = 0.0
            features_df['sentiment_std'] = 0.0
            features_df['article_count'] = 0
            return features_df
        
        log.info("Merging sentiment scores...")
        
        # Get recent sentiment (last 7 days average)
        sentiment_df['date'] = pd.to_datetime(sentiment_df['date'])
        recent_date = sentiment_df['date'].max()
        lookback_date = recent_date - timedelta(days=7)
        
        recent_sentiment = sentiment_df[sentiment_df['date'] >= lookback_date].copy()
        
        # Aggregate by stock
        sentiment_agg = recent_sentiment.groupby('stock_symbol').agg({
            'avg_sentiment': 'mean',
            'sentiment_std': 'mean',
            'article_count': 'sum'
        }).reset_index()
        
        # Rename for merge
        sentiment_agg = sentiment_agg.rename(columns={'stock_symbol': 'symbol'})
        
        # Merge
        merged_df = features_df.merge(
            sentiment_agg,
            on='symbol',
            how='left'
        )
        
        # Fill missing sentiment with neutral
        merged_df['avg_sentiment'] = merged_df['avg_sentiment'].fillna(0.0)
        merged_df['sentiment_std'] = merged_df['sentiment_std'].fillna(0.0)
        merged_df['article_count'] = merged_df['article_count'].fillna(0)
        
        log.info(f"✓ Merged sentiment for {len(merged_df)} stocks")
        return merged_df
    
    def normalize_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize all features to 0-1 scale
        
        Args:
            df: DataFrame with raw features
            
        Returns:
            DataFrame with normalized features
        """
        log.info("Normalizing features...")
        
        df = df.copy()
        
        # Volatility (higher = more risk)
        if 'volatility_21d' in df.columns:
            df['norm_volatility'] = df['volatility_21d'] / df['volatility_21d'].max()
        else:
            df['norm_volatility'] = 0.5
        
        # Drawdown (higher = more risk)
        if 'max_drawdown' in df.columns:
            df['norm_drawdown'] = df['max_drawdown'] / 100  # Already in percentage
            df['norm_drawdown'] = df['norm_drawdown'].clip(0, 1)
        else:
            df['norm_drawdown'] = 0.5
        
        # Sentiment (more negative = more risk)
        # Convert from [-1, 1] to [1, 0] where 1 = high risk (negative sentiment)
        if 'avg_sentiment' in df.columns:
            df['norm_sentiment'] = (1 - df['avg_sentiment']) / 2
            df['norm_sentiment'] = df['norm_sentiment'].clip(0, 1)
        else:
            df['norm_sentiment'] = 0.5
        
        # Liquidity risk (higher = more risk)
        if 'liquidity_risk' in df.columns:
            max_liq = df['liquidity_risk'].quantile(0.95)  # Use 95th percentile to avoid outliers
            df['norm_liquidity'] = (df['liquidity_risk'] / max_liq).clip(0, 1)
        else:
            df['norm_liquidity'] = 0.5
        
        log.info("✓ Features normalized")
        return df
    
    def compute_risk_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute composite risk scores using weighted formula
        
        Args:
            df: DataFrame with normalized features
            
        Returns:
            DataFrame with risk scores
        """
        log.info("Computing composite risk scores...")
        
        df = df.copy()
        
        # Apply weighted formula
        df['risk_score'] = (
            self.weights['volatility'] * df['norm_volatility'] +
            self.weights['drawdown'] * df['norm_drawdown'] +
            self.weights['sentiment'] * df['norm_sentiment'] +
            self.weights['liquidity'] * df['norm_liquidity']
        )
        
        # Ensure risk_score is between 0 and 1
        df['risk_score'] = df['risk_score'].clip(0, 1)
        
        log.info("✓ Risk scores computed")
        return df
    
    def classify_risk_levels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Classify stocks into risk levels
        
        Args:
            df: DataFrame with risk scores
            
        Returns:
            DataFrame with risk classifications
        """
        log.info("Classifying risk levels...")
        
        df = df.copy()
        
        # Apply thresholds
        def classify(score):
            if score < self.thresholds['low']:
                return 'Low'
            elif score < self.thresholds['medium']:
                return 'Medium'
            else:
                return 'High'
        
        df['risk_level'] = df['risk_score'].apply(classify)
        
        # Count by level
        risk_counts = df['risk_level'].value_counts()
        log.info(f"✓ Risk classification complete:")
        log.info(f"  Low: {risk_counts.get('Low', 0)}")
        log.info(f"  Medium: {risk_counts.get('Medium', 0)}")
        log.info(f"  High: {risk_counts.get('High', 0)}")
        
        return df
    
    def add_risk_insights(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add human-readable insights about risk drivers
        
        Args:
            df: DataFrame with risk scores
            
        Returns:
            DataFrame with insights
        """
        log.info("Adding risk insights...")
        
        df = df.copy()
        
        def generate_insight(row):
            insights = []
            
            # Check each component
            if row['norm_volatility'] > 0.7:
                insights.append("High volatility")
            
            if row['norm_drawdown'] > 0.7:
                insights.append("Significant drawdown")
            
            if row['norm_sentiment'] > 0.6:
                insights.append("Negative news sentiment")
            
            if row['norm_liquidity'] > 0.7:
                insights.append("Liquidity concerns")
            
            if not insights:
                insights.append("Stable conditions")
            
            return " | ".join(insights)
        
        df['risk_drivers'] = df.apply(generate_insight, axis=1)
        
        log.info("✓ Risk insights added")
        return df
    
    def rank_stocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rank stocks by risk score
        
        Args:
            df: DataFrame with risk scores
            
        Returns:
            DataFrame with rankings
        """
        log.info("Ranking stocks by risk...")
        
        df = df.copy()
        
        # Add rank (1 = highest risk)
        df['risk_rank'] = df['risk_score'].rank(ascending=False, method='min').astype(int)
        
        # Sort by rank
        df = df.sort_values('risk_rank')
        
        log.info("✓ Stocks ranked")
        return df
    
    def save_risk_scores(self, df: pd.DataFrame, filename: str = "risk_scores.csv"):
        """
        Save risk scores to file
        
        Args:
            df: DataFrame with risk scores
            filename: Output filename
        """
        ensure_dir(self.config['paths']['data_processed'])
        filepath = f"{self.config['paths']['data_processed']}/{filename}"
        
        # Select columns for output
        output_cols = [
            'symbol', 'Date', 'Close',
            'risk_score', 'risk_level', 'risk_rank', 'risk_drivers',
            'norm_volatility', 'norm_drawdown', 'norm_sentiment', 'norm_liquidity',
            'volatility_21d', 'max_drawdown', 'avg_sentiment', 'liquidity_risk',
            'article_count'
        ]
        
        # Keep only existing columns
        available_cols = [col for col in output_cols if col in df.columns]
        output_df = df[available_cols].copy()
        
        save_dataframe(output_df, filepath, format='csv')
        log.info(f"✓ Saved risk scores to {filepath}")
    
    def run(self) -> pd.DataFrame:
        """
        Run the complete risk scoring pipeline
        
        Returns:
            DataFrame with risk scores
        """
        log.info("=" * 60)
        log.info("STARTING RISK SCORING AGENT")
        log.info("=" * 60)
        
        # Load data
        features_df = self.load_market_features()
        sentiment_df = self.load_sentiment_scores()
        
        # Get latest features
        latest_features = self.prepare_latest_features(features_df)
        
        # Merge sentiment
        combined_df = self.merge_sentiment(latest_features, sentiment_df)
        
        # Normalize features
        normalized_df = self.normalize_features(combined_df)
        
        # Compute risk scores
        risk_df = self.compute_risk_scores(normalized_df)
        
        # Classify risk levels
        risk_df = self.classify_risk_levels(risk_df)
        
        # Add insights
        risk_df = self.add_risk_insights(risk_df)
        
        # Rank stocks
        risk_df = self.rank_stocks(risk_df)
        
        # Save results
        self.save_risk_scores(risk_df)
        
        log.info("=" * 60)
        log.info("✓ RISK SCORING AGENT COMPLETED")
        log.info("=" * 60)
        
        return risk_df