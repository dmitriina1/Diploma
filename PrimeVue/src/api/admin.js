import { apiClient } from './base'

export const adminApi = {
  getAdminQuestions: () => apiClient.get('/api/admin/questions'),
  getQuestionDetail: (id) => apiClient.get(`/api/admin/questions/${id}`),
  createQuestion: (d) => apiClient.post('/api/admin/questions', d),
  updateQuestion: (id, d) => apiClient.put(`/api/admin/questions/${id}`, d),
  deleteQuestion: (id) => apiClient.delete(`/api/admin/questions/${id}`),
  mergeQuestions: (s, t) => apiClient.post('/api/admin/questions/merge', { source_id: s, target_id: t }),
  approveQuestions: (ids) => apiClient.post('/api/admin/approve-questions', { question_ids: ids }),
  revokeQuestions: (ids) => apiClient.post('/api/admin/revoke-questions', { question_ids: ids }),
  generateAnswer: (id) => apiClient.post(`/api/admin/generate-answer/${id}`),
  generateAnswersBulk: (ids = [], max = 10) => apiClient.post('/api/admin/generate-answers-bulk', { question_ids: ids, max_count: max }),
  recalculateProbabilities: () => apiClient.post('/api/admin/recalculate-probabilities'),
  addQuestionTag: (qid, tag) => apiClient.post(`/api/admin/questions/${qid}/tags`, { tag }),
  removeQuestionTag: (qid, tag) => apiClient.delete(`/api/admin/questions/${qid}/tags/${tag}`),

  getAdminSuggestions: () => apiClient.get('/api/admin/suggestions'),
  updateSuggestion: (id, d) => apiClient.put(`/api/admin/suggestions/${id}`, d),
  processSuggestion: (id) => apiClient.post(`/api/admin/suggestions/${id}/process`),

  getAdminFeedback: (p = {}) => apiClient.get('/api/admin/feedback', { params: p }),
  updateFeedback: (id, d) => apiClient.put(`/api/admin/feedback/${id}`, d),

  getAdminStats: () => apiClient.get('/api/admin/stats'),
  getAdminAnalytics: () => apiClient.get('/api/admin/analytics'),
  runHHSyncNow: () => apiClient.post('/api/admin/hh-sync/run'),

  getProcessedVideos: () => apiClient.get('/api/admin/videos'),
  getVideoQuestions: (vid) => apiClient.get(`/api/admin/videos/${vid}/questions`),
  deleteVideo: (vid) => apiClient.delete(`/api/admin/videos/${vid}`),
  updateVideo: (vid, d) => apiClient.patch(`/api/admin/videos/${vid}`, d),

  createTestAssignment: (d) => apiClient.post('/api/admin/test-assignments', d),
  updateTestAssignment: (id, d) => apiClient.put(`/api/admin/test-assignments/${id}`, d),
  deleteTestAssignment: (id) => apiClient.delete(`/api/admin/test-assignments/${id}`),

  upsertHHSkill: (d) => apiClient.post('/api/admin/hh-skills', d)
}
