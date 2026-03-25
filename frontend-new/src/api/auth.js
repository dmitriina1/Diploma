import { apiClient } from './base'

export const authApi = {
  login: (d) => apiClient.post('/api/auth/login', d),
  register: (d) => apiClient.post('/api/auth/register', d),
  getMe: () => apiClient.get('/api/auth/me'),
  getProfile: () => apiClient.get('/api/profile'),
  updateProfile: (d) => apiClient.put('/api/profile', d)
}
