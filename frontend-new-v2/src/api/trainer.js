import { apiClient, getUserSession } from './base'

export const trainerApi = {
  getSM2Cards: (p = {}) => apiClient.get(`/api/trainer/sm2-cards/${getUserSession()}`, { params: p }),
  submitSM2Review: (qid, q) => apiClient.post('/api/trainer/sm2-review', { question_id: qid, user_session: getUserSession(), quality: q }),
  resetSM2Progress: () => apiClient.delete(`/api/trainer/sm2-reset/${getUserSession()}`),

  startMockInterview: (d) => apiClient.post('/api/mock-interview/start', { ...d, user_session: getUserSession() }),
  submitMockInterview: (id, d) => apiClient.post(`/api/mock-interview/${id}/submit`, d),
  getMockInterviewHistory: () => apiClient.get(`/api/mock-interview/history/${getUserSession()}`)
}
