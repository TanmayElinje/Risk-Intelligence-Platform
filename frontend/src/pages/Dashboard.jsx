import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Activity,
  BarChart3
} from 'lucide-react';
import StatsCard from '../components/StatsCards';
import RiskScoreTable from '../components/RiskScoreTable';
import AlertsList from '../components/AlertsList';
import ConnectionStatus from '../components/ConnectionStatus';
import LiveAlertToast from '../components/LiveAlertToast';
import { useWebSocket } from '../hooks/useWebSocket';

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [riskScores, setRiskScores] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentAlert, setCurrentAlert] = useState(null);

  // WebSocket connection
  const {
    isConnected,
    stats: liveStats,
    latestAlert,
    riskUpdates
  } = useWebSocket();

  // Fetch initial data
  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Update stats from WebSocket
  useEffect(() => {
    if (liveStats) {
      setStats(prev => ({
        ...prev,
        total_stocks: liveStats.total_stocks,
        high_risk_stocks: liveStats.high_risk_stocks,
        recent_alerts_count: liveStats.recent_alerts_count
      }));
    }
  }, [liveStats]);

  // Handle new alerts from WebSocket
  useEffect(() => {
    if (latestAlert) {
      // Show toast notification
      setCurrentAlert(latestAlert);
      
      // Add to alerts list
      setAlerts(prev => [latestAlert, ...prev]);
    }
  }, [latestAlert]);

  // Update risk scores from WebSocket
  useEffect(() => {
    if (Object.keys(riskUpdates).length > 0) {
      setRiskScores(prev => {
        const updated = [...prev];
        Object.entries(riskUpdates).forEach(([symbol, update]) => {
          const index = updated.findIndex(s => s.symbol === symbol);
          if (index !== -1) {
            updated[index] = {
              ...updated[index],
              risk_score: update.risk_score,
              risk_level: update.risk_level,
              updated: true // Flag for animation
            };
          }
        });
        return updated;
      });

      // Remove update flag after animation
      setTimeout(() => {
        setRiskScores(prev =>
          prev.map(s => ({ ...s, updated: false }))
        );
      }, 1000);
    }
  }, [riskUpdates]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      // Fetch stats
      const statsRes = await fetch('http://localhost:5000/api/stats');
      const statsData = await statsRes.json();
      setStats(statsData);

      // Fetch risk scores
      const scoresRes = await fetch('http://localhost:5000/api/risk-scores');
      const scoresData = await scoresRes.json();
      setRiskScores(scoresData.data || scoresData);

      // Fetch recent alerts
      const alertsRes = await fetch('http://localhost:5000/api/alerts?limit=10');
      const alertsData = await alertsRes.json();
      setAlerts(alertsData.data || alertsData);

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Connection Status */}
      <ConnectionStatus isConnected={isConnected} />

      {/* Live Alert Toast */}
      {currentAlert && (
        <LiveAlertToast
          alert={currentAlert}
          onClose={() => setCurrentAlert(null)}
        />
      )}

      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Risk Intelligence Dashboard
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                Real-time market risk monitoring and analysis
                {isConnected && (
                  <span className="ml-2 text-green-600 font-medium">
                    • Live Updates Active
                  </span>
                )}
              </p>
            </div>
            <button
              onClick={() => navigate('/chat')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              AI Assistant
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="Total Stocks"
            value={stats?.total_stocks || 0}
            icon={<BarChart3 className="w-6 h-6" />}
            color="blue"
          />
          <StatsCard
            title="High Risk"
            value={stats?.high_risk_stocks || 0}
            icon={<TrendingDown className="w-6 h-6" />}
            color="red"
            subtitle={`${((stats?.high_risk_stocks / stats?.total_stocks) * 100 || 0).toFixed(1)}% of portfolio`}
          />
          <StatsCard
            title="Active Alerts"
            value={stats?.recent_alerts_count || 0}
            icon={<AlertTriangle className="w-6 h-6" />}
            color="yellow"
          />
          <StatsCard
            title="Avg Risk Score"
            value={stats?.avg_risk_score?.toFixed(2) || '0.00'}
            icon={<Activity className="w-6 h-6" />}
            color="purple"
          />
        </div>

        {/* Risk Scores Table and Alerts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <RiskScoreTable scores={riskScores} />
          </div>
          <div>
            <AlertsList alerts={alerts} />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;