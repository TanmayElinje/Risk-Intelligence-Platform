// frontend/src/services/authService.js
import axios from 'axios';

const API_URL = 'http://localhost:5000/api/auth';
const TOKEN_KEY = 'auth_token';

// Axios instance with auth header
const api = axios.create({
  baseURL: API_URL,
});

// Add token to requests automatically
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

// Token management
export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

export const setToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token);
};

export const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY);
};

// Auth API calls
export const login = async (username, password) => {
  const response = await api.post('/login', { username, password });
  if (response.data.token) {
    setToken(response.data.token);
  }
  return response.data;
};

export const signup = async (username, email, password, fullName) => {
  const response = await api.post('/signup', {
    username,
    email,
    password,
    full_name: fullName
  });
  if (response.data.token) {
    setToken(response.data.token);
  }
  return response.data;
};

export const logout = () => {
  removeToken();
};

export const verifyToken = async () => {
  const response = await api.get('/verify-token');
  return response.data.user;
};

export const getCurrentUser = async () => {
  const response = await api.get('/me');
  return response.data.user;
};

export const updateProfile = async (data) => {
  const response = await api.put('/update-profile', data);
  return response.data;
};

export const changePassword = async (currentPassword, newPassword) => {
  const response = await api.post('/change-password', {
    current_password: currentPassword,
    new_password: newPassword
  });
  return response.data;
};

// Helper to check if token exists
export const isAuthenticated = () => {
  return !!getToken();
};