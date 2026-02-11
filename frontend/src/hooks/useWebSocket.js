import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';

const SOCKET_URL = 'http://localhost:5000';

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [stats, setStats] = useState(null);
  const [latestAlert, setLatestAlert] = useState(null);
  const [riskUpdates, setRiskUpdates] = useState({});
  const socketRef = useRef(null);

  useEffect(() => {
    // Initialize socket connection
    socketRef.current = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    const socket = socketRef.current;

    // Connection events
    socket.on('connect', () => {
      console.log('✓ WebSocket connected');
      setIsConnected(true);
    });

    socket.on('disconnect', () => {
      console.log('✗ WebSocket disconnected');
      setIsConnected(false);
    });

    socket.on('connection_status', (data) => {
      console.log('Connection status:', data.message);
    });

    // Stats updates
    socket.on('stats_update', (data) => {
      console.log('Stats update:', data);
      setStats(data);
    });

    // Risk updates
    socket.on('risk_update', (data) => {
      console.log('Risk update:', data.symbol, data.risk_score);
      setRiskUpdates(prev => ({
        ...prev,
        [data.symbol]: {
          risk_score: data.risk_score,
          risk_level: data.risk_level,
          timestamp: data.timestamp
        }
      }));
    });

    // New alerts
    socket.on('new_alert', (data) => {
      console.log('New alert:', data);
      setLatestAlert(data);
    });

    // Cleanup on unmount
    return () => {
      socket.disconnect();
    };
  }, []);

  // Subscribe to specific stock
  const subscribeToStock = (symbol) => {
    if (socketRef.current) {
      socketRef.current.emit('subscribe_stock', { symbol });
    }
  };

  // Unsubscribe from stock
  const unsubscribeFromStock = (symbol) => {
    if (socketRef.current) {
      socketRef.current.emit('unsubscribe_stock', { symbol });
    }
  };

  // Request current stats
  const requestStats = () => {
    if (socketRef.current) {
      socketRef.current.emit('request_stats');
    }
  };

  return {
    isConnected,
    stats,
    latestAlert,
    riskUpdates,
    subscribeToStock,
    unsubscribeFromStock,
    requestStats
  };
};