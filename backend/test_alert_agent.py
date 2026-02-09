"""
Test Alert Agent
"""
from backend.utils import log
from backend.agents import AlertAgent

def main():
    """Test alert agent"""
    log.info("=" * 60)
    log.info("TESTING ALERT AGENT")
    log.info("=" * 60)
    
    # Initialize and run agent
    agent = AlertAgent()
    alerts = agent.run()
    
    # Summary
    log.info("\n" + "=" * 60)
    log.info("ALERT SUMMARY")
    log.info("=" * 60)
    
    if alerts:
        log.info(f"Total alerts: {len(alerts)}")
        
        # Group by type
        alert_types = {}
        for alert in alerts:
            alert_type = alert['alert_type']
            alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
        
        for alert_type, count in alert_types.items():
            log.info(f"  {alert_type}: {count}")
        
        # Group by severity
        severity_counts = {}
        for alert in alerts:
            severity = alert['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        log.info("\nBy severity:")
        for severity, count in severity_counts.items():
            log.info(f"  {severity}: {count}")
    else:
        log.info("No alerts generated")
    
    log.info("\n" + "=" * 60)
    log.info("✓ ALERT AGENT TEST COMPLETE")
    log.info("=" * 60)

if __name__ == "__main__":
    main()