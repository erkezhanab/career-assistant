// Методы работы с тестированием знаний.
//
// Особенность файла: здесь создаётся СВОЙ экземпляр axios, а не
// используется общий из axiosConfig.js. Причина — исторически этот
// модуль разрабатывался отдельно. Логика интерцепторов такая же:
// подстановка токена и его обновление при истечении срока.

import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Создаем экземпляр axios
const testingApi = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерцептор для добавления токена
// Выполняется перед каждым запросом: подставляет JWT-токен
testingApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Интерцептор для обработки ошибок
// Если токен просрочен (401), запрашивает новый и повторяет запрос
testingApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // _retry защищает от бесконечного цикла обновления токена
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          // Чистый axios, а не testingApi: иначе интерцептор
          // вызвал бы сам себя рекурсивно
          const response = await axios.post(
            `${API_URL}/auth/token/refresh/`,
            { refresh: refreshToken }
          );

          localStorage.setItem('access_token', response.data.access);
          originalRequest.headers.Authorization = `Bearer ${response.data.access}`;

          // Повторяем исходный запрос с новым токеном
          return testingApi(originalRequest);
        }
      } catch (refreshError) {
        // Refresh-токен тоже недействителен — выход из системы
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Методы API
export const testingService = {
  // Категории тестов
  getCategories: () => testingApi.get('/testing/categories/'),

  // Документы
  getCertificates: () => testingApi.get('/testing/documents/'),

  // Загрузка документа со сканом: заголовок multipart/form-data
  // указывается явно, так как у этого экземпляра axios по умолчанию
  // стоит application/json, который файлы передать не может
  addCertificate: (formData) => {
    return testingApi.post('/testing/documents/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  deleteCertificate: (id) => testingApi.delete(`/testing/documents/${id}/`),

  // Статус тестирования
  // Можно ли начать тест, когда доступна пересдача, прошлый результат
  getTestStatus: () => testingApi.get('/testing/status/'),

  // Управление тестами
  // Запуск: ИИ генерирует вопросы по резюме пользователя
  startTest: (data = {}) => testingApi.post('/testing/start/', data),

  // Очередной неотвеченный вопрос
  getQuestion: (sessionId) => testingApi.get(`/testing/session/${sessionId}/question/`),

  // Готовы ли вопросы (опрашивается, пока идёт генерация)
  getSessionStatus: (sessionId) => testingApi.get(`/testing/session/${sessionId}/status/`),

  submitAnswer: (sessionId, questionId, answer) => {
    // Поддержка одиночного и множественного выбора
    // Ответ приводится к виду, который ожидает backend:
    // строка для одного варианта, массив для нескольких
    let processedAnswer = answer;
    if (Array.isArray(answer)) {
      processedAnswer = answer;
    } else if (typeof answer === 'object' && answer !== null) {
      // Объект вида {0: 'A', 1: 'B'} превращаем в массив ['A', 'B']
      processedAnswer = Object.values(answer); // массив для multiple_choice
    }

    return testingApi.post('/testing/submit/', {
      session_id: sessionId,
      question_id: questionId,
      answer: processedAnswer
    });
  },

  // Завершение теста: сервер считает баллы и возвращает разбор
  completeTest: (sessionId) => testingApi.post('/testing/complete/', { session_id: sessionId }),

  // Резюме, по которым можно составить тест
  getAvailableResumes: () => testingApi.get('/testing/available-resumes/'),

  // Результаты
  getTestResult: (testId) => testingApi.get(`/testing/results/${testId}/`),
  getTestHistory: () => testingApi.get('/testing/history/'),
};


export default testingService;
