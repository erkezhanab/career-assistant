import axiosInstance from './axiosConfig';

export const interviewsAPI = {
  generateInterview: (data) => axiosInstance.post('/interviews/generate/', data),
  getUserInterviews: () => axiosInstance.get('/interviews/'),
  getInterviewDetails: (id) => axiosInstance.get(`/interviews/${id}/`),
  updateInterview: (id, data) => axiosInstance.put(`/interviews/${id}/`, data),
  completeInterview: (id, answers) => axiosInstance.post(`/interviews/${id}/complete/`, { answers }),
  getInterviewFeedback: (id) => axiosInstance.get(`/interviews/${id}/feedback/`),
};