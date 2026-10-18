import axiosInstance from './axiosConfig';

export const adminAPI = {
  // Пользователи
  getUsers: (params) => axiosInstance.get('/auth/admin/users/', { params }),
  getUserById: (id) => axiosInstance.get(`/auth/admin/users/${id}/`),
  updateUser: (id, data) => axiosInstance.patch(`/auth/admin/users/${id}/`, data),
  toggleUserActive: (id) => axiosInstance.post(`/auth/admin/users/${id}/toggle-active/`),
  
  // Статистика
  getStats: () => axiosInstance.get('/auth/admin/stats/'),
  
  // Проверка прав админа
  checkAdmin: () => axiosInstance.get('/auth/admin/check/') // Создадим позже
};