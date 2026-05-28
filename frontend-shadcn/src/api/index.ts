import { apiClient, getUserSession, getTasksClientId, getWebSocketUrl, API_BASE_URL } from './client'

export { apiClient, getUserSession, getTasksClientId, getWebSocketUrl, API_BASE_URL }

export const authApi = {
  login: (data: { username: string; password: string }) => apiClient.post('/api/auth/login', data),
  register: (data: { username: string; password: string; email?: string }) =>
    apiClient.post('/api/auth/register', data),
  getMe: () => apiClient.get('/api/auth/me'),
  getProfile: () => apiClient.get('/api/profile'),
  updateProfile: (data: Record<string, unknown>) => apiClient.put('/api/profile', data),
}

export const questionsApi = {
  list: (params: Record<string, unknown> = {}) => apiClient.get('/api/questions', { params }),
  similar: (params: Record<string, unknown> = {}) => apiClient.get('/api/questions/similar', { params }),
  detail: (id: number | string) => apiClient.get(`/api/questions/${id}`),
  professions: () => apiClient.get('/api/professions'),
  professionQuestions: (slug: string, params: Record<string, unknown> = {}) =>
    apiClient.get(`/api/professions/${slug}/questions`, { params }),
  tags: () => apiClient.get('/api/tags'),
  publicStats: () => apiClient.get('/api/stats'),
  recordings: (params: Record<string, unknown> = {}) => apiClient.get('/api/recordings', { params }),
}

export const processingApi = {
  processVideo: (data: { url: string; client_id?: string }) => apiClient.post('/api/process-video', data),
  getTask: (taskId: string) => apiClient.get(`/api/task/${taskId}`),
  getLastResult: (clientId: string) => apiClient.get(`/api/last-result/${clientId}`),
  getTasks: (clientId: string) => apiClient.get(`/api/tasks/${clientId}`),
  getAllTasks: () => apiClient.get('/api/all-tasks'),
}

export const trainerApi = {
  getCards: (userSession: string) => apiClient.get(`/api/trainer/sm2-cards/${userSession}`),
  reviewCard: (data: { question_id: number; grade: number; user_session: string }) =>
    apiClient.post('/api/trainer/sm2-review', data),
  resetCards: (userSession: string) => apiClient.delete(`/api/trainer/sm2-reset/${userSession}`),
}

export const contentApi = {
  createSuggestion: (data: { url: string; description?: string; user_session?: string }) =>
    apiClient.post('/api/suggestions', data),
  getSuggestions: (status?: string) =>
    apiClient.get('/api/suggestions', { params: status ? { status } : {} }),
  getTestAssignments: (params: Record<string, unknown> = {}) =>
    apiClient.get('/api/test-assignments', { params }),
  getTestAssignmentDetail: (id: number | string) => apiClient.get(`/api/test-assignments/${id}`),
  getHHSkills: (
    profession?: string | null,
    page = 1,
    perPage = 30,
    sources?: Array<'skills' | 'description' | 'title'> | null
  ) => {
    const p: Record<string, unknown> = { page, per_page: perPage }
    if (profession) p.profession = profession
    if (sources && sources.length) p.sources = sources.join(',')
    return apiClient.get('/api/hh-skills', { params: p })
  },
  getHHProfessions: () => apiClient.get('/api/hh-skills/professions'),
  postFeedback: (data: { message: string; user_session?: string; page?: string }) =>
    apiClient.post('/api/feedback', data),
  getBookmarks: (userSession: string) => apiClient.get(`/api/bookmarks/${userSession}`),
  addBookmark: (data: { question_id: number; user_session: string; note?: string }) =>
    apiClient.post('/api/bookmarks', data),
  getNotes: (userSession: string) => apiClient.get(`/api/notes/${userSession}`),
  updateNote: (questionId: number | string, data: { user_session: string; note: string }) =>
    apiClient.put(`/api/notes/${questionId}`, data),
  getUserAnswers: (questionId: number | string) => apiClient.get(`/api/user-answers/${questionId}`),
  postUserAnswer: (
    questionId: number | string,
    data: { user_session: string; text: string; is_anonymous?: boolean }
  ) => apiClient.post(`/api/user-answers/${questionId}`, data),
  voteAnswer: (answerId: number, data: { user_session: string; vote: 1 | -1 | 0 }) =>
    apiClient.post(`/api/user-answers/${answerId}/vote`, data),
}

