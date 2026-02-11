"""
Alert Agent - Monitor risk scores and generate alerts
Now using PostgreSQL for data persistence
"""
from typing import List, Dict
from datetime import datetime, timedelta
from backend.utils import log, load_config
from backend.database import DatabaseService
from backend.agents.rag_agent import NewsRAGAgent

class AlertAgent:
    """
    Agent responsible for monitoring risk scores and generating alerts
    """
    
    def __init__(self):
        self.config = load_config()
        self.alert_thresholds = {
            'high_risk': 0.6,
            'spike_threshold': 0.2,  # 20% increase
            'spike_absolute': 0.15   # Absolute increase
        }
        self.rag_agent = None
    
    def load_rag_agent(self):
        """Load RAG agent for explanations (lazy loading)"""
        if self.rag_agent is None:
            try:
                log.info("Loading RAG agent for alert explanations...")
                self.rag_agent = NewsRAGAgent()
                self.rag_agent.vector_store = self.rag_agent.load_vector_store()
                if self.rag_agent.vector_store:
                    log.info("✓ RAG agent loaded successfully")
                else:
                    log.warning("RAG vector store not found, alerts will have basic explanations")
            except Exception as e:
                log.error(f"Failed to load RAG agent: {str(e)}")
                self.rag_agent = None
    
    def detect_high_risk_stocks(self, risk_scores_df) -> List[Dict]:
        """Detect stocks with high risk levels"""
        alerts = []
        
        high_risk_stocks = risk_scores_df[
            risk_scores_df['risk_level'] == 'High'
        ]
        
        for _, stock in high_risk_stocks.iterrows():
            alert = {
                'symbol': stock['symbol'],
                'alert_type': 'high_risk',
                'severity': 'HIGH',
                'risk_score': stock['risk_score'],
                'prev_risk_score': None,
                'risk_change': None,
                'risk_change_pct': None,
                'risk_level': stock['risk_level'],
                'risk_drivers': stock['risk_drivers'],
                'explanation': None,
                'timestamp': datetime.utcnow()
            }
            alerts.append(alert)
        
        return alerts
    
    def detect_sudden_spikes(self, current_scores_df, historical_scores_df) -> List[Dict]:
        """Detect sudden spikes in risk scores"""
        alerts = []
        
        if historical_scores_df.empty:
            log.warning("No historical data available for spike detection")
            return alerts
        
        # Get average historical risk for each stock
        historical_avg = historical_scores_df.groupby('symbol')['risk_score'].mean().to_dict()
        
        for _, stock in current_scores_df.iterrows():
            symbol = stock['symbol']
            current_risk = stock['risk_score']
            
            if symbol not in historical_avg:
                continue
            
            prev_risk = historical_avg[symbol]
            risk_change = current_risk - prev_risk
            risk_change_pct = (risk_change / prev_risk * 100) if prev_risk > 0 else 0
            
            # Check if spike exceeds threshold
            if risk_change > self.alert_thresholds['spike_absolute'] or \
               risk_change_pct > self.alert_thresholds['spike_threshold'] * 100:
                
                alert = {
                    'symbol': symbol,
                    'alert_type': 'sudden_spike',
                    'severity': 'MEDIUM',
                    'risk_score': current_risk,
                    'prev_risk_score': prev_risk,
                    'risk_change': risk_change,
                    'risk_change_pct': risk_change_pct,
                    'risk_level': stock['risk_level'],
                    'risk_drivers': stock['risk_drivers'],
                    'explanation': None,
                    'timestamp': datetime.utcnow()
                }
                alerts.append(alert)
        
        return alerts
    
    def generate_explanations(self, alerts: List[Dict]) -> List[Dict]:
        """Generate RAG-based explanations for alerts"""
        if not self.rag_agent or not self.rag_agent.vector_store:
            log.warning("RAG agent not available, using basic explanations")
            for alert in alerts:
                alert['explanation'] = f"Alert for {alert['symbol']}: {alert['risk_drivers']}"
            return alerts
        
        log.info(f"Generating explanations for {len(alerts)} alerts...")
        
        for alert in alerts:
            try:
                query = f"Why is {alert['symbol']} showing {alert['alert_type']}? Risk drivers: {alert['risk_drivers']}"
                
                result = self.rag_agent.generate_explanation(
                    query=query,
                    stock_symbol=alert['symbol']
                )
                
                alert['explanation'] = result.get('explanation', alert['risk_drivers'])
                
            except Exception as e:
                log.error(f"Failed to generate explanation for {alert['symbol']}: {str(e)}")
                alert['explanation'] = alert['risk_drivers']
        
        return alerts
    
    def send_notifications(self, alerts: List[Dict]):
        """Send alert notifications (console for now)"""
        if not alerts:
            log.info("No alerts to send")
            return
        
        log.info("=" * 60)
        log.info(f"SENDING {len(alerts)} ALERT NOTIFICATIONS")
        log.info("=" * 60)
        
        for alert in alerts:
            severity_icon = "🚨" if alert['severity'] == 'HIGH' else "⚠️"
            
            log.info(f"{severity_icon} {alert['alert_type'].upper()}: {alert['symbol']}")
            log.info(f"   Risk Score: {alert['risk_score']:.3f} ({alert['risk_level']})")
            
            if alert['risk_change']:
                log.info(f"   Change: +{alert['risk_change']:.3f} ({alert['risk_change_pct']:.1f}%)")
            
            log.info(f"   Drivers: {alert['risk_drivers']}")
            
            if alert['explanation']:
                log.info(f"   Explanation: {alert['explanation'][:100]}...")
            
            log.info("-" * 60)
    
    def process(self):
        """
        Main processing method - Detect alerts and save to DB
        """
        log.info("=" * 60)
        log.info("ALERT AGENT - Monitoring Risk Alerts")
        log.info("=" * 60)
        
        with DatabaseService() as db:
            # Load current risk scores
            log.info("Loading current risk scores...")
            current_scores = db.get_latest_risk_scores()
            
            if current_scores.empty:
                log.error("No risk scores found! Run risk agent first.")
                return None
            
            log.info(f"Loaded {len(current_scores)} current risk scores")
            
            # Load historical risk scores
            log.info("Loading historical risk scores...")
            historical_scores = db.get_risk_history(days=30)
            
            # Detect high risk stocks
            log.info("Detecting high risk stocks...")
            high_risk_alerts = self.detect_high_risk_stocks(current_scores)
            log.info(f"Found {len(high_risk_alerts)} high risk alerts")
            
            # Detect sudden spikes
            log.info("Detecting sudden risk spikes...")
            spike_alerts = self.detect_sudden_spikes(current_scores, historical_scores)
            log.info(f"Found {len(spike_alerts)} spike alerts")
            
            # Combine all alerts
            all_alerts = high_risk_alerts + spike_alerts
            
            if not all_alerts:
                log.info("No alerts generated")
                return []
            
            # Load RAG agent for explanations
            self.load_rag_agent()
            
            # Generate explanations
            all_alerts = self.generate_explanations(all_alerts)
            
            # Send notifications
            self.send_notifications(all_alerts)
            
            # Save alerts to database
            log.info("Saving alerts to database...")
            db.save_alerts(all_alerts)
            
            log.info("=" * 60)
            log.info(f"✓ ALERT AGENT COMPLETED - Generated {len(all_alerts)} alerts")
            log.info("=" * 60)
            
            return all_alerts

def main():
    """Main execution"""
    agent = AlertAgent()
    alerts = agent.process()
    
    if alerts is not None:
        log.info(f"Total alerts generated: {len(alerts)}")

if __name__ == "__main__":
    main()