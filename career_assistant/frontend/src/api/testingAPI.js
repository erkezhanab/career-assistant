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
testingApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(
            `${API_URL}/auth/token/refresh/`,
            { refresh: refreshToken }
          );
          
          localStorage.setItem('access_token', response.data.access);
          originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
          
          return testingApi(originalRequest);
        }
      } catch (refreshError) {
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
addCertificate: (formData) => {
  return testingApi.post('/testing/documents/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
},
  deleteCertificate: (id) => testingApi.delete(`/testing/documents/${id}/`),

  // Статус тестирования
  getTestStatus: () => testingApi.get('/testing/status/'),

  // Управление тестами
  startTest: (data = {}) => testingApi.post('/testing/start/', data),

  getQuestion: (sessionId) => testingApi.get(`/testing/session/${sessionId}/question/`),
  getSessionStatus: (sessionId) => testingApi.get(`/testing/session/${sessionId}/status/`),

  submitAnswer: (sessionId, questionId, answer) => {
    // Поддержка одиночного и множественного выбора
    let processedAnswer = answer;
    if (Array.isArray(answer)) {
      processedAnswer = answer;
    } else if (typeof answer === 'object' && answer !== null) {
      processedAnswer = Object.values(answer); // массив для multiple_choice
    }

    return testingApi.post('/testing/submit/', {
      session_id: sessionId,
      question_id: questionId,
      answer: processedAnswer
    });
  },

  completeTest: (sessionId) => testingApi.post('/testing/complete/', { session_id: sessionId }),

  getAvailableResumes: () => testingApi.get('/testing/available-resumes/'),

  // Результаты
  getTestResult: (testId) => testingApi.get(`/testing/results/${testId}/`),
  getTestHistory: () => testingApi.get('/testing/history/'),
};


export default testingService;