import axios from 'axios'

const envBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '/api'

function normalizeBaseUrl(raw) {
  if (!raw) return '/api'
  if (raw.startsWith('/')) return raw
  return raw.replace(/\/$/, '')
}

export const API_BASE_URL = normalizeBaseUrl(envBase)

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' }
})

let redirectingToLogin = false

apiClient.interceptors.request.use((config) => {
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
    if (error.response?.status === 401 && !error.config.url?.includes('/api/auth/')) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      if (!redirectingToLogin && window.location.pathname !== '/' && window.location.pathname !== '/login') {
        redirectingToLogin = true
        window.location.replace('/login')
      }
    }
    return Promise.reject(error)
  }
)

export function getUserSession() {
  const authUser = localStorage.getItem('auth_user')
  if (authUser) {
    try {
      const u = JSON.parse(authUser)
      if (u.username) return u.username
    } catch {}
  }

  let s = localStorage.getItem('user_session')
  if (!s) {
    s = `user_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`
    localStorage.setItem('user_session', s)
  }
  return s
}

export function getTasksClientId() {
  let clientId = localStorage.getItem('tasks_client_id')
  if (!clientId) {
    clientId = `client_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    localStorage.setItem('tasks_client_id', clientId)
  }
  return clientId
}

export function getWebSocketUrl(clientId) {
  const cid = clientId || getTasksClientId()
  const base = API_BASE_URL

  if (base.startsWith('/')) {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    return `${protocol}://${window.location.host}/ws/${cid}`
  }

  const wsBase = base.replace(/^http/, 'ws').replace(/\/api$/, '')
  return `${wsBase}/ws/${cid}`
}
