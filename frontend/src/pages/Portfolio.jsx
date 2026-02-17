// frontend/src/pages/Portfolio.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Plus, TrendingUp, TrendingDown, DollarSign, Briefcase, Edit, Trash2, Search, X, ChevronDown } from 'lucide-react';
import { getToken } from '../services/authService';

const Portfolio = () => {
  const [portfolio, setPortfolio] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingHolding, setEditingHolding] = useState(null);

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      const token = getToken();
      const response = await fetch('http://localhost:5000/api/portfolio', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      setPortfolio(data.holdings || []);
      setSummary(data.summary || {});
    } catch (error) {
      console.error('Error fetching portfolio:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteHolding = async (holdingId) => {
    if (!confirm('Are you sure you want to remove this holding?')) return;
    
    try {
      const token = getToken();
      await fetch(`http://localhost:5000/api/portfolio/${holdingId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      fetchPortfolio();
    } catch (error) {
      console.error('Error deleting holding:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6 transition-colors">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              My Portfolio
            </h1>
            <p className="text-gray-600 mt-2">
              Track your stock holdings and performance
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            <Plus className="w-5 h-5" />
            Add Holding
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Total Value */}
          <div className="bg-white rounded-lg shadow p-6 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Value</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  ${summary.total_value?.toLocaleString() || '0'}
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          {/* Total Cost */}
          <div className="bg-white rounded-lg shadow p-6 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Cost</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  ${summary.total_cost?.toLocaleString() || '0'}
                </p>
              </div>
              <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
                <Briefcase className="w-6 h-6 text-gray-600" />
              </div>
            </div>
          </div>

          {/* Total Gain/Loss */}
          <div className="bg-white rounded-lg shadow p-6 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Gain/Loss</p>
                <p className={`text-2xl font-bold mt-1 ${
                  summary.total_gain_loss >= 0 
                    ? 'text-green-600' 
                    : 'text-red-600'
                }`}>
                  {summary.total_gain_loss >= 0 ? '+' : ''}${summary.total_gain_loss?.toLocaleString() || '0'}
                </p>
              </div>
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                summary.total_gain_loss >= 0 
                  ? 'bg-green-100' 
                  : 'bg-red-100'
              }`}>
                {summary.total_gain_loss >= 0 ? (
                  <TrendingUp className="w-6 h-6 text-green-600" />
                ) : (
                  <TrendingDown className="w-6 h-6 text-red-600" />
                )}
              </div>
            </div>
          </div>

          {/* Return % */}
          <div className="bg-white rounded-lg shadow p-6 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Return %</p>
                <p className={`text-2xl font-bold mt-1 ${
                  summary.total_gain_loss_pct >= 0 
                    ? 'text-green-600' 
                    : 'text-red-600'
                }`}>
                  {summary.total_gain_loss_pct >= 0 ? '+' : ''}{summary.total_gain_loss_pct?.toFixed(2) || '0'}%
                </p>
              </div>
              <div className={`text-3xl ${
                summary.total_gain_loss_pct >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {summary.total_gain_loss_pct >= 0 ? '📈' : '📉'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Holdings Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden transition-colors">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Holdings ({portfolio.length})
          </h2>
        </div>

        {portfolio.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Briefcase className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No Holdings Yet
            </h3>
            <p className="text-gray-600 mb-4">
              Start building your portfolio by adding your first stock
            </p>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
            >
              Add First Holding
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Current Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Gain/Loss</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {portfolio.map((holding) => (
                  <tr key={holding.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-semibold text-gray-900">{holding.symbol}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-700">
                      {holding.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-700">
                      ${holding.purchase_price?.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-700">
                      ${holding.current_price?.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-semibold text-gray-900">
                      ${holding.current_value?.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col">
                        <span className={`font-semibold ${
                          holding.gain_loss >= 0 
                            ? 'text-green-600' 
                            : 'text-red-600'
                        }`}>
                          {holding.gain_loss >= 0 ? '+' : ''}${holding.gain_loss?.toFixed(2)}
                        </span>
                        <span className={`text-sm ${
                          holding.gain_loss_pct >= 0 
                            ? 'text-green-600' 
                            : 'text-red-600'
                        }`}>
                          {holding.gain_loss_pct >= 0 ? '+' : ''}{holding.gain_loss_pct?.toFixed(2)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setEditingHolding(holding)}
                          className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => deleteHolding(holding.id)}
                          className="p-1 text-red-600 hover:bg-red-50 rounded"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add/Edit Modal */}
      {(showAddModal || editingHolding) && (
        <AddHoldingModal
          isOpen={showAddModal || !!editingHolding}
          onClose={() => {
            setShowAddModal(false);
            setEditingHolding(null);
          }}
          onSuccess={fetchPortfolio}
          editingHolding={editingHolding}
        />
      )}
    </div>
  );
};


// ==================== STOCK SEARCH DROPDOWN ====================

const StockSearchDropdown = ({ value, onChange, disabled }) => {
  const [query, setQuery] = useState(value || '');
  const [stocks, setStocks] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const wrapperRef = useRef(null);
  const inputRef = useRef(null);

  // Fetch all stocks once on mount
  useEffect(() => {
    const fetchStocks = async () => {
      setLoading(true);
      try {
        const token = getToken();
        const response = await fetch('http://localhost:5000/api/risk-scores', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        if (data.data && Array.isArray(data.data)) {
          // Extract unique symbols with risk info
          const stockList = data.data.map(s => ({
            symbol: s.symbol,
            risk_score: s.risk_score,
            risk_level: s.risk_level,
          }));
          // Dedupe by symbol
          const unique = [...new Map(stockList.map(s => [s.symbol, s])).values()];
          unique.sort((a, b) => a.symbol.localeCompare(b.symbol));
          setStocks(unique);
        }
      } catch (error) {
        console.error('Error fetching stocks:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchStocks();
  }, []);

  // Sync external value changes (e.g. editing mode)
  useEffect(() => {
    setQuery(value || '');
  }, [value]);

  // Filter stocks based on query
  useEffect(() => {
    if (!query.trim()) {
      setFiltered(stocks);
    } else {
      const q = query.toUpperCase();
      setFiltered(stocks.filter(s => s.symbol.includes(q)));
    }
    setHighlightIndex(-1);
  }, [query, stocks]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectStock = useCallback((symbol) => {
    setQuery(symbol);
    onChange(symbol);
    setIsOpen(false);
    setHighlightIndex(-1);
  }, [onChange]);

  const handleKeyDown = (e) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true);
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightIndex(prev => Math.min(prev + 1, filtered.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightIndex >= 0 && highlightIndex < filtered.length) {
          selectStock(filtered[highlightIndex].symbol);
        } else if (filtered.length === 1) {
          selectStock(filtered[0].symbol);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setHighlightIndex(-1);
        break;
    }
  };

  const getRiskBadge = (level) => {
    if (!level) return null;
    const colors = {
      high: 'bg-red-100 text-red-700',
      medium: 'bg-yellow-100 text-yellow-700',
      low: 'bg-green-100 text-green-700',
    };
    return (
      <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${colors[level] || ''}`}>
        {level.charAt(0).toUpperCase() + level.slice(1)}
      </span>
    );
  };

  return (
    <div ref={wrapperRef} className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          ref={inputRef}
          type="text"
          required
          disabled={disabled}
          value={query}
          onChange={(e) => {
            const val = e.target.value.toUpperCase();
            setQuery(val);
            onChange(val);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          className="w-full pl-9 pr-8 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
          placeholder="Search stocks... (e.g. AAPL)"
          autoComplete="off"
        />
        {query && !disabled && (
          <button
            type="button"
            onClick={() => {
              setQuery('');
              onChange('');
              inputRef.current?.focus();
              setIsOpen(true);
            }}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 text-gray-400 hover:text-gray-600 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && !disabled && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {loading ? (
            <div className="px-4 py-3 text-sm text-gray-500 text-center">
              Loading stocks...
            </div>
          ) : filtered.length === 0 ? (
            <div className="px-4 py-3 text-sm text-gray-500 text-center">
              {query ? `No stocks matching "${query}"` : 'No stocks available'}
            </div>
          ) : (
            filtered.map((stock, index) => (
              <button
                key={stock.symbol}
                type="button"
                onClick={() => selectStock(stock.symbol)}
                className={`w-full text-left px-4 py-2.5 flex items-center justify-between transition-colors ${
                  index === highlightIndex
                    ? 'bg-blue-50'
                    : 'hover:bg-gray-50'
                } ${
                  stock.symbol === value
                    ? 'bg-blue-50'
                    : ''
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="font-semibold text-gray-900 text-sm">
                    {stock.symbol}
                  </span>
                  {stock.risk_score != null && (
                    <span className="text-xs text-gray-500">
                      Risk: {(stock.risk_score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
                {getRiskBadge(stock.risk_level)}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
};


// ==================== ADD/EDIT HOLDING MODAL ====================

const AddHoldingModal = ({ isOpen, onClose, onSuccess, editingHolding }) => {
  const [formData, setFormData] = useState({
    symbol: '',
    quantity: '',
    purchase_price: '',
    purchase_date: new Date().toISOString().split('T')[0],
    notes: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (editingHolding) {
      setFormData({
        symbol: editingHolding.symbol,
        quantity: editingHolding.quantity,
        purchase_price: editingHolding.purchase_price,
        purchase_date: editingHolding.purchase_date?.split('T')[0] || new Date().toISOString().split('T')[0],
        notes: editingHolding.notes || ''
      });
    } else {
      // Reset form for new holding
      setFormData({
        symbol: '',
        quantity: '',
        purchase_price: '',
        purchase_date: new Date().toISOString().split('T')[0],
        notes: ''
      });
    }
    setError('');
  }, [editingHolding]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.symbol.trim()) {
      setError('Please select a stock symbol');
      return;
    }
    
    try {
      setSubmitting(true);
      const token = getToken();
      const url = editingHolding 
        ? `http://localhost:5000/api/portfolio/${editingHolding.id}`
        : 'http://localhost:5000/api/portfolio';
      
      const response = await fetch(url, {
        method: editingHolding ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();

      if (response.ok) {
        onSuccess();
        onClose();
      } else {
        setError(data.error || 'Failed to save holding');
      }
    } catch (error) {
      console.error('Error saving holding:', error);
      setError('Network error. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">
            {editingHolding ? 'Edit' : 'Add'} Holding
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Stock Symbol Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Stock Symbol
            </label>
            <StockSearchDropdown
              value={formData.symbol}
              onChange={(symbol) => setFormData({...formData, symbol})}
              disabled={!!editingHolding}
            />
            {editingHolding && (
              <p className="mt-1 text-xs text-gray-500">
                Symbol cannot be changed when editing
              </p>
            )}
          </div>

          {/* Quantity */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Quantity
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              required
              value={formData.quantity}
              onChange={(e) => setFormData({...formData, quantity: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
              placeholder="10"
            />
          </div>

          {/* Purchase Price */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Purchase Price ($)
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              required
              value={formData.purchase_price}
              onChange={(e) => setFormData({...formData, purchase_price: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
              placeholder="150.00"
            />
          </div>

          {/* Purchase Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Purchase Date
            </label>
            <input
              type="date"
              required
              value={formData.purchase_date}
              onChange={(e) => setFormData({...formData, purchase_date: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes (Optional)
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
              rows="2"
              placeholder="Long-term hold, earnings play, etc."
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Saving...
                </>
              ) : (
                <>{editingHolding ? 'Update' : 'Add'} Holding</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Portfolio;