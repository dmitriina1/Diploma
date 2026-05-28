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
    filters: {
      topic: '',
      level: '',
      search: ''
    }
  }),
  
  getters: {
    filteredQuestions(state) {
      let filtered = state.questions
      
      if (state.filters.topic) {
        filtered = filtered.filter(q => q.topic === state.filters.topic)
      }
      
      if (state.filters.level) {
        filtered = filtered.filter(q => q.difficulty === state.filters.level)
      }
      
      if (state.filters.search) {
        const search = state.filters.search.toLowerCase()
        filtered = filtered.filter(q => 
          q.question?.toLowerCase().includes(search) ||
          q.answer?.toLowerCase().includes(search) ||
          q.topic?.toLowerCase().includes(search)
        )
      }
      
      return filtered.sort((a, b) => (b.probability || 0) - (a.probability || 0))
    },
    
    topics(state) {
      // Собираем из ВСЕХ вопросов (adminQuestions), не только approved
      const allQuestions = state.adminQuestions.length > 0 ? state.adminQuestions : state.questions
      const topics = new Set(allQuestions.map(q => q.topic).filter(Boolean))
      return Array.from(topics).sort()
    },
    
    unapprovedQuestions(state) {
      return state.adminQuestions.filter(q => !q.approved)
    },
    
    approvedQuestions(state) {
      return state.adminQuestions.filter(q => q.approved)
    }
  },
  
  actions: {
    async fetchQuestions() {
      this.loading = true
      this.error = null
      try {
        const response = await api.getQuestions()
        this.questions = response.data.questions || []
      } catch (error) {
        this.error = error.message
        console.error('Error fetching questions:', error)
      } finally {
        this.loading = false
      }
    },
    
    async fetchAdminQuestions() {
      this.loading = true
      this.error = null
      try {
        const response = await api.getAdminQuestions()
        this.adminQuestions = response.data.questions || []
        this.totalVideos = response.data.total_videos || 0
      } catch (error) {
        this.error = error.message
        console.error('Error fetching admin questions:', error)
      } finally {
        this.loading = false
      }
    },
    
    async approveQuestions(questionIds) {
      try {
        await api.approveQuestions(questionIds)
        await this.fetchAdminQuestions()
        return true
      } catch (error) {
        this.error = error.message
        return false
      }
    },
    
    async revokeQuestions(questionIds) {
      try {
        await api.revokeQuestions(questionIds)
        await this.fetchAdminQuestions()
        return true
      } catch (error) {
        this.error = error.message
        return false
      }
    },
    
    async updateQuestion(questionId, data) {
      try {
        await api.updateQuestion(questionId, data)
        await this.fetchAdminQuestions()
        return true
      } catch (error) {
        this.error = error.message
        return false
      }
    },
    
    async mergeQuestions(sourceId, targetId) {
      try {
        const response = await api.mergeQuestions(sourceId, targetId)
        await this.fetchAdminQuestions()
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      }
    },
    
    async generateAnswer(questionId) {
      try {
        const response = await api.generateAnswer(questionId)
        await this.fetchAdminQuestions()
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      }
    },
    
    async deleteQuestion(questionId) {
      try {
        await api.deleteQuestion(questionId)
        await this.fetchAdminQuestions()
        return true
      } catch (error) {
        this.error = error.message
        return false
      }
    },
    
    setFilters(filters) {
      this.filters = { ...this.filters, ...filters }
    }
  }
})

export const useTasksStore = defineStore('tasks', {
  state: () => ({
    tasks: [],         // Все задачи (глобальный список)
    currentTask: null,  // Текущая активная задача
    loading: false,
    _pollingIntervals: {},  // Интервалы поллинга для каждой задачи
    _globalPollInterval: null,
  }),
  
  getters: {
    activeTasks(state) {
      return state.tasks.filter(t => 
        t.status !== 'completed' && t.status !== 'error'
      )
    },
    
    completedTasks(state) {
      return state.tasks.filter(t => t.status === 'completed')
    },
    
    errorTasks(state) {
      return state.tasks.filter(t => t.status === 'error')
    },
    
    hasActiveTasks(state) {
      return state.tasks.some(t => 
        t.status !== 'completed' && t.status !== 'error'
      )
    }
  },
  
  actions: {
    async fetchAllTasks() {
      try {
        const response = await api.getAllTasks()
        const newTasks = response.data.tasks || []
        
        // Merge with existing tasks to preserve logs
        this.tasks = newTasks.map(t => {
          const existing = this.tasks.find(et => et.task_id === t.task_id)
          return existing ? { ...existing, ...t } : t
        })
      } catch (error) {
        console.error('Error fetching tasks:', error)
      }
    },
    
    async processVideo(videoUrl, topic, level) {
      try {
        const response = await api.processVideo({
          youtube_url: videoUrl,
          topic: topic || 'General',
          level: level || 'middle'
        })
        
        const taskId = response.data.task_id
        
        // Добавляем задачу в список
        const newTask = {
          task_id: taskId,
          video_url: videoUrl,
          status: 'pending',
          progress: 0,
          step: 'Запуск обработки...',
          logs: [{ time: new Date().toISOString(), progress: 0, status: 'pending', message: 'Задача создана' }],
          created_at: new Date().toISOString(),
        }
        
        this.tasks.unshift(newTask)
        this.currentTask = newTask
        
        // Начинаем поллинг
        this.startPolling(taskId)
        
        return taskId
      } catch (error) {
        console.error('Error processing video:', error)
        throw error
      }
    },
    
    startPolling(taskId) {
      // Не дублируем
      if (this._pollingIntervals[taskId]) return
      
      const poll = async () => {
        try {
          const response = await api.getTaskStatus(taskId)
          const data = response.data
          
          // Обновляем задачу в списке
          const idx = this.tasks.findIndex(t => t.task_id === taskId)
          if (idx !== -1) {
            this.tasks[idx] = {
              ...this.tasks[idx],
              status: data.status,
              progress: data.progress || 0,
              step: data.step || 'Обработка...',
              logs: data.logs || this.tasks[idx].logs || [],
              result: data.result,
              error: data.error,
            }
          }
          
          // Обновляем currentTask
          if (this.currentTask?.task_id === taskId) {
            this.currentTask = this.tasks[idx]
          }
          
          // Останавливаем поллинг при завершении
          if (data.status === 'completed' || data.status === 'error') {
            this.stopPolling(taskId)
          }
        } catch (error) {
          console.error('Polling error:', error)
        }
      }
      
      // Первый запрос сразу
      poll()
      this._pollingIntervals[taskId] = setInterval(poll, 2000)
    },
    
    stopPolling(taskId) {
      if (this._pollingIntervals[taskId]) {
        clearInterval(this._pollingIntervals[taskId])
        delete this._pollingIntervals[taskId]
      }
    },
    
    startGlobalPolling() {
      if (this._globalPollInterval) return
      
      this.fetchAllTasks()
      this._globalPollInterval = setInterval(() => {
        this.fetchAllTasks()
      }, 5000)
    },
    
    stopGlobalPolling() {
      if (this._globalPollInterval) {
        clearInterval(this._globalPollInterval)
        this._globalPollInterval = null
      }
    },
    
    clearCurrentTask() {
      this.currentTask = null
    }
  }
})
