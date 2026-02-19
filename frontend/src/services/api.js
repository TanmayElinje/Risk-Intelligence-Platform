import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
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
  getStockExplanation: (symbol) => api.get(`/stock/${symbol}/explain`),
  
  // Alerts
  getAlerts: (params = {}) => api.get('/alerts', { params }),
  
  // Sentiment trends
  getSentimentTrends: (params = {}) => api.get('/sentiment-trends', { params }),
  
  // Top risks
  getTopRisks: (params = {}) => api.get('/top-risks', { params }),
  
  // Market features
  getMarketFeatures: (symbol, params = {}) => api.get(`/market-features/${symbol}`, { params }),
  
  // RAG query
  queryRAG: (query, stockSymbol = null, chatHistory = []) => {
    console.log('API: Sending RAG query:', { query, stock_symbol: stockSymbol, history_length: chatHistory.length });
    return api.post('/query-rag', { query, stock_symbol: stockSymbol, chat_history: chatHistory })
      .then(response => {
        console.log('API: RAG response received:', response);
        return response;
      })
      .catch(error => {
        console.error('API: RAG request failed:', error);
        throw error;
      });
  },
  
  // Risk history
  getRiskHistory: (params = {}) => api.get('/risk-history', { params }),
};

export default api;