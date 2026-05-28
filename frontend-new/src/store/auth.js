import { defineStore } from 'pinia'
import api from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('auth_user') || 'null'),
    token: localStorage.getItem('auth_token') || null,
    loading: false,
    error: null
  }),
  getters: {
    isAuthenticated: (s) => !!s.token && !!s.user,
    isAdmin: (s) => s.user?.role === 'admin',
    displayName: (s) => s.user?.display_name || s.user?.username || 'Гость',
  },
  actions: {
    async login(username, password) {
      this.loading = true; this.error = null
      try {
        const { data } = await api.login({ username, password })
        this.token = data.access_token; this.user = data.user
        localStorage.setItem('auth_token', data.access_token)
        localStorage.setItem('auth_user', JSON.stringify(data.user))
        return true
      } catch (e) { this.error = e.response?.data?.detail || 'Ошибка входа'; return false }
      finally { this.loading = false }
    },
    async register(username, password, displayName) {
      this.loading = true; this.error = null
      try {
        const { data } = await api.register({ username, password, display_name: displayName })
        this.token = data.access_token; this.user = data.user
        localStorage.setItem('auth_token', data.access_token)
        localStorage.setItem('auth_user', JSON.stringify(data.user))
        return true
      } catch (e) { this.error = e.response?.data?.detail || 'Ошибка регистрации'; return false }
      finally { this.loading = false }
    },
    logout() {
      this.token = null; this.user = null; this.error = null
      localStorage.removeItem('auth_token'); localStorage.removeItem('auth_user')
    },
    async checkAuth() {
      if (!this.token) return false
      try { const { data } = await api.getMe(); this.user = data; localStorage.setItem('auth_user', JSON.stringify(data)); return true }
      catch { this.logout(); return false }
    },
    clearError() { this.error = null }
  }
})
