// frontend/src/services/watchlistService.js
import axios from 'axios';
import { getToken } from './authService';

const API_URL = 'http://localhost:5000/api/watchlist';

// Axios instance with auth header
const api = axios.create({
  baseURL: API_URL,
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Get user's watchlist
export const getWatchlist = async () => {
  const response = await api.get('');
  return response.data;
};

// Add stock to watchlist
export const addToWatchlist = async (symbol, notes = '') => {
  const response = await api.post('/add', { symbol, notes });
  return response.data;
};

// Remove from watchlist
export const removeFromWatchlist = async (watchlistStockId) => {
  const response = await api.delete(`/remove/${watchlistStockId}`);
  return response.data;
};

// Update watchlist notes
export const updateWatchlistNotes = async (watchlistStockId, notes) => {
  const response = await api.put(`/update/${watchlistStockId}`, { notes });
  return response.data;
};

// Check if stock is in watchlist
export const checkInWatchlist = async (symbol) => {
  const response = await api.get(`/check/${symbol}`);
  return response.data;
};