// frontend/src/components/Layout.jsx
import React, { useState, useEffect } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  BarChart3, 
  Bell, 
  Bot,
  LogOut,
  User,
  Settings,
  Star,
  Menu,
  Scale,
  Briefcase,
  LineChart,
  Atom,
  FlaskConical,
  ChevronDown
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import LiveRiskTicker from './LiveRiskTicker';
import MobileNav from './MobileNav';

const Layout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNavMenu, setShowNavMenu] = useState(false);
  const [showMobileNav, setShowMobileNav] = useState(false);
  const [riskStats, setRiskStats] = useState({ high: 0, medium: 0, low: 0 });

  const isActive = (path) => location.pathname === path;

  // Fetch real risk stats
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('http://localhost:5000/api/stats', {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        if (res.ok) {
          const data = await res.json();
          setRiskStats({
            high: data.high_risk_stocks || 0,
            medium: data.medium_risk_stocks || 0,
            low: data.low_risk_stocks || 0,
          });
        }
      } catch (e) { console.error('Failed to fetch risk stats:', e); }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: BarChart3 },
    { path: '/portfolio', label: 'Portfolio', icon: Briefcase },
    { path: '/watchlist', label: 'Watchlist', icon: Star },
    { path: '/comparison', label: 'Compare', icon: Scale },
    { path: '/historical', label: 'History', icon: LineChart },
    { path: '/advanced-analytics', label: 'Advanced Analytics', icon: Atom },
    { path: '/backtesting', label: 'Backtesting', icon: FlaskConical },
    { path: '/alerts', label: 'Alerts', icon: Bell },
    { path: '/chat', label: 'AI Assistant', icon: Bot },
  ];

  // Find the current page label for the dropdown button
  const currentPage = navItems.find(item => isActive(item.path)) || navItems[0];
  const CurrentIcon = currentPage.icon;

  const styles = {
    main: {
      backgroundColor: '#ffffff',
      minHeight: '100vh',
    },
    nav: {
      backgroundColor: 'rgb(255, 255, 255)',
      borderBottomColor: 'rgb(229, 231, 235)',
    },
    summaryBar: {
      backgroundColor: 'rgb(249, 250, 251)',
      borderTopColor: 'rgb(229, 231, 235)',
    },
    footer: {
      backgroundColor: '#ffffff',
      borderTopColor: 'rgb(229, 231, 235)',
    },
  };

  return (
    <div style={styles.main}>
      {/* Live Risk Ticker */}
      <div className="fixed top-0 w-full z-50">
        <LiveRiskTicker />
      </div>

      {/* Top Navigation */}
      <nav 
        style={styles.nav}
        className="border-b fixed w-full top-[40px] z-40"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Logo and Mobile Menu Button */}
            <div className="flex items-center gap-3">
              {/* Mobile Menu Button */}
              <button
                onClick={() => setShowMobileNav(true)}
                className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <Menu className="w-6 h-6 text-gray-600" />
              </button>

              {/* Logo */}
              <div className="flex-shrink-0 flex items-center">
                <div className="w-8 h-8 bg-gradient-to-br from-pink-500 to-purple-600 rounded-lg"></div>
                <div className="ml-3 hidden sm:block">
                  <h1 className="text-xl font-bold text-gray-900">
                    Risk Intelligence Platform
                  </h1>
                  <p className="text-xs text-gray-500">
                    AI-Powered Financial Risk Monitoring
                  </p>
                </div>
              </div>
            </div>

            {/* Right Side: Nav Dropdown + User Menu */}
            <div className="flex items-center gap-2">

              {/* Navigation Dropdown */}
              <div className="relative">
                <button
                  onClick={() => { setShowNavMenu(!showNavMenu); setShowUserMenu(false); }}
                  className={`hidden md:flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    showNavMenu ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <CurrentIcon className="w-4 h-4" />
                  {currentPage.label}
                  <ChevronDown className={`w-4 h-4 transition-transform ${showNavMenu ? 'rotate-180' : ''}`} />
                </button>

                {showNavMenu && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setShowNavMenu(false)} />
                    <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg py-1 z-20 border border-gray-200">
                      {navItems.map((item) => {
                        const Icon = item.icon;
                        const active = isActive(item.path);
                        return (
                          <Link
                            key={item.path}
                            to={item.path}
                            onClick={() => setShowNavMenu(false)}
                            className={`flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                              active
                                ? 'bg-blue-50 text-blue-600 font-semibold'
                                : 'text-gray-700 hover:bg-gray-50'
                            }`}
                          >
                            <Icon className="w-4 h-4" />
                            {item.label}
                          </Link>
                        );
                      })}
                      <div className="border-t border-gray-100 my-1" />
                      <Link
                        to="/settings"
                        onClick={() => setShowNavMenu(false)}
                        className={`flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                          isActive('/settings')
                            ? 'bg-blue-50 text-blue-600 font-semibold'
                            : 'text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        <Settings className="w-4 h-4" />
                        Settings
                      </Link>
                    </div>
                  </>
                )}
              </div>

              {/* User Menu */}
              <div className="relative">
                <button
                  onClick={() => { setShowUserMenu(!showUserMenu); setShowNavMenu(false); }}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <span className="text-white font-semibold text-sm">
                      {user?.username?.charAt(0).toUpperCase() || 'U'}
                    </span>
                  </div>
                  <span className="text-sm font-medium hidden lg:block text-gray-700">
                    {user?.username || 'User'}
                  </span>
                </button>

                {showUserMenu && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setShowUserMenu(false)} />
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 z-20 border border-gray-200">
                      <div className="px-4 py-2 border-b border-gray-100">
                        <p className="text-sm font-medium text-gray-900">{user?.username}</p>
                        <p className="text-xs text-gray-500">{user?.email}</p>
                      </div>
                      
                      <button
                        onClick={() => { setShowUserMenu(false); navigate('/watchlist'); }}
                        className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                      >
                        <Star className="w-4 h-4" />
                        My Watchlist
                      </button>
                      
                      <button
                        onClick={() => { setShowUserMenu(false); navigate('/settings'); }}
                        className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                      >
                        <Settings className="w-4 h-4" />
                        Settings
                      </button>
                      
                      <div className="border-t border-gray-100 mt-1"></div>
                      
                      <button
                        onClick={handleLogout}
                        className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                      >
                        <LogOut className="w-4 h-4" />
                        Logout
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Risk Summary Bar */}
        <div style={styles.summaryBar} className="border-t">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
            <div className="flex items-center justify-end gap-4 sm:gap-6 text-xs sm:text-sm">
              <div className="flex items-center gap-1 sm:gap-2">
                <span className="font-bold text-lg sm:text-2xl text-red-600">{riskStats.high}</span>
                <span className="text-gray-600">High Risk</span>
              </div>
              <div className="flex items-center gap-1 sm:gap-2">
                <span className="font-bold text-lg sm:text-2xl text-yellow-600">{riskStats.medium}</span>
                <span className="text-gray-600">Medium</span>
              </div>
              <div className="flex items-center gap-1 sm:gap-2">
                <span className="font-bold text-lg sm:text-2xl text-green-600">{riskStats.low}</span>
                <span className="text-gray-600">Low Risk</span>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation Drawer */}
      <MobileNav 
        isOpen={showMobileNav}
        onClose={() => setShowMobileNav(false)}
        navItems={navItems}
      />

      {/* Main Content */}
      <main className="pt-[148px] pb-8 min-h-screen">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>

      {/* Footer */}
      <footer style={styles.footer} className="border-t py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-center text-sm gap-2 text-gray-500">
            <p>© 2026 Risk Intelligence Platform</p>
            <p>Last updated: {new Date().toLocaleTimeString()}</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;