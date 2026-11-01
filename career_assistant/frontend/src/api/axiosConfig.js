// Настройка HTTP-клиента axios — через него идут ВСЕ запросы к backend.
//
// Здесь решаются две задачи, которые иначе пришлось бы повторять
// в каждом компоненте:
//   1. автоматически подставлять JWT-токен в каждый запрос;
//   2. автоматически обновлять просроченный токен и повторять запрос.

import axios from 'axios';

// Адрес backend берётся из переменной окружения (файл .env),
// а если её нет — используется локальный сервер разработки.
// Благодаря этому при публикации проекта адрес меняется без правки кода
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Свой экземпляр axios: настройки действуют только на наши запросы
// и не влияют на другие части приложения
const axiosInstance = axios.create({
  baseURL: API_URL,
});

// ИНТЕРЦЕПТОР ЗАПРОСА — выполняется ПЕРЕД отправкой каждого запроса.
// Добавляет токен авторизации, чтобы backend понял, кто обращается
axiosInstance.interceptors.request.use(
  (config) => {
    // Токен хранится в localStorage и сохраняется после перезагрузки страницы
    const token = localStorage.getItem('access_token');
    if (token) {
      // Формат "Bearer <токен>" — его ожидает библиотека simplejwt на backend
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Интерцептор для обновления токена
// ИНТЕРЦЕПТОР ОТВЕТА — выполняется ПОСЛЕ получения ответа.
// Если токен просрочен (ошибка 401), пытается получить новый
// по refresh-токену и беззвучно повторяет исходный запрос,
// чтобы пользователя не выбрасывало из системы каждые сутки
axiosInstance.interceptors.response.use(
  // Успешный ответ пропускаем без изменений
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Флаг _retry защищает от бесконечного цикла: если повторный
    // запрос снова вернёт 401, обновление токена уже не запустится
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        // Запрос нового access-токена. Используется «чистый» axios,
        // а не axiosInstance — иначе интерцептор вызвал бы сам себя
        const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
          refresh: refreshToken
        });

        // Сохраняем новый токен и подставляем его в дальнейшие запросы
        localStorage.setItem('access_token', response.data.access);
        axiosInstance.defaults.headers.common['Authorization'] =
          `Bearer ${response.data.access}`;

        // Повторяем исходный запрос — для пользователя всё выглядит
        // так, будто ошибки не было
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        // Refresh-токен тоже просрочен (прошло больше 7 дней) —
        // остаётся только разлогинить и отправить на страницу входа
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Остальные ошибки передаём дальше — их обрабатывают сами компоненты
    return Promise.reject(error);
  }
);

export default axiosInstance;
