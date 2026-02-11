import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import { formatDistanceToNow } from 'date-fns';

const Alerts = () => {
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState('all'); // all, high, medium
  const [sortBy, setSortBy] = useState('recent'); // recent, symbol

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const response = await apiService.getAlerts({ limit: 100 });
      setAlerts(response.data.data);
    } catch (error) {
      console.error('Failed to load alerts:', error);
      toast.error('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'all') return true;
    return alert.severity?.toLowerCase() === filter;
  });

  const sortedAlerts = [...filteredAlerts].sort((a, b) => {
    if (sortBy === 'recent') {
      return new Date(b.timestamp) - new Date(a.timestamp);
    } else {
      return a.symbol.localeCompare(b.symbol);
    }
  });

  const stats = {
    total: alerts.length,
    high: alerts.filter(a => a.severity === 'HIGH').length,
    medium: alerts.filter(a => a.severity === 'MEDIUM').length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading alerts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Risk Alerts</h1>
          <p className="text-gray-600 mt-1">Monitor and manage risk alerts across your portfolio</p>
        </div>
        <button
          onClick={loadAlerts}
          className="btn btn-primary"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Alerts</p>
              <p className="text-3xl font-bold mt-1">{stats.total}</p>
            </div>
            <div className="text-4xl">🔔</div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">High Severity</p>
              <p className="text-3xl font-bold mt-1 text-red-600">{stats.high}</p>
            </div>
            <div className="text-4xl">🚨</div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Medium Severity</p>
              <p className="text-3xl font-bold mt-1 text-yellow-600">{stats.medium}</p>
            </div>
            <div className="text-4xl">⚠️</div>
          </div>
        </div>
      </div>

      {/* Filters and Sort */}
      <div className="card">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Filter:</label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Alerts</option>
              <option value="high">High Severity</option>
              <option value="medium">Medium Severity</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Sort by:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="recent">Most Recent</option>
              <option value="symbol">Stock Symbol</option>
            </select>
          </div>

          <div className="ml-auto text-sm text-gray-500">
            Showing {sortedAlerts.length} of {alerts.length} alerts
          </div>
        </div>
      </div>

      {/* Alerts Timeline */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Alert Timeline</h2>
        
        {sortedAlerts.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">✅</div>
            <p className="text-xl font-semibold text-gray-700">No alerts found</p>
            <p className="text-gray-500 mt-2">All stocks are within acceptable risk levels</p>
          </div>
        ) : (
          <div className="space-y-4">
            {sortedAlerts.map((alert, idx) => (
              <div
                key={idx}
                className={`border-l-4 p-4 rounded-r-lg ${
                  alert.severity === 'HIGH'
                    ? 'border-red-500 bg-red-50'
                    : 'border-yellow-500 bg-yellow-50'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center space-x-3">
                    <Link
                      to={`/stock/${alert.symbol}`}
                      className={`text-xl font-bold ${
                        alert.severity === 'HIGH' ? 'text-red-700' : 'text-yellow-700'
                      } hover:underline`}
                    >
                      {alert.symbol}
                    </Link>
                    <span className={`badge ${
                      alert.severity === 'HIGH' ? 'badge-high' : 'badge-medium'
                    }`}>
                      {alert.severity}
                    </span>
                    <span className="badge bg-gray-200 text-gray-700">
                      {alert.alert_type?.replace('_', ' ')}
                    </span>
                  </div>
                  
                  <div className="text-right text-sm text-gray-600">
                    {alert.timestamp && formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                  <div>
                    <p className="text-xs text-gray-500">Risk Score</p>
                    <p className="text-lg font-semibold">{alert.risk_score?.toFixed(3)}</p>
                  </div>
                  
                  {alert.risk_change && (
                    <div>
                      <p className="text-xs text-gray-500">Risk Change</p>
                      <p className="text-lg font-semibold text-red-600">
                        +{alert.risk_change?.toFixed(3)} ({alert.risk_change_pct?.toFixed(1)}%)
                      </p>
                    </div>
                  )}
                  
                  <div>
                    <p className="text-xs text-gray-500">Risk Level</p>
                    <p className="text-lg font-semibold">{alert.risk_level}</p>
                  </div>
                </div>

                <div className="mb-3">
                  <p className="text-sm font-semibold text-gray-700 mb-1">Risk Drivers:</p>
                  <p className="text-sm text-gray-600">{alert.risk_drivers}</p>
                </div>

                {alert.explanation && (
                  <div className="bg-white bg-opacity-50 p-3 rounded border border-gray-200">
                    <p className="text-sm font-semibold text-gray-700 mb-1">Explanation:</p>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{alert.explanation}</p>
                  </div>
                )}

                <div className="mt-3 flex space-x-2">
                  <Link
                    to={`/stock/${alert.symbol}`}
                    className="btn btn-primary text-sm"
                  >
                    View Details →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Alerts;