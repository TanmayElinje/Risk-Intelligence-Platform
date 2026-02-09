import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API methods
export const apiService = {
  // Health check
  healthCheck: () => api.get('/health'),
  
  // Stats
  getStats: () => api.get('/stats'),
  
  // Risk scores
  getRiskScores: (params = {}) => api.get('/risk-scores', { params }),
  
  // Stock details
  getStockDetails: (symbol) => api.get(`/stock/${symbol}`),
  
  // Alerts
  getAlerts: (params = {}) => api.get('/alerts', { params }),
  
  // Sentiment trends
  getSentimentTrends: (params = {}) => api.get('/sentiment-trends', { params }),
  
  // Top risks
  getTopRisks: (params = {}) => api.get('/top-risks', { params }),
  
  // Market features
  getMarketFeatures: (symbol, params = {}) => api.get(`/market-features/${symbol}`, { params }),
  
  // RAG query
  queryRAG: (query, stockSymbol = null) => api.post('/query-rag', { query, stock_symbol: stockSymbol }),
  
  // Risk history
  getRiskHistory: (params = {}) => api.get('/risk-history', { params }),
};

export default api;