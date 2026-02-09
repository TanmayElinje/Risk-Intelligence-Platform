"""
Alert Agent - Generates automated risk alerts with explanations
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
from backend.utils import log, load_config, load_dataframe, save_dataframe, ensure_dir
from backend.agents.rag_agent import NewsRAGAgent

class AlertAgent:
    """
    Agent responsible for generating risk alerts
    """
    
    def __init__(self):
        """Initialize Alert Agent"""
        self.config = load_config()
        self.agent_config = self.config['agents']['alert']
        self.triggers = self.agent_config['triggers']
        self.notification_config = self.agent_config['notification']
        
        # Initialize RAG agent for explanations
        self.rag_agent = None
        
        log.info("Alert Agent initialized")
        log.info(f"Alert triggers: {self.triggers}")
    
    def load_risk_scores(self) -> pd.DataFrame:
        """
        Load latest risk scores
        
        Returns:
            DataFrame with risk scores
        """
        log.info("Loading risk scores...")
        
        risk_path = f"{self.config['paths']['data_processed']}/risk_scores.csv"
        
        try:
            risk_df = load_dataframe(risk_path, format='csv')
            log.info(f"Loaded {len(risk_df)} risk scores")
            return risk_df
        except FileNotFoundError:
            log.error("Risk scores not found")
            raise
    
    def load_historical_risk(self) -> Optional[pd.DataFrame]:
        """
        Load historical risk scores for comparison
        
        Returns:
            DataFrame with historical risk or None
        """
        history_path = f"{self.config['paths']['data_processed']}/risk_history.csv"
        
        try:
            history_df = load_dataframe(history_path, format='csv')
            log.info(f"Loaded historical risk data: {len(history_df)} records")
            return history_df
        except FileNotFoundError:
            log.info("No historical risk data found (first run)")
            return None
    
    def init_rag_agent(self):
        """Initialize RAG agent for explanations"""
        if self.rag_agent is None:
            log.info("Initializing RAG agent for explanations...")
            try:
                self.rag_agent = NewsRAGAgent()
                # Try to load existing vector store
                self.rag_agent.vector_store = self.rag_agent.load_vector_store()
                
                if self.rag_agent.vector_store is None:
                    log.warning("RAG vector store not available, alerts will have limited explanations")
            except Exception as e:
                log.warning(f"Failed to initialize RAG agent: {str(e)}")
                self.rag_agent = None
    
    def detect_high_risk_stocks(self, risk_df: pd.DataFrame) -> List[Dict]:
        """
        Detect stocks with high risk levels
        
        Args:
            risk_df: DataFrame with risk scores
            
        Returns:
            List of alert dictionaries
        """
        log.info("Detecting high-risk stocks...")
        
        high_risk = risk_df[risk_df['risk_level'] == 'High'].copy()
        
        alerts = []
        for _, row in high_risk.iterrows():
            alert = {
                'alert_type': 'high_risk',
                'symbol': row['symbol'],
                'risk_score': row['risk_score'],
                'risk_level': row['risk_level'],
                'risk_rank': row['risk_rank'],
                'risk_drivers': row['risk_drivers'],
                'timestamp': datetime.now(),
                'severity': 'HIGH'
            }
            alerts.append(alert)
        
        log.info(f"✓ Detected {len(alerts)} high-risk stocks")
        return alerts
    
    def detect_sudden_spikes(
        self,
        current_risk: pd.DataFrame,
        historical_risk: Optional[pd.DataFrame]
    ) -> List[Dict]:
        """
        Detect sudden risk increases
        
        Args:
            current_risk: Current risk scores
            historical_risk: Historical risk scores
            
        Returns:
            List of alert dictionaries
        """
        if historical_risk is None or historical_risk.empty:
            log.info("No historical data for spike detection")
            return []
        
        log.info("Detecting sudden risk spikes...")
        
        # Get previous risk scores
        historical_risk = historical_risk.sort_values('timestamp')
        prev_risk = historical_risk.groupby('symbol').tail(1)[['symbol', 'risk_score']].copy()
        prev_risk = prev_risk.rename(columns={'risk_score': 'prev_risk_score'})
        
        # Merge with current
        comparison = current_risk.merge(prev_risk, on='symbol', how='left')
        comparison['prev_risk_score'] = comparison['prev_risk_score'].fillna(0.5)
        
        # Calculate change
        comparison['risk_change'] = comparison['risk_score'] - comparison['prev_risk_score']
        comparison['risk_change_pct'] = (comparison['risk_change'] / (comparison['prev_risk_score'] + 0.001)) * 100
        
        # Detect spikes (>20% increase or >0.15 absolute increase)
        spike_threshold_pct = 20
        spike_threshold_abs = 0.15
        
        spikes = comparison[
            (comparison['risk_change_pct'] > spike_threshold_pct) |
            (comparison['risk_change'] > spike_threshold_abs)
        ].copy()
        
        alerts = []
        for _, row in spikes.iterrows():
            alert = {
                'alert_type': 'sudden_spike',
                'symbol': row['symbol'],
                'risk_score': row['risk_score'],
                'prev_risk_score': row['prev_risk_score'],
                'risk_change': row['risk_change'],
                'risk_change_pct': row['risk_change_pct'],
                'risk_level': row['risk_level'],
                'risk_drivers': row['risk_drivers'],
                'timestamp': datetime.now(),
                'severity': 'MEDIUM' if row['risk_change_pct'] < 50 else 'HIGH'
            }
            alerts.append(alert)
        
        log.info(f"✓ Detected {len(alerts)} sudden risk spikes")
        return alerts
    
    def generate_explanation(self, alert: Dict) -> str:
        """
        Generate explanation for an alert using RAG
        
        Args:
            alert: Alert dictionary
            
        Returns:
            Explanation text
        """
        symbol = alert['symbol']
        alert_type = alert['alert_type']
        
        # Initialize RAG if needed
        if self.rag_agent is None:
            self.init_rag_agent()
        
        # Generate query based on alert type
        if alert_type == 'high_risk':
            query = f"Why is {symbol} risk high? What are the concerns?"
        elif alert_type == 'sudden_spike':
            query = f"What recent developments caused {symbol} risk to increase?"
        else:
            query = f"What is the latest news about {symbol}?"
        
        # Get explanation from RAG
        if self.rag_agent and self.rag_agent.vector_store:
            try:
                result = self.rag_agent.generate_explanation(query, symbol)
                return result['explanation']
            except Exception as e:
                log.warning(f"Failed to generate RAG explanation: {str(e)}")
        
        # Fallback to basic explanation
        return self._generate_basic_explanation(alert)
    
    def _generate_basic_explanation(self, alert: Dict) -> str:
        """
        Generate basic explanation without RAG
        
        Args:
            alert: Alert dictionary
            
        Returns:
            Basic explanation
        """
        symbol = alert['symbol']
        risk_score = alert['risk_score']
        drivers = alert.get('risk_drivers', 'Unknown drivers')
        
        explanation = f"Risk alert for {symbol}:\n"
        explanation += f"Risk Score: {risk_score:.3f}\n"
        explanation += f"Risk Drivers: {drivers}\n"
        
        if alert['alert_type'] == 'sudden_spike':
            change = alert.get('risk_change', 0)
            change_pct = alert.get('risk_change_pct', 0)
            explanation += f"Risk increased by {change:.3f} ({change_pct:.1f}%)\n"
        
        return explanation
    
    def format_alert_message(self, alert: Dict, explanation: str) -> str:
        """
        Format alert into readable message
        
        Args:
            alert: Alert dictionary
            explanation: Explanation text
            
        Returns:
            Formatted alert message
        """
        symbol = alert['symbol']
        severity = alert['severity']
        alert_type = alert['alert_type'].replace('_', ' ').title()
        
        # Create header
        header = f"\n{'='*70}\n"
        header += f"🚨 {severity} ALERT: {alert_type} - {symbol}\n"
        header += f"{'='*70}\n"
        
        # Create details
        details = f"Timestamp: {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        details += f"Risk Score: {alert['risk_score']:.3f} ({alert['risk_level']})\n"
        
        if alert['alert_type'] == 'sudden_spike':
            details += f"Previous Score: {alert.get('prev_risk_score', 0):.3f}\n"
            details += f"Change: +{alert.get('risk_change', 0):.3f} ({alert.get('risk_change_pct', 0):.1f}%)\n"
        
        details += f"Risk Rank: #{alert['risk_rank']}\n"
        details += f"\nRisk Drivers:\n{alert['risk_drivers']}\n"
        
        # Add explanation
        details += f"\nExplanation:\n{explanation}\n"
        
        footer = f"{'='*70}\n"
        
        return header + details + footer
    
    def send_notifications(self, alert_message: str):
        """
        Send alert notifications
        
        Args:
            alert_message: Formatted alert message
        """
        # Console notification
        if self.notification_config.get('console', True):
            print(alert_message)
        
        # Email notification (placeholder)
        if self.notification_config.get('email', False):
            log.info("Email notifications not configured")
            # TODO: Implement email sending
    
    def save_alerts(self, alerts: List[Dict], filename: str = "alerts.csv"):
        """
        Save alerts to file
        
        Args:
            alerts: List of alert dictionaries
            filename: Output filename
        """
        if not alerts:
            log.info("No alerts to save")
            return
        
        ensure_dir(self.config['paths']['data_processed'])
        filepath = f"{self.config['paths']['data_processed']}/{filename}"
        
        # Convert to DataFrame
        alerts_df = pd.DataFrame(alerts)
        
        # Load existing alerts and append
        try:
            existing_alerts = load_dataframe(filepath, format='csv')
            alerts_df = pd.concat([existing_alerts, alerts_df], ignore_index=True)
        except FileNotFoundError:
            pass
        
        save_dataframe(alerts_df, filepath, format='csv')
        log.info(f"✓ Saved {len(alerts)} alerts to {filepath}")
    
    def update_risk_history(self, risk_df: pd.DataFrame):
        """
        Update risk history for trend analysis
        
        Args:
            risk_df: Current risk scores
        """
        history_path = f"{self.config['paths']['data_processed']}/risk_history.csv"
        
        # Add timestamp
        risk_history = risk_df.copy()
        risk_history['timestamp'] = datetime.now()
        
        # Select relevant columns
        history_cols = ['symbol', 'risk_score', 'risk_level', 'timestamp']
        risk_history = risk_history[history_cols]
        
        # Load and append
        try:
            existing_history = load_dataframe(history_path, format='csv')
            risk_history = pd.concat([existing_history, risk_history], ignore_index=True)
            
            # Keep only last 30 days
            risk_history['timestamp'] = pd.to_datetime(risk_history['timestamp'])
            cutoff_date = datetime.now() - pd.Timedelta(days=30)
            risk_history = risk_history[risk_history['timestamp'] > cutoff_date]
            
        except FileNotFoundError:
            pass
        
        save_dataframe(risk_history, history_path, format='csv')
        log.info(f"✓ Updated risk history: {len(risk_history)} records")
    
    def run(self) -> List[Dict]:
        """
        Run the complete alert generation pipeline
        
        Returns:
            List of generated alerts
        """
        log.info("=" * 60)
        log.info("STARTING ALERT AGENT")
        log.info("=" * 60)
        
        # Load data
        risk_df = self.load_risk_scores()
        historical_risk = self.load_historical_risk()
        
        all_alerts = []
        
        # Detect high-risk stocks
        if 'high_risk' in self.triggers:
            high_risk_alerts = self.detect_high_risk_stocks(risk_df)
            all_alerts.extend(high_risk_alerts)
        
        # Detect sudden spikes
        if 'sudden_spike' in self.triggers:
            spike_alerts = self.detect_sudden_spikes(risk_df, historical_risk)
            all_alerts.extend(spike_alerts)
        
        log.info(f"Total alerts generated: {len(all_alerts)}")
        
        # Generate explanations and send notifications
        if all_alerts:
            log.info("Generating explanations and sending notifications...")
            
            for alert in all_alerts:
                # Generate explanation
                explanation = self.generate_explanation(alert)
                alert['explanation'] = explanation
                
                # Format and send
                alert_message = self.format_alert_message(alert, explanation)
                self.send_notifications(alert_message)
        else:
            log.info("✓ No alerts triggered - all stocks within acceptable risk levels")
        
        # Save alerts
        self.save_alerts(all_alerts)
        
        # Update risk history
        self.update_risk_history(risk_df)
        
        log.info("=" * 60)
        log.info("✓ ALERT AGENT COMPLETED")
        log.info("=" * 60)
        
        return all_alerts