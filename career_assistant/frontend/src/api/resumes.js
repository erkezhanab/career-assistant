// Методы работы с резюме.

import axiosInstance from './axiosConfig';

export const resumesAPI = {
  // Загрузка файла резюме.
  // Принимает FormData (а не обычный объект), потому что только
  // этот формат позволяет передавать файлы. Заголовок
  // multipart/form-data браузер подставит сам
  uploadResume: (formData) =>
    axiosInstance.post('/resumes/upload/', formData),

  // Список всех резюме пользователя
  getUserResumes: () => axiosInstance.get('/resumes/'),

  // Результаты анализа ИИ по конкретному резюме.
  // Этот запрос повторяется периодически, пока статус 'pending',
  // так как анализ выполняется на сервере в фоне
  getResumeAnalysis: (id) => axiosInstance.get(`/resumes/${id}/analysis/`),

  // Удаление резюме (на сервере удаляется и сам файл)
  deleteResume: (id) => axiosInstance.delete(`/resumes/${id}/`),
};
