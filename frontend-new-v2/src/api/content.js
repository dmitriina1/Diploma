import { apiClient } from './base'

export const contentApi = {
  createSuggestion: (d) => apiClient.post('/api/suggestions', d),
  getSuggestions: (status = null) => apiClient.get('/api/suggestions', { params: status ? { status } : {} }),

  getTestAssignments: (p = {}) => apiClient.get('/api/test-assignments', { params: p }),
  getTestAssignmentDetail: (id) => apiClient.get(`/api/test-assignments/${id}`),

  getHHSkills: (prof = null, page = 1, pp = 30, sources = null) => {
    const p = { page, per_page: pp }
    if (prof) p.profession = prof
    if (sources) p.sources = sources  // "skills,description,title"
    return apiClient.get('/api/hh-skills', { params: p })
  },
  getHHProfessions: () => apiClient.get('/api/hh-skills/professions')
}
