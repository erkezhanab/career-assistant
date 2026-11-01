// Методы работы с пробными собеседованиями.
//
// Порядок вызовов соответствует этапам интервью:
// generateInterview -> updateInterview (по ходу) -> completeInterview -> getInterviewFeedback

import axiosInstance from './axiosConfig';

export const interviewsAPI = {
  // Создание интервью: ИИ генерирует вопросы по резюме
  generateInterview: (data) => axiosInstance.post('/interviews/generate/', data),

  // История пройденных собеседований
  getUserInterviews: () => axiosInstance.get('/interviews/'),

  // Одно интервью с вопросами и ответами
  getInterviewDetails: (id) => axiosInstance.get(`/interviews/${id}/`),

  // Промежуточное сохранение ответов, без завершения интервью
  updateInterview: (id, data) => axiosInstance.put(`/interviews/${id}/`, data),

  // Завершение: отправляет все ответы, в ответ приходит разбор от ИИ
  completeInterview: (id, answers) => axiosInstance.post(`/interviews/${id}/complete/`, { answers }),

  // Повторный просмотр разбора ранее пройденного интервью
  getInterviewFeedback: (id) => axiosInstance.get(`/interviews/${id}/feedback/`),
};
