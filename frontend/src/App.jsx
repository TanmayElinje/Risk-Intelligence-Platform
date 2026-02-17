// frontend/src/App.jsx - WITH STOCK COMPARISON
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AlertNotifier from './components/AlertNotifier';

// Auth Pages
import Login from './pages/Login';
import Signup from './pages/Signup';

// Protected Pages
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Alerts from './pages/Alerts';
import StockDetails from './pages/StockDetails';
import RAGChat from './pages/RAGChat';
import Watchlist from './pages/Watchlist';
import Settings from './pages/Settings';
import StockComparison from './pages/StockComparison';  // ← NEW IMPORT
import Portfolio from './pages/Portfolio';  // ← PORTFOLIO IMPORT
import HistoricalData from './pages/HistoricalData';  // ← HISTORICAL DATA IMPORT
import AdvancedAnalytics from './pages/AdvancedAnalytics';  // ← ADVANCED ANALYTICS IMPORT
import Backtesting from './pages/Backtesting';  // ← BACKTESTING IMPORT

function App() {
  return (
    <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            {/* Protected Routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AlertNotifier />
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="alerts" element={<Alerts />} />
              <Route path="watchlist" element={<Watchlist />} />
              <Route path="comparison" element={<StockComparison />} />  {/* ← NEW ROUTE */}
              <Route path="portfolio" element={<Portfolio />} />  {/* ← PORTFOLIO ROUTE */}
              <Route path="historical" element={<HistoricalData />} />  {/* ← HISTORICAL DATA ROUTE */}
              <Route path="advanced-analytics" element={<AdvancedAnalytics />} />  {/* ← ADVANCED ANALYTICS ROUTE */}
              <Route path="backtesting" element={<Backtesting />} />  {/* ← BACKTESTING ROUTE */}
              <Route path="settings" element={<Settings />} />
              <Route path="stock/:symbol" element={<StockDetails />} />
              <Route path="chat" element={<RAGChat />} />
            </Route>

            {/* Catch all - redirect to dashboard */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
    </BrowserRouter>
  );
}

export default App;