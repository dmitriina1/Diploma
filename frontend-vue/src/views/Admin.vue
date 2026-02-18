<template>
  <div class="admin-page">
    <NavBar />

    <div class="admin-container">
      <!-- Header -->
      <header class="admin-header">
        <div class="header-left">
          <h1><i class="pi pi-sliders-h"></i> Панель управления</h1>
          <p class="subtitle">Обработка видео, утверждение вопросов и генерация ответов</p>
        </div>
        <Button label="Загрузить видео" icon="pi pi-plus" @click="showUploadDialog = true" class="upload-btn" />
      </header>

      <!-- Active Tasks Panel (always visible when tasks exist) -->
      <section v-if="allTasks.length > 0" class="tasks-section">
        <div class="section-title">
          <i class="pi pi-spinner pi-spin" v-if="hasActiveTasks"></i>
          <i class="pi pi-list" v-else></i>
          <span>Обработка видео</span>
          <Badge :value="activeTasks.length" severity="warning" v-if="activeTasks.length" />
        </div>
        
        <div class="tasks-list">
          <div v-for="task in allTasks" :key="task.task_id" 
               class="task-card" :class="'status-' + task.status">
            <div class="task-header">
              <div class="task-title">
                <Tag :value="getStatusLabel(task.status)" :severity="getStatusSeverity(task.status)" :icon="getStatusIcon(task.status)" />
                <span class="task-url" :title="task.video_url">{{ truncateUrl(task.video_url) }}</span>
              </div>
              <span class="task-time">{{ formatTime(task.created_at) }}</span>
            </div>
            
            <ProgressBar :value="task.progress" :showValue="true" 
                         :class="{ 'error-bar': task.status === 'error' }" />
            
            <div class="task-step">
              <i :class="getStepIcon(task.status)"></i>
              {{ task.step || 'Ожидание...' }}
            </div>
            
            <!-- Error display -->
            <div v-if="task.status === 'error' && task.error" class="task-error">
              <i class="pi pi-exclamation-triangle"></i>
              {{ task.error }}
            </div>
            
            <!-- Result summary -->
            <div v-if="task.status === 'completed' && task.result" class="task-result">
              <i class="pi pi-check-circle"></i>
              Найдено {{ task.result.questions_count }} вопросов
            </div>
            
            <!-- Logs toggle -->
            <div class="task-logs-toggle" @click="toggleLogs(task.task_id)">
              <i :class="expandedLogs[task.task_id] ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"></i>
              <span>{{ expandedLogs[task.task_id] ? 'Скрыть логи' : 'Показать логи' }}</span>
            </div>
            
            <transition name="slide">
              <div v-if="expandedLogs[task.task_id] && task.logs?.length" class="task-logs">
                <div v-for="(log, i) in task.logs" :key="i" class="log-entry" :class="'log-' + log.status">
                  <span class="log-time">{{ formatLogTime(log.time) }}</span>
                  <span class="log-msg">{{ log.message }}</span>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </section>

      <!-- Tabs -->
      <TabView class="admin-tabs">
        <TabPanel header="Утверждение вопросов">
          <QuestionApproval ref="approvalComponent" />
        </TabPanel>
        
        <TabPanel header="Генерация ответов">
          <AnswerGenerator />
        </TabPanel>
        
        <TabPanel header="Статистика">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon" style="background: linear-gradient(135deg, #667eea, #764ba2)">
                <i class="pi pi-question-circle"></i>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ totalQuestions }}</div>
                <div class="stat-label">Всего вопросов</div>
              </div>
            </div>
            
            <div class="stat-card">
              <div class="stat-icon" style="background: linear-gradient(135deg, #22c55e, #16a34a)">
                <i class="pi pi-check-circle"></i>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ approvedCount }}</div>
                <div class="stat-label">Утверждено</div>
              </div>
            </div>
            
            <div class="stat-card">
              <div class="stat-icon" style="background: linear-gradient(135deg, #f59e0b, #d97706)">
                <i class="pi pi-clock"></i>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ unapprovedCount }}</div>
                <div class="stat-label">Ожидают</div>
              </div>
            </div>
            
            <div class="stat-card">
              <div class="stat-icon" style="background: linear-gradient(135deg, #6366f1, #4f46e5)">
                <i class="pi pi-book"></i>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ questionsWithAnswers }}</div>
                <div class="stat-label">С ответами</div>
              </div>
            </div>
            
            <div class="stat-card">
              <div class="stat-icon" style="background: linear-gradient(135deg, #ec4899, #db2777)">
                <i class="pi pi-bookmark"></i>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ topicsCount }}</div>
                <div class="stat-label">Технологий</div>
              </div>
            </div>
            
            <div class="stat-card">
              <div class="stat-icon" style="background: linear-gradient(135deg, #14b8a6, #0d9488)">
                <i class="pi pi-video"></i>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ videosProcessed }}</div>
                <div class="stat-label">Видео</div>
              </div>
            </div>
          </div>
          
          <Card class="mt-3">
            <template #title>Распределение по технологиям</template>
            <template #content>
              <DataTable :value="topicDistribution" showGridlines stripedRows>
                <Column field="topic" header="Технология" />
                <Column field="count" header="Вопросов">
                  <template #body="s">
                    <Badge :value="s.data.count" severity="info" />
                  </template>
                </Column>
                <Column field="approved" header="Утверждено">
                  <template #body="s">
                    <Badge :value="s.data.approved" severity="success" />
                  </template>
                </Column>
                <Column field="with_answers" header="С ответами">
                  <template #body="s">
                    <Badge :value="s.data.with_answers" severity="info" />
                  </template>
                </Column>
              </DataTable>
            </template>
          </Card>
          
          <div class="system-actions mt-3">
            <Button label="Пересчитать вероятности" icon="pi pi-refresh" @click="recalculateProbabilities" :loading="recalculating" />
            <Button label="Экспорт JSON" icon="pi pi-download" @click="exportJSON" severity="secondary" />
          </div>
        </TabPanel>
      </TabView>
    </div>
    
    <VideoUpload v-model:visible="showUploadDialog" @submitted="onVideoSubmitted" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useQuestionsStore, useTasksStore } from '../store'
