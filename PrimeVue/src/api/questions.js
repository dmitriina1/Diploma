import { apiClient, getUserSession } from './base'

export const questionsApi = {
  getQuestions: (p = {}) => apiClient.get('/api/questions', { params: p }),
  getPublicQuestionDetail: (id) => apiClient.get(`/api/questions/${id}`),
  getSimilarQuestions: (q, l = 5) => apiClient.get('/api/questions/similar', { params: { query: q, limit: l } }),

  getAllTags: () => apiClient.get('/api/tags'),

  addBookmark: (qid, note = '') => apiClient.post('/api/bookmarks', { question_id: qid, user_session: getUserSession(), note }),
  removeBookmark: (qid) => apiClient.post('/api/bookmarks', { question_id: qid, user_session: getUserSession() }),
  getBookmarks: () => apiClient.get(`/api/bookmarks/${getUserSession()}`),

  saveNote: (qid, note) => apiClient.put(`/api/notes/${qid}`, { user_session: getUserSession(), note }),
  getNote: (qid) => apiClient.get(`/api/notes/${getUserSession()}`).then((r) => {
    const n = (r.data.notes || []).find((item) => item.question_id === qid)
    return { data: { note: n?.note || '' } }
  }),
  getAllNotes: () => apiClient.get(`/api/notes/${getUserSession()}`),

  createFeedback: (d) => apiClient.post('/api/feedback', d),

  getUserAnswers: (qid) => apiClient.get(`/api/user-answers/${qid}`, { params: { user_session: getUserSession() } }),
  createUserAnswer: (qid, text, name = 'Аноним') => apiClient.post(`/api/user-answers/${qid}`, { user_session: getUserSession(), user_name: name, answer_text: text }),
  voteUserAnswer: (aid, vt) => apiClient.post(`/api/user-answers/${aid}/vote`, { user_session: getUserSession(), vote_type: vt }),
  deleteUserAnswer: (aid) => apiClient.delete(`/api/user-answers/${aid}`, { params: { user_session: getUserSession() } }),

  getProfessions: () => apiClient.get('/api/professions'),
  getProfessionQuestions: (slug, p = {}) => apiClient.get(`/api/professions/${slug}/questions`, { params: p })
}
