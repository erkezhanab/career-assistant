import axiosInstance from './axiosConfig';
export const authAPI = {
  register: (userData) => axiosInstance.post('/auth/register/', userData),
  login: (credentials) => axiosInstance.post('/auth/login/', credentials),
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
  getProfile: () => axiosInstance.get('/auth/profile/'),
  updateProfile: (data) => axiosInstance.put('/auth/profile/', data),
  changePassword: (data) => axiosInstance.post('/auth/change-password/', data),
  
  // Новый метод для получения данных пользователя с проверкой профиля
  getUserInfo: async () => {
    try {
      const response = await axiosInstance.get('/auth/user-info/');
      return response.data;
    } catch (error) {
      // Если профиль не найден, возвращаем базовые данные
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