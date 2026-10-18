import axiosInstance from './axiosConfig';

export const vacanciesAPI = {
  searchVacancies: (data) => axiosInstance.post('/vacancies/search/', data),
  getVacancies: (params) => axiosInstance.get('/vacancies/', { params }),
  getVacancyDetails: (id) => axiosInstance.get(`/vacancies/${id}/`),
};

