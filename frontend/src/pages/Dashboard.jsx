import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import RiskHeatmap from '../components/RiskHeatmap';
import StatsCards from '../components/StatsCards';
import AlertsFeed from '../components/AlertsFeed';
import SearchBar from '../components/SearchBar';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [riskScores, setRiskScores] = useState([]);
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [scoresRes, statsRes, alertsRes] = await Promise.all([
        apiService.getRiskScores(),
        apiService.getStats(),
        apiService.getAlerts({ limit: 10 }),
      ]);

      setRiskScores(scoresRes.data.data);
      setStats(statsRes.data);
      setAlerts(alertsRes.data.data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search */}
      <SearchBar stocks={riskScores} />

      {/* Stats Cards */}
      <StatsCards stats={stats} />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Heatmap - Takes 2 columns */}
        <div className="lg:col-span-2">
          <RiskHeatmap data={riskScores} />
        </div>

        {/* Alerts Feed - Takes 1 column */}
        <div>
          <AlertsFeed alerts={alerts} />
        </div>
      </div>

      {/* Top Risky Stocks Table */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Top Risky Stocks</h2>
          <Link to="/analytics" className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            View All →
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rank</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Level</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk Drivers</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {riskScores.slice(0, 10).map((stock) => (
                <tr key={stock.symbol} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    #{stock.risk_rank}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link to={`/stock/${stock.symbol}`} className="text-blue-600 hover:text-blue-800 font-medium">
                      {stock.symbol}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="text-sm font-medium text-gray-900">
                        {stock.risk_score?.toFixed(3)}
                      </div>
                      <div className="ml-2 w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            stock.risk_level === 'High' ? 'bg-red-600' :
                            stock.risk_level === 'Medium' ? 'bg-yellow-600' : 'bg-green-600'
                          }`}
                          style={{ width: `${stock.risk_score * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`badge badge-${stock.risk_level?.toLowerCase()}`}>
                      {stock.risk_level}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {stock.risk_drivers?.substring(0, 50)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <Link to={`/stock/${stock.symbol}`} className="text-blue-600 hover:text-blue-800">
                      Details →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;