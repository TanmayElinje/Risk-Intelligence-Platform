// frontend/src/components/WatchlistButton.jsx
import React, { useState, useEffect } from 'react';
import { Star } from 'lucide-react';
import * as watchlistService from '../services/watchlistService';

const WatchlistButton = ({ symbol, className = '' }) => {
  const [inWatchlist, setInWatchlist] = useState(false);
  const [watchlistStockId, setWatchlistStockId] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    checkWatchlist();
  }, [symbol]);

  const checkWatchlist = async () => {
    try {
      const data = await watchlistService.checkInWatchlist(symbol);
      setInWatchlist(data.in_watchlist);
      setWatchlistStockId(data.watchlist_stock_id);
    } catch (error) {
      console.error('Error checking watchlist:', error);
    }
  };

  const handleToggle = async () => {
    setLoading(true);
    try {
      if (inWatchlist) {
        // Remove from watchlist
        await watchlistService.removeFromWatchlist(watchlistStockId);
        setInWatchlist(false);
        setWatchlistStockId(null);
      } else {
        // Add to watchlist
        const data = await watchlistService.addToWatchlist(symbol);
        setInWatchlist(true);
        setWatchlistStockId(data.watchlist_stock.id);
      }
    } catch (error) {
      console.error('Error toggling watchlist:', error);
      alert(error.response?.data?.error || 'Failed to update watchlist');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleToggle}
      disabled={loading}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all disabled:opacity-50 ${
        inWatchlist
          ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      } ${className}`}
      title={inWatchlist ? 'Remove from watchlist' : 'Add to watchlist'}
    >
      <Star
        className={`w-5 h-5 ${inWatchlist ? 'fill-yellow-500 text-yellow-500' : ''}`}
      />
      {loading ? 'Loading...' : inWatchlist ? 'In Watchlist' : 'Add to Watchlist'}
    </button>
  );
};

export default WatchlistButton;