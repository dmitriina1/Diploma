import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export default {
  // Processing
  processVideo(data) {
    return apiClient.post('/api/process-video', data)
  },
  
  getTaskStatus(taskId) {
    return apiClient.get(`/api/task/${taskId}`)
  },
  
  getAllTasks() {
    return apiClient.get('/api/all-tasks')
  },
  
  // Questions
  getQuestions(params = {}) {
    return apiClient.get('/api/questions', { params })
  },
  
  getPublicQuestionDetail(questionId) {
    return apiClient.get(`/api/questions/${questionId}`)
  },
  
  getSimilarQuestions(query, limit = 5) {
    return apiClient.get('/api/questions/similar', { params: { query, limit } })
  },
  
  // Admin - Questions
  getAdminQuestions() {
    return apiClient.get('/api/admin/questions')
  },
  
  getQuestionDetail(questionId) {
    return apiClient.get(`/api/admin/questions/${questionId}`)
  },
  
  createQuestion(data) {
    return apiClient.post('/api/admin/questions', data)
  },
  
  updateQuestion(questionId, data) {
    return apiClient.put(`/api/admin/questions/${questionId}`, data)
  },
  
  deleteQuestion(questionId) {
    return apiClient.delete(`/api/admin/questions/${questionId}`)
  },
  
  mergeQuestions(sourceId, targetId) {
    return apiClient.post('/api/admin/questions/merge', { source_id: sourceId, target_id: targetId })
  },
  
  approveQuestions(questionIds) {
    return apiClient.post('/api/admin/approve-questions', { question_ids: questionIds })
  },
  
  revokeQuestions(questionIds) {
    return apiClient.post('/api/admin/revoke-questions', { question_ids: questionIds })
  },
  
  generateAnswer(questionId) {
    return apiClient.post(`/api/admin/generate-answer/${questionId}`)
  },
  
  recalculateProbabilities() {
    return apiClient.post('/api/admin/recalculate-probabilities')
  },
  
  // Export
  exportQuestions(taskId) {
    return apiClient.get(`/api/export/${taskId}`)
  },
  
  exportJSON() {
    return apiClient.get('/api/admin/questions')
  },
  
  exportCSV() {
    return apiClient.get('/api/admin/questions')
  },
  
  getTranscript(taskId) {
    return apiClient.get(`/api/transcript/${taskId}`)
  },
  
  getFullExport(taskId) {
    return apiClient.get(`/api/full-export/${taskId}`)
  },
  
  // Health
  getHealth() {
    return apiClient.get('/health')
  }
}
