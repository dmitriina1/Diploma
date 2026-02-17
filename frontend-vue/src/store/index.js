import { defineStore } from 'pinia'
import api from '../api/client'

export const useQuestionsStore = defineStore('questions', {
  state: () => ({
    questions: [],
    adminQuestions: [],
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
      const topics = new Set(state.questions.map(q => q.topic).filter(Boolean))
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
    currentTask: null,
    taskHistory: [],
    ws: null
  }),
  
  actions: {
    async processVideo(videoUrl, topic, level) {
      try {
        const response = await api.processVideo({
          youtube_url: videoUrl,
          topic,
          level
        })
        
        this.currentTask = {
          taskId: response.data.task_id,
          status: 'pending',
          progress: 0,
          step: 'Запуск обработки...'
        }
        
        this.pollTask(response.data.task_id)
        return response.data.task_id
      } catch (error) {
        console.error('Error processing video:', error)
        throw error
      }
    },
    
    async pollTask(taskId) {
      const poll = async () => {
        try {
          const response = await api.getTaskStatus(taskId)
          const data = response.data
          
          this.currentTask = {
            taskId,
            status: data.status,
            progress: data.progress || 0,
            step: data.step || 'Обработка...',
            result: data.result
          }
          
          if (data.status === 'completed' || data.status === 'error') {
            this.taskHistory.unshift(this.currentTask)
            if (this.taskHistory.length > 10) {
              this.taskHistory = this.taskHistory.slice(0, 10)
            }
            return
          }
          
          setTimeout(poll, 2000)
        } catch (error) {
          console.error('Error polling task:', error)
          setTimeout(poll, 2000)
        }
      }
      
      poll()
    },
    
    clearCurrentTask() {
      this.currentTask = null
    }
  }
})
