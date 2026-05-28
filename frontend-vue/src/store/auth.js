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
    isAuthenticated: (state) => !!state.token && !!state.user,
    isAdmin: (state) => state.user?.role === 'admin',
    displayName: (state) => state.user?.display_name || state.user?.username || 'Гость',
    userRole: (state) => state.user?.role || null
  },

  actions: {
    async login(username, password) {
      this.loading = true
      this.error = null
      try {
        const response = await api.login({ username, password })
        const { access_token, user } = response.data

        this.token = access_token
        this.user = user
        localStorage.setItem('auth_token', access_token)
        localStorage.setItem('auth_user', JSON.stringify(user))
        
        return true
      } catch (error) {
        const msg = error.response?.data?.detail || 'Ошибка входа'
        this.error = msg
        return false
      } finally {
        this.loading = false
      }
    },

    async register(username, password, displayName) {
      this.loading = true
      this.error = null
      try {
        const response = await api.register({ username, password, display_name: displayName })
        const { access_token, user } = response.data

        this.token = access_token
        this.user = user
        localStorage.setItem('auth_token', access_token)
        localStorage.setItem('auth_user', JSON.stringify(user))
        
        return true
      } catch (error) {
        const msg = error.response?.data?.detail || 'Ошибка регистрации'
        this.error = msg
        return false
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.token = null
      this.user = null
      this.error = null
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
    },

    async checkAuth() {
      if (!this.token) return false
      try {
        const response = await api.getMe()
        this.user = response.data
        localStorage.setItem('auth_user', JSON.stringify(response.data))
        return true
      } catch {
        this.logout()
        return false
      }
    },

    clearError() {
      this.error = null
    }
  }
})
