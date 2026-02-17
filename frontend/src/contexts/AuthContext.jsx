// frontend/src/contexts/AuthContext.jsx
import React, { createContext, useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import * as authService from '../services/authService';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // Check if user is logged in on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = authService.getToken();
      if (token) {
        // Verify token and get user
        const userData = await authService.verifyToken();
        setUser(userData);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      authService.removeToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      setError(null);
      const response = await authService.login(username, password);
      setUser(response.user);
      navigate('/');
      return response;
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Login failed';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const signup = async (username, email, password, fullName) => {
    try {
      setError(null);
      const response = await authService.signup(username, email, password, fullName);
      setUser(response.user);
      navigate('/');
      return response;
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Signup failed';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    navigate('/login');
  };

  const updateProfile = async (data) => {
    try {
      setError(null);
      const response = await authService.updateProfile(data);
      setUser(response.user);
      return response;
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Update failed';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const changePassword = async (currentPassword, newPassword) => {
    try {
      setError(null);
      const response = await authService.changePassword(currentPassword, newPassword);
      return response;
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Password change failed';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const value = {
    user,
    loading,
    error,
    login,
    signup,
    logout,
    updateProfile,
    changePassword,
    isAuthenticated: !!user,
    isAdmin: user?.is_admin || false
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};