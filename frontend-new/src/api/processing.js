import { apiClient, getTasksClientId } from './base'

export const processingApi = {
  processVideo: (d) => apiClient.post('/api/process-video', d),
  processVideoWithClient: (d, clientId = getTasksClientId()) => apiClient.post(`/api/process-video/${clientId}`, d),
  getTaskStatus: (id) => apiClient.get(`/api/task/${id}`),
  getAllTasks: () => apiClient.get('/api/all-tasks'),
  getClientTasks: (clientId = getTasksClientId()) => apiClient.get(`/api/tasks/${clientId}`),
  getLastResult: (clientId = getTasksClientId()) => apiClient.get(`/api/last-result/${clientId}`),
  uploadVideoFile: (fd, cfg = {}) => apiClient.post('/api/admin/upload-video-file', fd, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 600000, ...cfg }),

  exportQuestions: (tid) => apiClient.get(`/api/export/${tid}`),
  exportCSV: () => apiClient.get('/api/admin/export-csv', { responseType: 'blob' }),
  getTranscript: (tid) => apiClient.get(`/api/transcript/${tid}`),
  getFullExport: (tid) => apiClient.get(`/api/full-export/${tid}`),
  getHealth: () => apiClient.get('/health')
}
