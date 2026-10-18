import axiosInstance from './axiosConfig';

export const applicationsAPI = {
  apply: (data) => axiosInstance.post('/applications/apply/', data),
  generateCoverLetter: (data) => axiosInstance.post('/applications/generate-letter/', data),
  getUserApplications: () => axiosInstance.get('/applications/'),
  updateApplicationStatus: (id, status) => axiosInstance.patch(`/applications/${id}/`, { status }),
};