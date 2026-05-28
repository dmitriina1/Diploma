import { defineStore } from 'pinia'

const STORAGE_KEY = 'ui_theme'

function detectInitialTheme() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'light' || saved === 'dark') return saved
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme)
  localStorage.setItem(STORAGE_KEY, theme)
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    mode: 'dark'
  }),
  getters: {
    isDark: (s) => s.mode === 'dark'
  },
  actions: {
    init() {
      this.mode = detectInitialTheme()
      applyTheme(this.mode)
    },
    setMode(mode) {
      this.mode = mode === 'light' ? 'light' : 'dark'
      applyTheme(this.mode)
    },
    toggle() {
      this.setMode(this.mode === 'dark' ? 'light' : 'dark')
    }
  }
})
