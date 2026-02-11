import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import {
  BarChart, Bar, PieChart, Pie, Cell, ScatterChart, Scatter,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer
} from 'recharts';

const Analytics = () => {
  const [loading, setLoading] = useState(true);
  const [riskScores, setRiskScores] = useState([]);
  const [sentimentTrends, setSentimentTrends] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      const [scoresRes, sentimentRes, statsRes] = await Promise.all([
        apiService.getRiskScores(),
        apiService.getSentimentTrends({ days: 30 }),
        apiService.getStats(),
      ]);

      setRiskScores(scoresRes.data.data);
      setSentimentTrends(sentimentRes.data.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to load analytics data:', error);
      toast.error('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  // Prepare data for charts
  const riskDistribution = [
    { name: 'Low Risk', value: stats.low_risk_stocks, color: '#10b981' },
    { name: 'Medium Risk', value: stats.medium_risk_stocks, color: '#f59e0b' },
    { name: 'High Risk', value: stats.high_risk_stocks, color: '#ef4444' },
  ];

  const topRiskyStocks = riskScores.slice(0, 10);

  // Risk vs Sentiment scatter data
  const scatterData = riskScores.map(stock => ({
    symbol: stock.symbol,
    risk: stock.risk_score,
    sentiment: stock.avg_sentiment || 0,
  }));

  // Component contributions
  const componentData = riskScores.slice(0, 10).map(stock => ({
    symbol: stock.symbol,
    volatility: stock.norm_volatility || 0,
    drawdown: stock.norm_drawdown || 0,
    sentiment: stock.norm_sentiment || 0,
    liquidity: stock.norm_liquidity || 0,
  }));

  // Sentiment trend aggregation
  const sentimentByDate = {};
  sentimentTrends.forEach(item => {
    const date = new Date(item.date).toLocaleDateString();
    if (!sentimentByDate[date]) {
      sentimentByDate[date] = { date, total: 0, count: 0 };
    }
    sentimentByDate[date].total += item.avg_sentiment;
    sentimentByDate[date].count += 1;
  });

  const sentimentChartData = Object.values(sentimentByDate)
    .map(item => ({
      date: item.date,
      avg_sentiment: item.total / item.count,
    }))
    .slice(-14); // Last 14 days

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Advanced Analytics</h1>
        <p className="text-gray-600 mt-1">Deep dive into risk metrics and trends</p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <p className="text-sm text-gray-500">Total Stocks Analyzed</p>
          <p className="text-3xl font-bold mt-1">{stats.total_stocks}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Avg Risk Score</p>
          <p className="text-3xl font-bold mt-1">{stats.avg_risk_score?.toFixed(3)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Avg Sentiment</p>
          <p className="text-3xl font-bold mt-1">{stats.avg_sentiment?.toFixed(3)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">High Risk %</p>
          <p className="text-3xl font-bold mt-1 text-red-600">
            {((stats.high_risk_stocks / stats.total_stocks) * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution Pie Chart */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Risk Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={riskDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {riskDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top 10 Risky Stocks Bar Chart */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Top 10 Risky Stocks</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topRiskyStocks}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="symbol" />
              <YAxis domain={[0, 1]} />
              <Tooltip />
              <Bar dataKey="risk_score" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Risk vs Sentiment Scatter */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Risk vs Sentiment Correlation</h2>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="sentiment" name="Sentiment" domain={[-1, 1]} />
              <YAxis dataKey="risk" name="Risk Score" domain={[0, 1]} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter name="Stocks" data={scatterData} fill="#3b82f6" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Sentiment Trend */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Sentiment Trend (14 Days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={sentimentChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={[-1, 1]} />
              <Tooltip />
              <Line type="monotone" dataKey="avg_sentiment" stroke="#10b981" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Component Breakdown */}
        <div className="card lg:col-span-2">
          <h2 className="text-xl font-bold mb-4">Risk Component Breakdown (Top 10 Stocks)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={componentData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="symbol" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="volatility" stackId="a" fill="#8b5cf6" name="Volatility" />
              <Bar dataKey="drawdown" stackId="a" fill="#ef4444" name="Drawdown" />
              <Bar dataKey="sentiment" stackId="a" fill="#f59e0b" name="Sentiment" />
              <Bar dataKey="liquidity" stackId="a" fill="#3b82f6" name="Liquidity" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Table */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Risk Metrics Table</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Volatility</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Drawdown</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Sentiment</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Level</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {riskScores.slice(0, 20).map((stock) => (
                <tr key={stock.symbol} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-medium">{stock.symbol}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{stock.risk_score?.toFixed(3)}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{stock.volatility_21d?.toFixed(3)}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{stock.max_drawdown?.toFixed(2)}%</td>
                  <td className="px-6 py-4 whitespace-nowrap">{stock.avg_sentiment?.toFixed(3)}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`badge badge-${stock.risk_level?.toLowerCase()}`}>
                      {stock.risk_level}
                    </span>
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

export default Analytics;