import NavBar from '../components/NavBar.vue'
import VideoUpload from '../components/VideoUpload.vue'
import QuestionApproval from '../components/QuestionApproval.vue'
import AnswerGenerator from '../components/AnswerGenerator.vue'
import api from '../api/client'

const questionsStore = useQuestionsStore()
const tasksStore = useTasksStore()

const showUploadDialog = ref(false)
const recalculating = ref(false)
const approvalComponent = ref(null)
const expandedLogs = ref({})

// Task getters
const allTasks = computed(() => tasksStore.tasks)
const activeTasks = computed(() => tasksStore.activeTasks)
const hasActiveTasks = computed(() => tasksStore.hasActiveTasks)

// Stats
const totalQuestions = computed(() => questionsStore.questions.length)
const approvedCount = computed(() => questionsStore.approvedQuestions.length)
const unapprovedCount = computed(() => questionsStore.unapprovedQuestions.length)
const questionsWithAnswers = computed(() => questionsStore.questions.filter(q => q.answer).length)
const topicsCount = computed(() => questionsStore.topics.length)
const videosProcessed = computed(() => {
  const v = new Set(questionsStore.questions.map(q => q.video_url))
  return v.size
})

const topicDistribution = computed(() => {
  return questionsStore.topics.map(topic => {
    const qs = questionsStore.questions.filter(q => q.topic === topic)
    return {
      topic,
      count: qs.length,
      approved: qs.filter(q => q.is_approved || q.approved).length,
      with_answers: qs.filter(q => q.answer).length
    }
  }).sort((a, b) => b.count - a.count)
})

// Helpers
const getStatusSeverity = (s) => ({
  pending: 'info', downloading: 'info', downloaded: 'info',
  transcribing: 'warning', transcribed: 'warning',
  extracting: 'warning', extracted: 'warning',
  saving: 'warning', completed: 'success', error: 'danger'
})[s] || 'info'

const getStatusIcon = (s) => ({
  pending: 'pi pi-clock', downloading: 'pi pi-download', downloaded: 'pi pi-check',
  transcribing: 'pi pi-spin pi-spinner', transcribed: 'pi pi-check',
  extracting: 'pi pi-spin pi-spinner', extracted: 'pi pi-check',
  saving: 'pi pi-spin pi-spinner', completed: 'pi pi-check-circle', error: 'pi pi-times-circle'
})[s] || 'pi pi-circle'

const getStatusLabel = (s) => ({
  pending: 'Ожидание', downloading: 'Скачивание', downloaded: 'Скачано',
  transcribing: 'Транскрибация', transcribed: 'Транскрибировано',
  extracting: 'Извлечение', extracted: 'Извлечено',
  saving: 'Сохранение', completed: 'Готово', error: 'Ошибка'
})[s] || s

const getStepIcon = (s) => {
  if (s === 'error') return 'pi pi-exclamation-triangle'
  if (s === 'completed') return 'pi pi-check'
  return 'pi pi-info-circle'
}

