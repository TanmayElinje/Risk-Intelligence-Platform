import { Link, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { apiService } from '../services/api';

const Layout = ({ children }) => {
  const location = useLocation();
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      const response = await apiService.getStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/alerts', label: 'Alerts', icon: '🚨', badge: stats?.total_alerts },
    { path: '/analytics', label: 'Analytics', icon: '📈' },
    { path: '/ask', label: 'AI Assistant', icon: '🤖' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="text-2xl">🧠</div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Risk Intelligence Platform
                </h1>
                <p className="text-xs text-gray-500">AI-Powered Financial Risk Monitoring</p>
              </div>
            </div>

            {!isLoading && stats && (
              <div className="flex items-center space-x-6 text-sm">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">{stats.high_risk_stocks}</div>
                  <div className="text-gray-500">High Risk</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">{stats.medium_risk_stocks}</div>
                  <div className="text-gray-500">Medium</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{stats.low_risk_stocks}</div>
                  <div className="text-gray-500">Low Risk</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`
                    flex items-center space-x-2 py-4 border-b-2 transition-colors
                    ${isActive
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                    }
                  `}
                >
                  <span>{item.icon}</span>
                  <span className="font-medium">{item.label}</span>
                  {item.badge > 0 && (
                    <span className="bg-red-600 text-white text-xs px-2 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center text-sm text-gray-500">
            <p>© 2026 Risk Intelligence Platform</p>
            {stats && (
              <p>Last updated: {new Date(stats.last_updated).toLocaleTimeString()}</p>
            )}
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;