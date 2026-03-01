import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' }
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401 && !error.config.url?.includes('/api/auth/')) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      if (window.location.pathname !== '/' && window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

function getUserSession() {
  const authUser = localStorage.getItem('auth_user')
  if (authUser) {
    try { const u = JSON.parse(authUser); if (u.username) return u.username } catch {}
  }
  let s = localStorage.getItem('user_session')
  if (!s) { s = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9); localStorage.setItem('user_session', s) }
  return s
}

export default {
  getUserSession,
  login: (d) => apiClient.post('/api/auth/login', d),
  register: (d) => apiClient.post('/api/auth/register', d),
  getMe: () => apiClient.get('/api/auth/me'),
  getProfile: () => apiClient.get('/api/profile'),
  updateProfile: (d) => apiClient.put('/api/profile', d),
  processVideo: (d) => apiClient.post('/api/process-video', d),
  getTaskStatus: (id) => apiClient.get(`/api/task/${id}`),
  getAllTasks: () => apiClient.get('/api/all-tasks'),
  getQuestions: (p = {}) => apiClient.get('/api/questions', { params: p }),
  getPublicQuestionDetail: (id) => apiClient.get(`/api/questions/${id}`),
  getSimilarQuestions: (q, l = 5) => apiClient.get('/api/questions/similar', { params: { query: q, limit: l } }),
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
  getAllTags: () => apiClient.get('/api/tags'),
  addQuestionTag: (qid, tag) => apiClient.post(`/api/admin/questions/${qid}/tags`, { tag }),
  removeQuestionTag: (qid, tag) => apiClient.delete(`/api/admin/questions/${qid}/tags/${tag}`),
  createSuggestion: (d) => apiClient.post('/api/suggestions', d),
  getSuggestions: (status = null) => apiClient.get('/api/suggestions', { params: status ? { status } : {} }),
  getAdminSuggestions: () => apiClient.get('/api/admin/suggestions'),
  updateSuggestion: (id, d) => apiClient.put(`/api/admin/suggestions/${id}`, d),
  processSuggestion: (id) => apiClient.post(`/api/admin/suggestions/${id}/process`),
  createFeedback: (d) => apiClient.post('/api/feedback', d),
  getAdminFeedback: (p = {}) => apiClient.get('/api/admin/feedback', { params: p }),
  updateFeedback: (id, d) => apiClient.put(`/api/admin/feedback/${id}`, d),
  addBookmark: (qid, note = '') => apiClient.post('/api/bookmarks', { question_id: qid, user_session: getUserSession(), note }),
  removeBookmark: (qid) => apiClient.post('/api/bookmarks', { question_id: qid, user_session: getUserSession() }),
  getBookmarks: () => apiClient.get(`/api/bookmarks/${getUserSession()}`),
  saveNote: (qid, note) => apiClient.put(`/api/notes/${qid}`, { user_session: getUserSession(), note }),
  getNote: (qid) => apiClient.get(`/api/notes/${getUserSession()}`).then(r => { const n = (r.data.notes || []).find(n => n.question_id === qid); return { data: { note: n?.note || '' } } }),
  getAllNotes: () => apiClient.get(`/api/notes/${getUserSession()}`),
  startMockInterview: (d) => apiClient.post('/api/mock-interview/start', { ...d, user_session: getUserSession() }),
  submitMockInterview: (id, d) => apiClient.post(`/api/mock-interview/${id}/submit`, d),
  getMockInterviewHistory: () => apiClient.get(`/api/mock-interview/history/${getUserSession()}`),
  uploadVideoFile: (fd, cfg = {}) => apiClient.post('/api/admin/upload-video-file', fd, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 600000, ...cfg }),
  getPublicStats: () => apiClient.get('/api/stats'),
  getAdminStats: () => apiClient.get('/api/admin/stats'),
  getAdminAnalytics: () => apiClient.get('/api/admin/analytics'),
  getProcessedVideos: () => apiClient.get('/api/admin/videos'),
  getVideoQuestions: (vid) => apiClient.get(`/api/admin/videos/${vid}/questions`),
  deleteVideo: (vid) => apiClient.delete(`/api/admin/videos/${vid}`),
  updateVideo: (vid, d) => apiClient.patch(`/api/admin/videos/${vid}`, d),
  exportQuestions: (tid) => apiClient.get(`/api/export/${tid}`),
  exportJSON: () => apiClient.get('/api/admin/questions'),
  exportCSV: () => apiClient.get('/api/admin/export-csv', { responseType: 'blob' }),
  getTranscript: (tid) => apiClient.get(`/api/transcript/${tid}`),
  getFullExport: (tid) => apiClient.get(`/api/full-export/${tid}`),
  getHealth: () => apiClient.get('/health'),
  getProfessions: () => apiClient.get('/api/professions'),
  getProfessionQuestions: (slug, p = {}) => apiClient.get(`/api/professions/${slug}/questions`, { params: p }),
  getSM2Cards: (p = {}) => apiClient.get(`/api/trainer/sm2-cards/${getUserSession()}`, { params: p }),
  submitSM2Review: (qid, q) => apiClient.post('/api/trainer/sm2-review', { question_id: qid, user_session: getUserSession(), quality: q }),
  resetSM2Progress: () => apiClient.delete(`/api/trainer/sm2-reset/${getUserSession()}`),
  getUserAnswers: (qid) => apiClient.get(`/api/user-answers/${qid}`, { params: { user_session: getUserSession() } }),
  createUserAnswer: (qid, text, name = 'Аноним') => apiClient.post(`/api/user-answers/${qid}`, { user_session: getUserSession(), user_name: name, answer_text: text }),
  voteUserAnswer: (aid, vt) => apiClient.post(`/api/user-answers/${aid}/vote`, { user_session: getUserSession(), vote_type: vt }),
  deleteUserAnswer: (aid) => apiClient.delete(`/api/user-answers/${aid}`, { params: { user_session: getUserSession() } }),
  getTestAssignments: (p = {}) => apiClient.get('/api/test-assignments', { params: p }),
  getTestAssignmentDetail: (id) => apiClient.get(`/api/test-assignments/${id}`),
  createTestAssignment: (d) => apiClient.post('/api/admin/test-assignments', d),
  updateTestAssignment: (id, d) => apiClient.put(`/api/admin/test-assignments/${id}`, d),
  deleteTestAssignment: (id) => apiClient.delete(`/api/admin/test-assignments/${id}`),
  getHHSkills: (prof = null, page = 1, pp = 30) => { const p = { page, per_page: pp }; if (prof) p.profession = prof; return apiClient.get('/api/hh-skills', { params: p }) },
  getHHProfessions: () => apiClient.get('/api/hh-skills/professions'),
  upsertHHSkill: (d) => apiClient.post('/api/admin/hh-skills', d),
}
