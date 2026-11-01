// Методы работы с аутентификацией.
//
// Этот слой скрывает адреса API от компонентов: страницам не нужно
// знать, по какому пути отправлять запрос — они просто вызывают
// authAPI.login(...). Если адрес на backend изменится,
// правка нужна только здесь.

import axiosInstance from './axiosConfig';

export const authAPI = {
  // Регистрация нового пользователя
  register: (userData) => axiosInstance.post('/auth/register/', userData),

  // Вход: в ответ приходят access- и refresh-токены
  login: (credentials) => axiosInstance.post('/auth/login/', credentials),

  // Выход выполняется только на стороне браузера: при JWT сервер
  // не хранит сессий, поэтому достаточно удалить токены локально
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },

  getProfile: () => axiosInstance.get('/auth/profile/'),
  updateProfile: (data) => axiosInstance.put('/auth/profile/', data),

  // PUT, а не POST: на backend это UpdateAPIView,
  // которое принимает только PUT и PATCH
  changePassword: (data) => axiosInstance.put('/auth/change-password/', data),

  // Новый метод для получения данных пользователя с проверкой профиля
  // Отличается от getProfile: возвращает ещё и права доступа
  // (is_superuser), по которым интерфейс показывает раздел админа
  getUserInfo: async () => {
    try {
      const response = await axiosInstance.get('/auth/user-info/');
      return response.data;
    } catch (error) {
      // Если профиль не найден, возвращаем базовые данные
      // Пустая «заготовка» вместо ошибки: интерфейс отрисуется,
      // пусть и без имени пользователя
      console.warn('Profile not found, returning basic user info');
      return {
        email: '',
        first_name: '',
        last_name: '',
        is_superuser: false
      };
    }
  },
};