export const chatApi = {
  start: (topic: string, difficulty: string) =>
    apiClient.post('/api/interview-chat/start', {
      topic,
      difficulty,
      user_session: getUserSession(),
    }),
  send: (interviewId: string | number, message: string) =>
    apiClient.post(`/api/interview-chat/${interviewId}/message`, {
      message,
      user_session: getUserSession(),
    }),
  end: (interviewId: string | number) =>
    apiClient.post(`/api/interview-chat/${interviewId}/end`, {
      user_session: getUserSession(),
    }),
  history: (limit = 10) =>
    apiClient.get('/api/interview-chat/history', {
      params: { user_session: getUserSession(), limit },
    }),
}

export const mockApi = {
  start: (data: { difficulty?: string; profession?: string; questions_count?: number }) =>
    apiClient.post('/api/mock-interview/start', { ...data, user_session: getUserSession() }),
  submit: (interviewId: string | number, data: Record<string, unknown>) =>
    apiClient.post(`/api/mock-interview/${interviewId}/submit`, { ...data, user_session: getUserSession() }),
  history: (userSession?: string) =>
    apiClient.get(`/api/mock-interview/history/${userSession || getUserSession()}`),
}

export const adminApi = {
  getQuestions: (params: Record<string, unknown> = {}) =>
    apiClient.get('/api/admin/questions', { params }),
  getQuestion: (id: number | string) => apiClient.get(`/api/admin/questions/${id}`),
  createQuestion: (d: Record<string, unknown>) => apiClient.post('/api/admin/questions', d),
  updateQuestion: (id: number | string, d: Record<string, unknown>) =>
    apiClient.put(`/api/admin/questions/${id}`, d),
  deleteQuestion: (id: number | string) => apiClient.delete(`/api/admin/questions/${id}`),
  approve: (ids: number[]) => apiClient.post('/api/admin/approve-questions', { question_ids: ids }),
  revoke: (ids: number[]) => apiClient.post('/api/admin/revoke-questions', { question_ids: ids }),
  generateAnswer: (id: number | string) => apiClient.post(`/api/admin/generate-answer/${id}`),
  generateAnswersBulk: (ids: number[] = [], max = 10) =>
    apiClient.post('/api/admin/generate-answers-bulk', { question_ids: ids, max_count: max }),
  recalcProbabilities: () => apiClient.post('/api/admin/recalculate-probabilities'),
  getSuggestions: () => apiClient.get('/api/admin/suggestions'),
  updateSuggestion: (id: number | string, d: Record<string, unknown>) =>
    apiClient.put(`/api/admin/suggestions/${id}`, d),
  processSuggestion: (id: number | string) => apiClient.post(`/api/admin/suggestions/${id}/process`),
  getFeedback: (params: Record<string, unknown> = {}) =>
    apiClient.get('/api/admin/feedback', { params }),
  updateFeedback: (id: number | string, d: Record<string, unknown>) =>
    apiClient.put(`/api/admin/feedback/${id}`, d),
  getStats: () => apiClient.get('/api/admin/stats'),
  getAnalytics: () => apiClient.get('/api/admin/analytics'),
  getVideos: () => apiClient.get('/api/admin/videos'),
  getVideoQuestions: (videoId: number | string) =>
    apiClient.get(`/api/admin/videos/${videoId}/questions`),
  deleteVideo: (videoId: number | string) => apiClient.delete(`/api/admin/videos/${videoId}`),
  updateVideo: (videoId: number | string, d: Record<string, unknown>) =>
    apiClient.patch(`/api/admin/videos/${videoId}`, d),
  runHHSync: () => apiClient.post('/api/admin/hh-sync/run'),
  createTestAssignment: (d: Record<string, unknown>) =>
    apiClient.post('/api/admin/test-assignments', d),
  updateTestAssignment: (id: number | string, d: Record<string, unknown>) =>
    apiClient.put(`/api/admin/test-assignments/${id}`, d),
  deleteTestAssignment: (id: number | string) =>
    apiClient.delete(`/api/admin/test-assignments/${id}`),
  exportCsv: () => apiClient.get('/api/admin/export-csv', { responseType: 'blob' }),
  uploadVideoFile: (formData: FormData) =>
    apiClient.post('/api/admin/upload-video-file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}
