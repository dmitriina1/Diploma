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
    _globalPollInterval: null,
    _ws: null,
    _wsRetryTimer: null
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
      const r = await api.processVideoWithClient({ youtube_url: url, topic: topic || 'General', level: level || 'middle' })
      const taskId = r.data.task_id
      const t = { task_id: taskId, video_url: url, status: 'pending', progress: 0, step: 'Запуск...', logs: [], created_at: new Date().toISOString() }
      this.tasks.unshift(t); this.currentTask = t; this.startPolling(taskId); return taskId
    },
    upsertTask(taskPatch) {
      if (!taskPatch?.task_id) return
      const idx = this.tasks.findIndex((t) => t.task_id === taskPatch.task_id)
      if (idx === -1) {
        this.tasks.unshift({ logs: [], ...taskPatch })
      } else {
        this.tasks[idx] = { ...this.tasks[idx], ...taskPatch, logs: taskPatch.logs || this.tasks[idx].logs || [] }
      }
      if (this.currentTask?.task_id === taskPatch.task_id) {
        this.currentTask = this.tasks.find((t) => t.task_id === taskPatch.task_id) || null
      }
    },
    startPolling(taskId) {
      if (this._pollingIntervals[taskId]) return
      const poll = async () => {
        try {
          const r = await api.getTaskStatus(taskId); const d = r.data
          this.upsertTask({ task_id: taskId, status: d.status, progress: d.progress || 0, step: d.step || '', logs: d.logs || [], result: d.result, error: d.error, video_url: d.video_url || d.youtube_url })
          if (d.status === 'completed' || d.status === 'error') this.stopPolling(taskId)
        } catch {}
      }
      poll(); this._pollingIntervals[taskId] = setInterval(poll, 2000)
    },
    stopPolling(id) { if (this._pollingIntervals[id]) { clearInterval(this._pollingIntervals[id]); delete this._pollingIntervals[id] } },
    connectWs() {
      if (this._ws && (this._ws.readyState === WebSocket.OPEN || this._ws.readyState === WebSocket.CONNECTING)) return
      const url = api.getWebSocketUrl()
      try {
        this._ws = new WebSocket(url)
        this._ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (!data?.task_id) return
            if (data.type === 'progress') {
              this.upsertTask({ task_id: data.task_id, status: data.status, progress: data.progress, step: data.step })
            } else if (data.type === 'completed') {
              this.upsertTask({ task_id: data.task_id, status: 'completed', progress: 100, result: { video_title: data.video_title, questions_count: data.questions_count } })
              this.stopPolling(data.task_id)
            } else if (data.type === 'error') {
              this.upsertTask({ task_id: data.task_id, status: 'error', error: data.error })
              this.stopPolling(data.task_id)
            }
          } catch {}
        }
        this._ws.onclose = () => {
          this._ws = null
          if (this._wsRetryTimer) clearTimeout(this._wsRetryTimer)
          this._wsRetryTimer = setTimeout(() => this.connectWs(), 3000)
        }
      } catch {}
    },
    disconnectWs() {
      if (this._wsRetryTimer) {
        clearTimeout(this._wsRetryTimer)
        this._wsRetryTimer = null
      }
      if (this._ws) {
        this._ws.close()
        this._ws = null
      }
    },
    startGlobalPolling() {
      if (!this._globalPollInterval) {
        this.fetchAllTasks()
        this._globalPollInterval = setInterval(() => this.fetchAllTasks(), 5000)
      }
      this.connectWs()
    },
    stopGlobalPolling() {
      if (this._globalPollInterval) { clearInterval(this._globalPollInterval); this._globalPollInterval = null }
      this.disconnectWs()
    },
    clearCurrentTask() { this.currentTask = null }
  }
})
