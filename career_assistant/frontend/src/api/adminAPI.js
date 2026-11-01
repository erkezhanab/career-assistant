// Методы административной панели.
//
// Все эти запросы доступны только суперпользователю: backend
// проверяет права через правило IsAdminUser и отвечает 403,
// если обращается обычный пользователь.

import axiosInstance from './axiosConfig';

export const adminAPI = {
  // Пользователи
  // params передаётся как строка запроса: ?search=...&is_active=true
  getUsers: (params) => axiosInstance.get('/auth/admin/users/', { params }),

  getUserById: (id) => axiosInstance.get(`/auth/admin/users/${id}/`),

  // PATCH меняет только переданные поля, остальные остаются как были
  updateUser: (id, data) => axiosInstance.patch(`/auth/admin/users/${id}/`, data),

  // Блокировка/разблокировка аккаунта (переключатель)
  toggleUserActive: (id) => axiosInstance.post(`/auth/admin/users/${id}/toggle-active/`),

  // Статистика
  // Сводные показатели для главной страницы админ-панели
  getStats: () => axiosInstance.get('/auth/admin/stats/'),
};
