import axiosInstance from './axiosConfig';


export const resumesAPI = {
  uploadResume: (formData) =>
    axiosInstance.post('/resumes/upload/', formData),

  getUserResumes: () => axiosInstance.get('/resumes/'),
  getResumeAnalysis: (id) => axiosInstance.get(`/resumes/${id}/analysis/`),
  deleteResume: (id) => axiosInstance.delete(`/resumes/${id}/`),
};