import { create } from 'zustand'
import type { User } from '@/types'
import { authApi } from '@/api'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
  init: () => void
  login: (data: { username: string; password: string }) => Promise<User>
  register: (data: { username: string; password: string; email?: string }) => Promise<User>
  logout: () => void
  refreshProfile: () => Promise<void>
  updateProfile: (data: Record<string, unknown>) => Promise<User>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  loading: false,

  init: () => {
    const token = localStorage.getItem('auth_token')
    const userRaw = localStorage.getItem('auth_user')
    if (token && userRaw) {
      try {
        const user = JSON.parse(userRaw) as User
        set({ user, token, isAuthenticated: true })
      } catch {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('auth_user')
      }
    }
  },

  login: async ({ username, password }) => {
    set({ loading: true })
    try {
      const { data } = await authApi.login({ username, password })
      const token = data.access_token || data.token
      const user = data.user as User
      localStorage.setItem('auth_token', token)
      localStorage.setItem('auth_user', JSON.stringify(user))
      set({ user, token, isAuthenticated: true })
      return user
    } finally {
      set({ loading: false })
    }
  },

  register: async ({ username, password, email }) => {
    set({ loading: true })
    try {
      const { data } = await authApi.register({ username, password, email })
      const token = data.access_token || data.token
      const user = data.user as User
      localStorage.setItem('auth_token', token)
      localStorage.setItem('auth_user', JSON.stringify(user))
      set({ user, token, isAuthenticated: true })
      return user
    } finally {
      set({ loading: false })
    }
  },

  logout: () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    set({ user: null, token: null, isAuthenticated: false })
  },

  refreshProfile: async () => {
    if (!get().isAuthenticated) return
    try {
      const { data } = await authApi.getProfile()
      const user = data as User
      localStorage.setItem('auth_user', JSON.stringify(user))
      set({ user })
    } catch { /* ignore */ }
  },

  updateProfile: async (payload) => {
    const { data } = await authApi.updateProfile(payload)
    const user = data as User
    localStorage.setItem('auth_user', JSON.stringify(user))
    set({ user })
    return user
  },
}))
