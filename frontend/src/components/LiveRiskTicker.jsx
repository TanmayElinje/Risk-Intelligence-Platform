// frontend/src/components/LiveRiskTicker.jsx - MORE STOCKS
import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';

const LiveRiskTicker = () => {
  const [stocks, setStocks] = useState([]);
  const { lastMessage } = useWebSocket();

  useEffect(() => {
    fetchStocks();
    
    // Refresh every 30 seconds for variety
    const interval = setInterval(fetchStocks, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (lastMessage?.type === 'stats_update') {
      fetchStocks();
    }
  }, [lastMessage]);

  const fetchStocks = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/risk-scores');
      const data = await response.json();
      
      // Handle different response structures
      let riskScores = [];
      
      if (Array.isArray(data)) {
        riskScores = data;
      } else if (data.risk_scores && Array.isArray(data.risk_scores)) {
        riskScores = data.risk_scores;
      } else if (typeof data === 'object') {
        riskScores = Object.values(data).find(val => Array.isArray(val)) || [];
      }
      
      // Get diverse stocks across all risk levels (not just high risk)
      const allStocks = riskScores.filter(s => s && s.symbol && s.risk_score);
      
      // Take top 30 for variety (increased from 10)
      const selectedStocks = allStocks.slice(0, 30);
      
      setStocks(selectedStocks);
    } catch (error) {
      console.error('Error fetching ticker stocks:', error);
      setStocks([]);
    }
  };

  const getRiskColor = (riskScore) => {
    if (riskScore > 0.6) return 'text-red-600 bg-red-50';
    if (riskScore > 0.4) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  const getRiskLabel = (riskScore) => {
    if (riskScore > 0.6) return 'HIGH';
    if (riskScore > 0.4) return 'MED';
    return 'LOW';
  };

  const getChangeIcon = () => {
    const rand = Math.random();
    if (rand > 0.6) return <TrendingUp className="w-3 h-3 text-green-600" />;
    if (rand > 0.3) return <TrendingDown className="w-3 h-3 text-red-600" />;
    return <Minus className="w-3 h-3 text-gray-500" />;
  };

  const getSimulatedChange = () => {
    const change = (Math.random() * 5 - 2.5).toFixed(2);
    const isPositive = parseFloat(change) > 0;
    return (
      <span className={`text-xs font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        {isPositive ? '+' : ''}{change}%
      </span>
    );
  };

  const getSimulatedPrice = () => {
    return (Math.random() * 500 + 50).toFixed(2);
  };

  if (stocks.length === 0) {
    return null;
  }

  return (
    <div className="bg-gray-900 text-white py-2 overflow-hidden border-b border-gray-700 shadow-lg">
      <div className="ticker-wrap">
        <div className="ticker-move">
          {/* Duplicate stocks THREE times for longer seamless loop */}
          {[...stocks, ...stocks, ...stocks].map((stock, index) => (
            <div
              key={`${stock.symbol}-${index}`}
              className="ticker-item inline-flex items-center gap-3 px-6 py-1"
            >
              {/* Stock Symbol */}
              <span className="font-bold text-sm tracking-wide">{stock.symbol}</span>

              {/* Simulated Price */}
              <span className="text-gray-300 text-sm font-mono">
                ${getSimulatedPrice()}
              </span>

              {/* Change Indicator */}
              <div className="flex items-center gap-1">
                {getChangeIcon()}
                {getSimulatedChange()}
              </div>

              {/* Risk Badge */}
              <span
                className={`px-2 py-0.5 rounded text-xs font-bold ${getRiskColor(
                  stock.risk_score
                )}`}
              >
                {getRiskLabel(stock.risk_score)}
              </span>

              {/* Separator */}
              <span className="text-gray-600 text-lg">•</span>
            </div>
          ))}
        </div>
      </div>

      {/* CSS for animation */}
      <style>{`
        .ticker-wrap {
          width: 100%;
          overflow: hidden;
          white-space: nowrap;
        }

        .ticker-move {
          display: inline-block;
          animation: ticker 90s linear infinite;
        }

        .ticker-move:hover {
          animation-play-state: paused;
        }

        @keyframes ticker {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-33.333%);
          }
        }

        .ticker-item {
          transition: background-color 0.2s;
        }

        .ticker-item:hover {
          background-color: rgba(255, 255, 255, 0.1);
        }
      `}</style>
    </div>
  );
};

export default LiveRiskTicker;