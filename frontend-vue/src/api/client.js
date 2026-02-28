import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Генерируем/получаем уникальную сессию пользователя
function getUserSession() {
  let session = localStorage.getItem('user_session')
  if (!session) {
    session = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    localStorage.setItem('user_session', session)
  }
  return session
}

export default {
  getUserSession,

  // ============== Processing ==============
  processVideo(data) {
    return apiClient.post('/api/process-video', data)
  },
  
  getTaskStatus(taskId) {
    return apiClient.get(`/api/task/${taskId}`)
  },
  
  getAllTasks() {
    return apiClient.get('/api/all-tasks')
  },
  
  // ============== Questions (public) ==============
  getQuestions(params = {}) {
    return apiClient.get('/api/questions', { params })
  },
  
  getPublicQuestionDetail(questionId) {
    return apiClient.get(`/api/questions/${questionId}`)
  },
  
  getSimilarQuestions(query, limit = 5) {
    return apiClient.get('/api/questions/similar', { params: { query, limit } })
  },
  
  // ============== Admin - Questions ==============
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
  
  approveQuestions(ids) {
    return apiClient.post('/api/admin/approve-questions', { question_ids: ids })
  },
  
  revokeQuestions(ids) {
    return apiClient.post('/api/admin/revoke-questions', { question_ids: ids })
  },
  
  generateAnswer(id) {
    return apiClient.post(`/api/admin/generate-answer/${id}`)
  },
  
  generateAnswersBulk(questionIds = [], maxCount = 10) {
    return apiClient.post('/api/admin/generate-answers-bulk', { question_ids: questionIds, max_count: maxCount })
  },
  
  recalculateProbabilities() {
    return apiClient.post('/api/admin/recalculate-probabilities')
  },
  
  // ============== Tags ==============
  getAllTags() {
    return apiClient.get('/api/tags')
  },
  
  addQuestionTag(questionId, tag) {
    return apiClient.post(`/api/admin/questions/${questionId}/tags`, { tag })
  },
  
  removeQuestionTag(questionId, tag) {
    return apiClient.delete(`/api/admin/questions/${questionId}/tags/${tag}`)
  },
  
  // ============== Suggestions ==============
  createSuggestion(data) {
    return apiClient.post('/api/suggestions', data)
  },
  
  getSuggestions(status = null) {
    const params = status ? { status } : {}
    return apiClient.get('/api/suggestions', { params })
  },
  
  getAdminSuggestions() {
    return apiClient.get('/api/admin/suggestions')
  },
  
  updateSuggestion(id, data) {
    return apiClient.put(`/api/admin/suggestions/${id}`, data)
  },
  
  processSuggestion(id) {
    return apiClient.post(`/api/admin/suggestions/${id}/process`)
  },
  
  // ============== Feedback ==============
  createFeedback(data) {
    return apiClient.post('/api/feedback', data)
  },
  
  getAdminFeedback(params = {}) {
    // Backend uses is_resolved (boolean), not status string
    return apiClient.get('/api/admin/feedback', { params })
  },
  
  updateFeedback(id, data) {
    return apiClient.put(`/api/admin/feedback/${id}`, data)
  },
  
  // ============== Bookmarks ==============
  addBookmark(questionId, note = '') {
    return apiClient.post('/api/bookmarks', { question_id: questionId, user_session: getUserSession(), note })
  },

  removeBookmark(questionId) {
    // Toggle again to remove
    return apiClient.post('/api/bookmarks', { question_id: questionId, user_session: getUserSession() })
  },
  
  getBookmarks() {
    return apiClient.get(`/api/bookmarks/${getUserSession()}`)
  },
  
  // ============== User Notes ==============
  saveNote(questionId, note) {
    return apiClient.put(`/api/notes/${questionId}`, { user_session: getUserSession(), note })
  },
  
  getNote(questionId) {
    // Get all notes and find the one for this question
    return apiClient.get(`/api/notes/${getUserSession()}`).then(r => {
      const notes = r.data.notes || []
      const found = notes.find(n => n.question_id === questionId)
      return { data: { note: found?.note || '' } }
    })
  },

  getAllNotes() {
    return apiClient.get(`/api/notes/${getUserSession()}`)
  },
  
  // ============== Mock Interview ==============
  startMockInterview(data) {
    return apiClient.post('/api/mock-interview/start', { ...data, user_session: getUserSession() })
  },
  
  submitMockInterview(interviewId, data) {
    return apiClient.post(`/api/mock-interview/${interviewId}/submit`, data)
  },
  
  getMockInterviewHistory() {
    return apiClient.get(`/api/mock-interview/history/${getUserSession()}`)
  },
  
  // ============== Upload local video ==============
  uploadVideoFile(formData, config = {}) {
    return apiClient.post('/api/admin/upload-video-file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000,
      ...config
    })
  },
  
  // ============== Stats ==============
  getPublicStats() {
    return apiClient.get('/api/stats')
  },
  
  getAdminStats() {
    return apiClient.get('/api/admin/stats')
  },
  
  // ============== Videos ==============
  getProcessedVideos() {
    return apiClient.get('/api/admin/videos')
  },

  getVideoQuestions(videoId) {
    return apiClient.get(`/api/admin/videos/${videoId}/questions`)
  },

  deleteVideo(videoId) {
    return apiClient.delete(`/api/admin/videos/${videoId}`)
  },

  updateVideo(videoId, data) {
    return apiClient.patch(`/api/admin/videos/${videoId}`, data)
  },
  
  // ============== Export ==============
  exportQuestions(taskId) {
    return apiClient.get(`/api/export/${taskId}`)
  },
  
  exportJSON() {
    return apiClient.get('/api/admin/questions')
  },
  
  exportCSV() {
    return apiClient.get('/api/admin/export-csv', { responseType: 'blob' })
  },
  
  getTranscript(taskId) {
    return apiClient.get(`/api/transcript/${taskId}`)
  },
  
  getFullExport(taskId) {
    return apiClient.get(`/api/full-export/${taskId}`)
  },
  
  // ============== Health ==============
  getHealth() {
    return apiClient.get('/health')
  },

  // ============== v3: Professions ==============
  getProfessions() {
    return apiClient.get('/api/professions')
  },

  getProfessionQuestions(slug, params = {}) {
    return apiClient.get(`/api/professions/${slug}/questions`, { params })
  },

  // ============== v3: SM-2 Trainer ==============
  getSM2Cards(params = {}) {
    const session = getUserSession()
    return apiClient.get(`/api/trainer/sm2-cards/${session}`, { params })
  },

  submitSM2Review(questionId, quality) {
    return apiClient.post('/api/trainer/sm2-review', {
      question_id: questionId,
      user_session: getUserSession(),
      quality
    })
  },

  resetSM2Progress() {
    return apiClient.delete(`/api/trainer/sm2-reset/${getUserSession()}`)
  },

  // ============== v3: UGC User Answers ==============
  getUserAnswers(questionId) {
    return apiClient.get(`/api/user-answers/${questionId}`, {
      params: { user_session: getUserSession() }
    })
  },

  createUserAnswer(questionId, answerText, userName = 'Аноним') {
    return apiClient.post(`/api/user-answers/${questionId}`, {
      user_session: getUserSession(),
      user_name: userName,
      answer_text: answerText
    })
  },

  voteUserAnswer(answerId, voteType) {
    return apiClient.post(`/api/user-answers/${answerId}/vote`, {
      user_session: getUserSession(),
      vote_type: voteType
    })
  },

  deleteUserAnswer(answerId) {
    return apiClient.delete(`/api/user-answers/${answerId}`, {
      params: { user_session: getUserSession() }
    })
  },

  // ============== v3: Test Assignments ==============
  getTestAssignments(params = {}) {
    return apiClient.get('/api/test-assignments', { params })
  },

  createTestAssignment(data) {
    return apiClient.post('/api/admin/test-assignments', data)
  },

  deleteTestAssignment(id) {
    return apiClient.delete(`/api/admin/test-assignments/${id}`)
  },

  // ============== v3: HH Skills ==============
  getHHSkills(profession = null, page = 1, perPage = 30) {
    const params = { page, per_page: perPage }
    if (profession) params.profession = profession
    return apiClient.get('/api/hh-skills', { params })
  },

  getHHProfessions() {
    return apiClient.get('/api/hh-skills/professions')
  },

  upsertHHSkill(data) {
    return apiClient.post('/api/admin/hh-skills', data)
  }
}
