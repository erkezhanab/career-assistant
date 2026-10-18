import React, { createContext, useState, useContext, useEffect } from 'react';
import { authAPI } from '../api/auth';
import { toast } from 'react-toastify';

const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const response = await authAPI.getProfile();
        setUser(response.data);
      } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
    }
    setLoading(false);
  };

  const login = async (email, password) => {
    try {
      const response = await authAPI.login({ email, password });
      
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
      
      const userResponse = await authAPI.getProfile();
      setUser(userResponse.data);
      
      toast.success('Вход выполнен успешно!');
      return { success: true };
    } catch (error) {
      toast.error(error.response?.data?.error || 'Ошибка входа');
      return { 
        success: false, 
        error: error.response?.data?.error || 'Ошибка входа' 
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);
      
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
      
      setUser(response.data.user);
      
      toast.success('Регистрация успешна!');
      return { success: true };
    } catch (error) {
      const errors = error.response?.data;
      if (errors) {
        Object.values(errors).forEach(errorArray => {
          errorArray.forEach(errorMessage => {
            toast.error(errorMessage);
          });
        });
      } else {
        toast.error('Ошибка регистрации');
      }
      return { 
        success: false, 
        error: error.response?.data || 'Ошибка регистрации' 
      };
    }
  };

  const logout = () => {
    authAPI.logout();
    setUser(null);
    toast.info('Вы вышли из системы');
    window.location.href = '/login';
  };

  const updateProfile = async (data) => {
    try {
      const response = await authAPI.updateProfile(data);
      setUser(response.data);
      toast.success('Профиль обновлен');
      return { success: true };
    } catch (error) {
      toast.error('Ошибка обновления профиля');
      return { success: false };
    }
  };

  const value = {
    user,
    login,
    register,
    logout,
    updateProfile,
    loading,
    checkAuth
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};