const truncateUrl = (url) => {
  if (!url) return '—'
  if (url.length > 60) return url.substring(0, 57) + '...'
  return url
}

const formatTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleString('ru-RU', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
}

const formatLogTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const toggleLogs = (taskId) => {
  expandedLogs.value[taskId] = !expandedLogs.value[taskId]
}

// Actions
const onVideoSubmitted = async (taskId) => {
  // Task is already added to the store — just refresh UI
  if (approvalComponent.value) {
    setTimeout(() => approvalComponent.value.refresh?.(), 5000)
  }
}

const recalculateProbabilities = async () => {
  if (!confirm('Пересчитать вероятности?')) return
  recalculating.value = true
  try {
    await api.recalculateProbabilities()
    await questionsStore.fetchQuestions()
  } catch (e) {
    alert('Ошибка: ' + e.message)
  } finally {
    recalculating.value = false
  }
}

const exportJSON = async () => {
  try {
    const r = await api.getAdminQuestions()
    const blob = new Blob([JSON.stringify(r.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `questions-${Date.now()}.json`; a.click()
    URL.revokeObjectURL(url)
  } catch (e) { alert('Ошибка экспорта') }
}

onMounted(async () => {
  await Promise.all([
    questionsStore.fetchQuestions(),
    questionsStore.fetchAdminQuestions(),
    tasksStore.fetchAllTasks()
  ])
  tasksStore.startGlobalPolling()
  
  // Start polling for active tasks
  for (const t of tasksStore.activeTasks) {
    tasksStore.startPolling(t.task_id)
  }
})

onUnmounted(() => {
  tasksStore.stopGlobalPolling()
})
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #0f0f1e 0%, #1a1a2e 50%, #16213e 100%);
}

.admin-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.5rem 2rem 3rem;
}

/* Header */
.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.admin-header h1 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
  font-size: 1.8rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea, #f093fb);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  margin: 0.3rem 0 0;
  color: rgba(255,255,255,0.45);
  font-size: 0.9rem;
}

.upload-btn {
  font-weight: 600;
  padding: 0.7rem 1.5rem;
}

/* Tasks Section */
.tasks-section {
  margin-bottom: 2rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: rgba(255,255,255,0.85);
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.task-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 1rem 1.25rem;
  transition: border-color 0.3s;
}

.task-card.status-error {
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.04);
}

.task-card.status-completed {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.03);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.6rem;
}

.task-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.task-url {
  font-size: 0.85rem;
  color: rgba(255,255,255,0.55);
  font-family: 'Fira Code', monospace;
}

.task-time {
  font-size: 0.75rem;
  color: rgba(255,255,255,0.35);
}

.task-step {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: rgba(255,255,255,0.6);
}

.task-error {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  color: #f87171;
  font-size: 0.85rem;
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
}

.task-result {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 6px;
  color: #4ade80;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.error-bar :deep(.p-progressbar-value) {
  background: linear-gradient(135deg, #ef4444, #dc2626) !important;
}

/* Logs */
.task-logs-toggle {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: rgba(255,255,255,0.35);
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
}

.task-logs-toggle:hover {
  color: rgba(255,255,255,0.6);
}

.task-logs {
  margin-top: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
  background: rgba(0,0,0,0.3);
  border-radius: 6px;
  padding: 0.5rem;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 0.75rem;
}

.log-entry {
  display: flex;
  gap: 0.6rem;
  padding: 0.15rem 0;
  color: rgba(255,255,255,0.5);
}

.log-entry.log-error {
  color: #f87171;
}

.log-entry.log-completed {
  color: #4ade80;
}

.log-time {
  color: rgba(255,255,255,0.3);
  flex-shrink: 0;
}

/* Slide transition */
.slide-enter-active, .slide-leave-active {
  transition: all 0.25s ease;
}

.slide-enter-from, .slide-leave-to {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 1.2rem;
  transition: transform 0.2s, border-color 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255,255,255,0.15);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon i {
  font-size: 1.3rem;
  color: white;
}

.stat-number {
  font-size: 1.8rem;
  font-weight: 800;
  line-height: 1;
  color: rgba(255,255,255,0.9);
}

.stat-label {
  font-size: 0.8rem;
  color: rgba(255,255,255,0.45);
  margin-top: 0.2rem;
}

/* System actions */
.system-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.mt-3 {
  margin-top: 1.5rem;
}

/* Admin tabs override */
.admin-tabs :deep(.p-tabview-panels) {
  background: transparent;
}

.admin-tabs :deep(.p-tabview-nav) {
  background: transparent;
  border-color: rgba(255,255,255,0.08);
}
</style>
