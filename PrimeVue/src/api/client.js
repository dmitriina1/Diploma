import { API_BASE_URL, apiClient, getTasksClientId, getUserSession, getWebSocketUrl } from './base'
import { authApi } from './auth'
import { processingApi } from './processing'
import { questionsApi } from './questions'
import { trainerApi } from './trainer'
import { contentApi } from './content'
import { adminApi } from './admin'
import { chatApi } from './chat'

const api = {
  API_BASE_URL,
  apiClient,
  getUserSession,
  getTasksClientId,
  getWebSocketUrl,

  ...authApi,
  ...processingApi,
  ...questionsApi,
  ...trainerApi,
  ...contentApi,
  ...adminApi,
  ...chatApi,

  getPublicStats: () => apiClient.get('/api/stats'),
  exportJSON: () => adminApi.getAdminQuestions()
}

export default api
