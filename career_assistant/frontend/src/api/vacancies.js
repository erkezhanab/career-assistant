// Методы работы с вакансиями.

import axiosInstance from './axiosConfig';

export const vacanciesAPI = {
  // Поиск вакансий. POST, а не GET: параметров много
  // (должность, город, зарплата, список языков), и передавать их
  // в теле запроса удобнее, чем в адресной строке.
  // ВАЖНО: ответ может быть как массивом вакансий, так и объектом
  // с полем message (когда ничего не найдено) — компонент
  // обязан проверять тип через Array.isArray()
  searchVacancies: (data) => axiosInstance.post('/vacancies/search/', data),

  // Все сохранённые вакансии (загружаются при открытии страницы)
  getVacancies: (params) => axiosInstance.get('/vacancies/', { params }),

  // Подробности одной вакансии
  getVacancyDetails: (id) => axiosInstance.get(`/vacancies/${id}/`),
};
