// frontend/src/pages/StockComparison.jsx
import React, { useState, useEffect } from 'react';
import { Search, X, TrendingUp, TrendingDown, Minus, Plus } from 'lucide-react';

const StockComparison = () => {
  const [selectedStocks, setSelectedStocks] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [availableStocks, setAvailableStocks] = useState([]);
  const [comparisonData, setComparisonData] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch available stocks
  useEffect(() => {
    fetchAvailableStocks();
  }, []);

  // Fetch comparison data when stocks are selected
  useEffect(() => {
    if (selectedStocks.length > 0) {
      fetchComparisonData();
    }
  }, [selectedStocks]);

  const fetchAvailableStocks = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/risk-scores');
      const data = await response.json();
      setAvailableStocks(data.data || []);
    } catch (error) {
      console.error('Error fetching stocks:', error);
    }
  };

  const fetchComparisonData = async () => {
    try {
      setLoading(true);
      const promises = selectedStocks.map(symbol =>
        fetch(`http://localhost:5000/api/risk-scores`).then(r => r.json())
      );
      
      const results = await Promise.all(promises);
      
      // Find the selected stocks in the results
      const stocksData = selectedStocks.map(symbol => {
        const allStocks = results[0]?.data || [];
        return allStocks.find(s => s.symbol === symbol);
      }).filter(Boolean);
      
      setComparisonData(stocksData);
    } catch (error) {
      console.error('Error fetching comparison data:', error);
    } finally {
      setLoading(false);
    }
  };

  const addStock = (symbol) => {
    if (selectedStocks.length >= 4) {
      alert('Maximum 4 stocks can be compared');
      return;
    }
    if (!selectedStocks.includes(symbol)) {
      setSelectedStocks([...selectedStocks, symbol]);
      setSearchTerm('');
    }
  };

  const removeStock = (symbol) => {
    setSelectedStocks(selectedStocks.filter(s => s !== symbol));
    setComparisonData(comparisonData.filter(s => s.symbol !== symbol));
  };

  const filteredStocks = availableStocks.filter(stock =>
    stock.symbol.toLowerCase().includes(searchTerm.toLowerCase()) &&
    !selectedStocks.includes(stock.symbol)
  ).slice(0, 10);

  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'high': return 'text-red-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getRiskBg = (level) => {
    switch (level?.toLowerCase()) {
      case 'high': return 'bg-red-50';
      case 'medium': return 'bg-yellow-50';
      case 'low': return 'bg-green-50';
      default: return 'bg-gray-50';
    }
  };

  const getRiskIcon = (level) => {
    switch (level?.toLowerCase()) {
      case 'high': return <TrendingDown className="w-5 h-5" />;
      case 'medium': return <Minus className="w-5 h-5" />;
      case 'low': return <TrendingUp className="w-5 h-5" />;
      default: return <Minus className="w-5 h-5" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6 transition-colors">
        <h1 className="text-3xl font-bold text-gray-900">
          Stock Comparison
        </h1>
        <p className="text-gray-600 mt-2">
          Compare up to 4 stocks side-by-side
        </p>
      </div>

      {/* Stock Selector */}
      <div className="bg-white rounded-lg shadow p-6 transition-colors">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Select Stocks to Compare ({selectedStocks.length}/4)
        </h2>

        {/* Selected Stocks Pills */}
        {selectedStocks.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {selectedStocks.map(symbol => (
              <div
                key={symbol}
                className="flex items-center gap-2 px-3 py-2 bg-blue-100 text-blue-700 rounded-lg"
              >
                <span className="font-medium">{symbol}</span>
                <button
                  onClick={() => removeStock(symbol)}
                  className="hover:text-blue-900"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search stocks by symbol..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            disabled={selectedStocks.length >= 4}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
        </div>

        {/* Search Results Dropdown */}
        {searchTerm && filteredStocks.length > 0 && (
          <div className="mt-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {filteredStocks.map(stock => (
              <button
                key={stock.symbol}
                onClick={() => addStock(stock.symbol)}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-semibold text-gray-900">
                      {stock.symbol}
                    </span>
                    <span className="ml-2 text-sm text-gray-500">
                      Risk: {(stock.risk_score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <Plus className="w-5 h-5 text-blue-600" />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Comparison Table */}
      {comparisonData.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden transition-colors">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Comparison Results
            </h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                    Metric
                  </th>
                  {comparisonData.map(stock => (
                    <th key={stock.symbol} className="px-6 py-3 text-center text-sm font-medium text-gray-700">
                      {stock.symbol}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {/* Risk Score Row */}
                <tr className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">
                    Risk Score
                  </td>
                  {comparisonData.map(stock => (
                    <td key={stock.symbol} className="px-6 py-4 text-center">
                      <div className="flex flex-col items-center">
                        <span className={`text-2xl font-bold ${getRiskColor(stock.risk_level)}`}>
                          {(stock.risk_score * 100).toFixed(1)}%
                        </span>
                        <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                          <div
                            className={`h-2 rounded-full ${
                              stock.risk_score > 0.6 ? 'bg-red-600' :
                              stock.risk_score > 0.4 ? 'bg-yellow-600' :
                              'bg-green-600'
                            }`}
                            style={{ width: `${stock.risk_score * 100}%` }}
                          />
                        </div>
                      </div>
                    </td>
                  ))}
                </tr>

                {/* Risk Level Row */}
                <tr className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">
                    Risk Level
                  </td>
                  {comparisonData.map(stock => (
                    <td key={stock.symbol} className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <span className={getRiskColor(stock.risk_level)}>
                          {getRiskIcon(stock.risk_level)}
                        </span>
                        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                          stock.risk_level?.toLowerCase() === 'high' ? 'bg-red-100 text-red-800' :
                          stock.risk_level?.toLowerCase() === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {stock.risk_level || 'Unknown'}
                        </span>
                      </div>
                    </td>
                  ))}
                </tr>

                {/* Sentiment Row */}
                <tr className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">
                    Sentiment
                  </td>
                  {comparisonData.map(stock => (
                    <td key={stock.symbol} className="px-6 py-4 text-center">
                      <div className="flex flex-col items-center">
                        <span className={`text-lg font-semibold ${
                          stock.avg_sentiment > 0 ? 'text-green-600' :
                          stock.avg_sentiment < 0 ? 'text-red-600' :
                          'text-gray-600'
                        }`}>
                          {stock.avg_sentiment > 0 ? '↑ Positive' :
                           stock.avg_sentiment < 0 ? '↓ Negative' :
                           '— Neutral'}
                        </span>
                        <span className="text-sm text-gray-500 mt-1">
                          Score: {stock.avg_sentiment?.toFixed(2) || 'N/A'}
                        </span>
                      </div>
                    </td>
                  ))}
                </tr>

                {/* Winner Indicator */}
                <tr className="bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">
                    Lowest Risk
                  </td>
                  {comparisonData.map(stock => {
                    const lowestRisk = Math.min(...comparisonData.map(s => s.risk_score));
                    const isWinner = stock.risk_score === lowestRisk;
                    
                    return (
                      <td key={stock.symbol} className="px-6 py-4 text-center">
                        {isWinner && (
                          <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
                            🏆 Best Choice
                          </span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty State */}
      {selectedStocks.length === 0 && (
        <div className="bg-white rounded-lg shadow p-12 text-center transition-colors">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Search className="w-8 h-8 text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No Stocks Selected
          </h3>
          <p className="text-gray-600">
            Search and select stocks above to start comparing
          </p>
        </div>
      )}
    </div>
  );
};

export default StockComparison;