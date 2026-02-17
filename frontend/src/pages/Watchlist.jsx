// frontend/src/pages/Watchlist.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Star, Trash2, Edit2, Plus, TrendingUp, TrendingDown } from 'lucide-react';
import * as watchlistService from '../services/watchlistService';

const Watchlist = () => {
  const navigate = useNavigate();
  const [watchlist, setWatchlist] = useState(null);
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingNotes, setEditingNotes] = useState(null);
  const [notesText, setNotesText] = useState('');

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    try {
      setLoading(true);
      const data = await watchlistService.getWatchlist();
      setWatchlist(data.watchlist);
      setStocks(data.stocks);
    } catch (error) {
      console.error('Error fetching watchlist:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (watchlistStockId, symbol) => {
    if (!confirm(`Remove ${symbol} from watchlist?`)) return;

    try {
      await watchlistService.removeFromWatchlist(watchlistStockId);
      setStocks(stocks.filter(s => s.id !== watchlistStockId));
    } catch (error) {
      console.error('Error removing from watchlist:', error);
      alert('Failed to remove from watchlist');
    }
  };

  const handleStartEdit = (stock) => {
    setEditingNotes(stock.id);
    setNotesText(stock.notes || '');
  };

  const handleSaveNotes = async (watchlistStockId) => {
    try {
      await watchlistService.updateWatchlistNotes(watchlistStockId, notesText);
      setStocks(stocks.map(s => 
        s.id === watchlistStockId ? { ...s, notes: notesText } : s
      ));
      setEditingNotes(null);
    } catch (error) {
      console.error('Error updating notes:', error);
      alert('Failed to update notes');
    }
  };

  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'high':
        return 'text-red-600 bg-red-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'low':
        return 'text-green-600 bg-green-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getRiskIcon = (level) => {
    switch (level?.toLowerCase()) {
      case 'high':
      case 'medium':
        return <TrendingDown className="w-4 h-4" />;
      case 'low':
        return <TrendingUp className="w-4 h-4" />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Star className="w-8 h-8 text-yellow-500 fill-yellow-500" />
              My Watchlist
            </h1>
            <p className="text-gray-600 mt-2">
              {stocks.length} {stocks.length === 1 ? 'stock' : 'stocks'} tracked
            </p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Add Stocks
          </button>
        </div>
      </div>

      {/* Empty State */}
      {stocks.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Star className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Your watchlist is empty
          </h3>
          <p className="text-gray-600 mb-6">
            Start tracking stocks by adding them from the dashboard or stock details page
          </p>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Browse Stocks
          </button>
        </div>
      ) : (
        /* Watchlist Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {stocks.map((stock) => (
            <div
              key={stock.id}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6"
            >
              {/* Stock Header */}
              <div className="flex items-start justify-between mb-4">
                <div
                  className="cursor-pointer flex-1"
                  onClick={() => navigate(`/stock/${stock.symbol}`)}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {getRiskIcon(stock.risk_level)}
                    <h3 className="text-xl font-bold text-gray-900">
                      {stock.symbol}
                    </h3>
                  </div>
                  <p className="text-sm text-gray-600">{stock.name}</p>
                  {stock.sector && (
                    <p className="text-xs text-gray-500 mt-1">{stock.sector}</p>
                  )}
                </div>
                <button
                  onClick={() => handleRemove(stock.id, stock.symbol)}
                  className="text-gray-400 hover:text-red-600 transition-colors"
                  title="Remove from watchlist"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>

              {/* Risk Score */}
              {stock.risk_score && (
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Risk Score</span>
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded ${getRiskColor(
                        stock.risk_level
                      )}`}
                    >
                      {stock.risk_level}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        stock.risk_score > 0.6
                          ? 'bg-red-600'
                          : stock.risk_score > 0.4
                          ? 'bg-yellow-600'
                          : 'bg-green-600'
                      }`}
                      style={{ width: `${(stock.risk_score * 100).toFixed(0)}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {(stock.risk_score * 100).toFixed(1)}%
                  </p>
                </div>
              )}

              {/* Notes Section */}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Notes</span>
                  {editingNotes !== stock.id && (
                    <button
                      onClick={() => handleStartEdit(stock)}
                      className="text-gray-400 hover:text-blue-600 transition-colors"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
                {editingNotes === stock.id ? (
                  <div>
                    <textarea
                      value={notesText}
                      onChange={(e) => setNotesText(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      rows="3"
                      placeholder="Add your notes..."
                    />
                    <div className="flex gap-2 mt-2">
                      <button
                        onClick={() => handleSaveNotes(stock.id)}
                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingNotes(null)}
                        className="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-gray-600">
                    {stock.notes || (
                      <span className="text-gray-400 italic">No notes yet</span>
                    )}
                  </p>
                )}
              </div>

              {/* Added Date */}
              <p className="text-xs text-gray-400 mt-4">
                Added {new Date(stock.added_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Watchlist;