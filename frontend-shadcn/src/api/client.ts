import axios, { type AxiosInstance } from 'axios'

const envBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '/api'

function normalize(raw: string): string {
  if (!raw) return '/api'
  if (raw.startsWith('/')) return raw
  return raw.replace(/\/$/, '')
}

export const API_BASE_URL = normalize(envBase)

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60_000,
})

apiClient.interceptors.request.use((config) => {
  // If baseURL already ends with /api and url starts with /api/, strip duplicate prefix
  if (config.baseURL?.endsWith('/api') && typeof config.url === 'string' && config.url.startsWith('/api/')) {
    config.url = config.url.slice(4)
  }
  const token = localStorage.getItem('auth_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (r) => r,
  (error) => {
    const status = error.response?.status
    const url = error.config?.url || ''
    if (status === 401 && !url.includes('/api/auth/')) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      const { pathname } = window.location
      if (pathname !== '/' && pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export function getUserSession(): string {
  const authUserRaw = localStorage.getItem('auth_user')
  if (authUserRaw) {
    try {
      const u = JSON.parse(authUserRaw)
      if (u?.username) return u.username as string
    } catch { /* ignore */ }
  }
  let s = localStorage.getItem('user_session')
  if (!s) {
    s = `user_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`
    localStorage.setItem('user_session', s)
  }
  return s
}

export function getTasksClientId(): string {
  let id = localStorage.getItem('tasks_client_id')
  if (!id) {
    id = `client_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    localStorage.setItem('tasks_client_id', id)
  }
  return id
}

export function getWebSocketUrl(clientId?: string): string {
  const cid = clientId || getTasksClientId()
  const base = API_BASE_URL
  if (base.startsWith('/')) {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    return `${protocol}://${window.location.host}/ws/${cid}`
  }
  const wsBase = base.replace(/^http/, 'ws').replace(/\/api$/, '')
  return `${wsBase}/ws/${cid}`
}
