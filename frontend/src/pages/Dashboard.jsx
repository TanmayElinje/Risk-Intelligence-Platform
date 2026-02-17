// frontend/src/pages/Dashboard.jsx - CORRECT API FORMAT
import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import RiskScoreTable from '../components/RiskScoreTable';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [riskScores, setRiskScores] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { lastMessage } = useWebSocket();

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (lastMessage?.type === 'stats_update') {
      setStats(lastMessage);
    }
  }, [lastMessage]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      const [statsRes, scoresRes, alertsRes] = await Promise.all([
        fetch('http://localhost:5000/api/stats'),
        fetch('http://localhost:5000/api/risk-scores'),
        fetch('http://localhost:5000/api/alerts?limit=10')
      ]);

      const statsData = await statsRes.json();
      const scoresData = await scoresRes.json();
      const alertsData = await alertsRes.json();

      setStats(statsData);
      
      // Handle the correct API format: {count: 50, data: [...]}
      if (scoresData.data && Array.isArray(scoresData.data)) {
        setRiskScores(scoresData.data);
      } else if (Array.isArray(scoresData)) {
        setRiskScores(scoresData);
      } else if (scoresData.risk_scores && Array.isArray(scoresData.risk_scores)) {
        setRiskScores(scoresData.risk_scores);
      } else {
        console.error('Unexpected scores data format:', scoresData);
        setRiskScores([]);
      }
      
      // Handle alerts - same format
      if (alertsData.data && Array.isArray(alertsData.data)) {
        setAlerts(alertsData.data);
      } else if (Array.isArray(alertsData)) {
        setAlerts(alertsData);
      } else if (alertsData.alerts && Array.isArray(alertsData.alerts)) {
        setAlerts(alertsData.alerts);
      } else {
        setAlerts([]);
      }
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setRiskScores([]);
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow p-6 transition-colors">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Risk Intelligence Dashboard
            </h1>
            <p className="text-gray-600 mt-2">
              Real-time market risk monitoring and analysis
              <span className="ml-2 text-green-600 font-medium">
                • Live Updates Active
              </span>
            </p>
          </div>
          <button className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors">
            AI Assistant
          </button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Scores Table */}
        <div className="lg:col-span-2">
          {loading ? (
            <div className="bg-white rounded-lg shadow p-12 text-center transition-colors">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-600 mt-4">Loading risk scores...</p>
            </div>
          ) : (
            <RiskScoreTable scores={riskScores} />
          )}
        </div>

        {/* Recent Alerts */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow overflow-hidden transition-colors">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Recent Alerts
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Latest 10 risk notifications
              </p>
            </div>

            <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
              {alerts.length === 0 ? (
                <p className="p-6 text-center text-gray-500">No alerts available</p>
              ) : (
                alerts.map((alert, index) => (
                  <div 
                    key={index} 
                    className="p-4 hover:bg-gray-50 transition-colors border-l-4 border-red-500"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
                          <svg className="w-5 h-5 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                        </div>
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h3 className="font-semibold text-gray-900">
                            {alert.symbol}
                          </h3>
                          <span className="text-xs text-gray-500">
                            {alert.days_ago} days ago
                          </span>
                        </div>
                        
                        <p className="text-sm text-gray-600 mb-2">
                          {alert.alert_type}
                        </p>
                        
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-500">
                            Risk: {alert.risk_score}%
                          </span>
                          <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded">
                            {alert.risk_level}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;