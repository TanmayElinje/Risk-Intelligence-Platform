// frontend/src/components/AlertNotifier.jsx
import { useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useNotifications } from '../hooks/useNotifications';
import { useNavigate } from 'react-router-dom';

const AlertNotifier = () => {
  const { lastMessage } = useWebSocket();
  const { showNotification, permission } = useNotifications();
  const navigate = useNavigate();

  useEffect(() => {
    if (!lastMessage) return;

    // Handle stats updates for high risk alerts
    if (lastMessage.type === 'stats_update') {
      const { high_risk_stocks } = lastMessage;
      
      // If high risk stocks exceed threshold, notify
      if (high_risk_stocks && high_risk_stocks > 10) {
        showNotification('⚠️ High Risk Alert', {
          body: `${high_risk_stocks} stocks are now at high risk!`,
          tag: 'high-risk-count',
          soundType: 'high-risk',
          onClick: () => {
            navigate('/');
            window.focus();
          }
        });
      }
    }

    // Handle individual stock alerts (if your backend sends them)
    if (lastMessage.type === 'stock_alert') {
      const { symbol, risk_level, message } = lastMessage;
      
      let soundType = 'default';
      let icon = '📊';
      
      if (risk_level === 'High') {
        soundType = 'high-risk';
        icon = '🔴';
      } else if (risk_level === 'Medium') {
        soundType = 'alert';
        icon = '🟡';
      }

      showNotification(`${icon} ${symbol} - ${risk_level} Risk`, {
        body: message || `${symbol} risk level changed to ${risk_level}`,
        tag: `stock-${symbol}`,
        soundType,
        onClick: () => {
          navigate(`/stock/${symbol}`);
          window.focus();
        }
      });
    }
  }, [lastMessage, showNotification, navigate]);

  // This component doesn't render anything
  return null;
};

export default AlertNotifier;