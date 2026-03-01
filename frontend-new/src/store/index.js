import { defineStore } from 'pinia'
import api from '../api/client'

export const useQuestionsStore = defineStore('questions', {
  state: () => ({
    questions: [],
    adminQuestions: [],
    totalVideos: 0,
    currentQuestion: null,
    loading: false,
    error: null,
    filters: { topic: '', level: '', search: '' }
  }),

  getters: {
    filteredQuestions(state) {
      let filtered = state.questions
      if (state.filters.topic) filtered = filtered.filter(q => q.topic === state.filters.topic)
      if (state.filters.level) filtered = filtered.filter(q => q.difficulty === state.filters.level)
      if (state.filters.search) {
        const s = state.filters.search.toLowerCase()
        filtered = filtered.filter(q =>
          q.question?.toLowerCase().includes(s) ||
          q.answer?.toLowerCase().includes(s) ||
          q.topic?.toLowerCase().includes(s)
        )
      }
      return filtered.sort((a, b) => (b.probability || 0) - (a.probability || 0))
    },
    topics(state) {
      const all = state.adminQuestions.length > 0 ? state.adminQuestions : state.questions
      return [...new Set(all.map(q => q.topic).filter(Boolean))].sort()
    },
    unapprovedQuestions(state) { return state.adminQuestions.filter(q => !q.approved) },
    approvedQuestions(state) { return state.adminQuestions.filter(q => q.approved) }
  },

  actions: {
    async fetchQuestions() {
      this.loading = true; this.error = null
      try { const r = await api.getQuestions(); this.questions = r.data.questions || [] }
      catch (e) { this.error = e.message }
      finally { this.loading = false }
    },
    async fetchAdminQuestions() {
      this.loading = true; this.error = null
      try { const r = await api.getAdminQuestions(); this.adminQuestions = r.data.questions || []; this.totalVideos = r.data.total_videos || 0 }
      catch (e) { this.error = e.message }
      finally { this.loading = false }
    },
    async approveQuestions(ids) {
      try { await api.approveQuestions(ids); await this.fetchAdminQuestions(); return true }
      catch (e) { this.error = e.message; return false }
    },
    async revokeQuestions(ids) {
      try { await api.revokeQuestions(ids); await this.fetchAdminQuestions(); return true }
      catch (e) { this.error = e.message; return false }
    },
    async updateQuestion(id, data) {
      try { await api.updateQuestion(id, data); await this.fetchAdminQuestions(); return true }
      catch (e) { this.error = e.message; return false }
    },
    async mergeQuestions(src, tgt) {
      try { const r = await api.mergeQuestions(src, tgt); await this.fetchAdminQuestions(); return r.data }
      catch (e) { this.error = e.message; throw e }
    },
    async generateAnswer(id) {
      try { const r = await api.generateAnswer(id); await this.fetchAdminQuestions(); return r.data }
      catch (e) { this.error = e.message; throw e }
    },
    async deleteQuestion(id) {
      try { await api.deleteQuestion(id); await this.fetchAdminQuestions(); return true }
      catch (e) { this.error = e.message; return false }
    },
    setFilters(f) { this.filters = { ...this.filters, ...f } }
  }
})

export const useTasksStore = defineStore('tasks', {
  state: () => ({
    tasks: [],
    currentTask: null,
    loading: false,
    _pollingIntervals: {},
    _globalPollInterval: null
  }),
  getters: {
    activeTasks(state) { return state.tasks.filter(t => t.status !== 'completed' && t.status !== 'error') },
    completedTasks(state) { return state.tasks.filter(t => t.status === 'completed') },
    errorTasks(state) { return state.tasks.filter(t => t.status === 'error') },
    hasActiveTasks(state) { return state.tasks.some(t => t.status !== 'completed' && t.status !== 'error') }
  },
  actions: {
    async fetchAllTasks() {
      try {
        const r = await api.getAllTasks()
        const nw = r.data.tasks || []
        this.tasks = nw.map(t => { const ex = this.tasks.find(et => et.task_id === t.task_id); return ex ? { ...ex, ...t } : t })
      } catch (e) { console.error('Error fetching tasks:', e) }
    },
    async processVideo(url, topic, level) {
      const r = await api.processVideo({ youtube_url: url, topic: topic || 'General', level: level || 'middle' })
      const taskId = r.data.task_id
      const t = { task_id: taskId, video_url: url, status: 'pending', progress: 0, step: 'Запуск...', logs: [], created_at: new Date().toISOString() }
      this.tasks.unshift(t); this.currentTask = t; this.startPolling(taskId); return taskId
    },
    startPolling(taskId) {
      if (this._pollingIntervals[taskId]) return
      const poll = async () => {
        try {
          const r = await api.getTaskStatus(taskId); const d = r.data
          const idx = this.tasks.findIndex(t => t.task_id === taskId)
          if (idx !== -1) this.tasks[idx] = { ...this.tasks[idx], status: d.status, progress: d.progress || 0, step: d.step || '', logs: d.logs || this.tasks[idx].logs || [], result: d.result, error: d.error }
          if (this.currentTask?.task_id === taskId) this.currentTask = this.tasks[idx]
          if (d.status === 'completed' || d.status === 'error') this.stopPolling(taskId)
        } catch {}
      }
      poll(); this._pollingIntervals[taskId] = setInterval(poll, 2000)
    },
    stopPolling(id) { if (this._pollingIntervals[id]) { clearInterval(this._pollingIntervals[id]); delete this._pollingIntervals[id] } },
    startGlobalPolling() { if (this._globalPollInterval) return; this.fetchAllTasks(); this._globalPollInterval = setInterval(() => this.fetchAllTasks(), 5000) },
    stopGlobalPolling() { if (this._globalPollInterval) { clearInterval(this._globalPollInterval); this._globalPollInterval = null } },
    clearCurrentTask() { this.currentTask = null }
  }
})
