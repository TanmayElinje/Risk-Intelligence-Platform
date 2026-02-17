// frontend/src/components/RiskScoreTable.jsx - WITH EXPORT + FILTERING
import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import ExportButton from './ExportButton';
import FilterControls from './FilterControls';

const RiskScoreTable = ({ scores }) => {
  const navigate = useNavigate();
  const { lastMessage } = useWebSocket();
  const [flashingRows, setFlashingRows] = useState(new Set());
  const [previousScores, setPreviousScores] = useState({});
  
  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('all');
  const [sortBy, setSortBy] = useState('risk_desc');
  const [showFilters, setShowFilters] = useState(false);

  // Detect changes and trigger flash animation
  useEffect(() => {
    if (!scores) return;

    const newFlashing = new Set();
    
    scores.forEach(stock => {
      const prevScore = previousScores[stock.symbol];
      if (prevScore && prevScore !== stock.risk_score) {
        newFlashing.add(stock.symbol);
      }
    });

    if (newFlashing.size > 0) {
      setFlashingRows(newFlashing);
      setTimeout(() => setFlashingRows(new Set()), 1000);
    }

    const scoreMap = {};
    scores.forEach(stock => {
      scoreMap[stock.symbol] = stock.risk_score;
    });
    setPreviousScores(scoreMap);
  }, [scores]);

  // Filter and sort stocks
  const filteredScores = useMemo(() => {
    if (!scores) return [];

    let filtered = [...scores];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(stock =>
        stock.symbol.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply risk level filter
    if (riskFilter !== 'all') {
      filtered = filtered.filter(stock =>
        stock.risk_level?.toLowerCase() === riskFilter.toLowerCase()
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'risk_desc':
          return b.risk_score - a.risk_score;
        case 'risk_asc':
          return a.risk_score - b.risk_score;
        case 'symbol_asc':
          return a.symbol.localeCompare(b.symbol);
        case 'symbol_desc':
          return b.symbol.localeCompare(a.symbol);
        case 'sentiment_desc':
          return (b.avg_sentiment || 0) - (a.avg_sentiment || 0);
        case 'sentiment_asc':
          return (a.avg_sentiment || 0) - (b.avg_sentiment || 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [scores, searchTerm, riskFilter, sortBy]);

  const getRiskBadgeColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRiskIcon = (level) => {
    switch (level?.toLowerCase()) {
      case 'high':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      case 'medium':
        return <Minus className="w-4 h-4 text-yellow-600" />;
      case 'low':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      default:
        return <Minus className="w-4 h-4 text-gray-600" />;
    }
  };

  const getRiskBarColor = (score) => {
    if (score > 0.6) return 'bg-red-600';
    if (score > 0.4) return 'bg-yellow-600';
    return 'bg-green-600';
  };

  if (!scores || scores.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 transition-colors">
        <h2 className="text-lg font-semibold mb-4 text-gray-900">Risk Scores</h2>
        <p className="text-gray-500 text-center py-8">No risk data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filter Controls */}
      <div className="bg-white rounded-lg shadow p-4 transition-colors">
        <FilterControls
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          riskFilter={riskFilter}
          setRiskFilter={setRiskFilter}
          sortBy={sortBy}
          setSortBy={setSortBy}
          showFilters={showFilters}
          setShowFilters={setShowFilters}
        />
      </div>

      {/* Risk Scores Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden transition-colors">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Risk Scores</h2>
              <p className="text-sm text-gray-500 mt-1">
                Showing {filteredScores.length} of {scores.length} stocks
              </p>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Live Indicator */}
              <div className="flex items-center gap-2">
                <div className="relative">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  <div className="absolute inset-0 w-3 h-3 bg-green-500 rounded-full animate-ping"></div>
                </div>
                <span className="text-sm text-gray-600 font-medium">Live Updates</span>
              </div>

              {/* Export Button - exports filtered data */}
              <ExportButton 
                data={filteredScores}
                filename="risk-scores"
                formatData={(data) => data.map(stock => ({
                  Symbol: stock.symbol,
                  'Risk Score': `${(stock.risk_score * 100).toFixed(2)}%`,
                  'Risk Level': stock.risk_level,
                  Sentiment: stock.avg_sentiment > 0 ? 'Positive' : stock.avg_sentiment < 0 ? 'Negative' : 'Neutral',
                  'Sentiment Score': stock.avg_sentiment?.toFixed(2) || 'N/A',
                  Date: new Date().toLocaleDateString(),
                }))}
                label="Export"
              />
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          {filteredScores.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-500">
                No stocks match your filters
              </p>
              <button
                onClick={() => {
                  setSearchTerm('');
                  setRiskFilter('all');
                }}
                className="mt-4 text-blue-600 hover:underline"
              >
                Clear filters
              </button>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Level
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sentiment
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredScores.map((stock) => {
                  const isFlashing = flashingRows.has(stock.symbol);
                  
                  return (
                    <tr
                      key={stock.symbol}
                      onClick={() => navigate(`/stock/${stock.symbol}`)}
                      className={`cursor-pointer transition-all duration-300 hover:bg-gray-50 ${
                        isFlashing ? 'bg-blue-100 animate-flash' : ''
                      }`}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {getRiskIcon(stock.risk_level)}
                          <span className="font-medium text-gray-900">{stock.symbol}</span>
                        </div>
                      </td>
                      
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="w-24 bg-gray-200 rounded-full h-2 overflow-hidden">
                            <div
                              className={`h-2 rounded-full transition-all duration-500 ${getRiskBarColor(stock.risk_score)}`}
                              style={{ 
                                width: `${(stock.risk_score * 100)}%`,
                                transition: 'width 0.5s ease-in-out'
                              }}
                            />
                          </div>
                          
                          <span className={`text-sm font-semibold transition-all duration-300 text-gray-900 ${
                            isFlashing ? 'scale-110' : ''
                          }`}>
                            {(stock.risk_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </td>
                      
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-3 py-1 text-xs font-semibold rounded-full transition-all duration-300 ${
                            getRiskBadgeColor(stock.risk_level)
                          } ${isFlashing ? 'ring-2 ring-blue-400' : ''}`}
                        >
                          {stock.risk_level || 'Unknown'}
                        </span>
                      </td>
                      
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`text-sm font-medium transition-colors duration-300 ${
                            stock.avg_sentiment > 0
                              ? 'text-green-600'
                              : stock.avg_sentiment < 0
                              ? 'text-red-600'
                              : 'text-gray-600'
                          }`}
                        >
                          {stock.avg_sentiment 
                            ? stock.avg_sentiment > 0 
                              ? '↑ Positive' 
                              : '↓ Negative'
                            : '— Neutral'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* CSS Animations */}
        <style>{`
          @keyframes flash {
            0%, 100% {
              background-color: rgba(59, 130, 246, 0.1);
            }
            50% {
              background-color: rgba(59, 130, 246, 0.3);
            }
          }

          .dark .animate-flash {
            animation: flash-dark 1s ease-in-out;
          }

          @keyframes flash-dark {
            0%, 100% {
              background-color: rgba(59, 130, 246, 0.2);
            }
            50% {
              background-color: rgba(59, 130, 246, 0.4);
            }
          }
        `}</style>
      </div>
    </div>
  );
};

export default RiskScoreTable;