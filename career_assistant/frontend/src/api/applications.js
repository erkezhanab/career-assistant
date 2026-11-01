// Методы работы с откликами на вакансии.

import axiosInstance from './axiosConfig';

export const applicationsAPI = {
  // Отправка отклика: вакансия + текст письма
  apply: (data) => axiosInstance.post('/applications/apply/', data),

  // Генерация сопроводительного письма через ИИ.
  // Отдельный запрос от apply: сначала пользователь получает письмо,
  // правит его при необходимости и только потом отправляет отклик
  generateCoverLetter: (data) => axiosInstance.post('/applications/generate-letter/', data),

  // Список моих откликов
  getUserApplications: () => axiosInstance.get('/applications/'),

  // PATCH, а не PUT: меняется только одно поле (статус),
  // остальные данные отклика передавать не нужно
  updateApplicationStatus: (id, status) => axiosInstance.patch(`/applications/${id}/`, { status }),
};
