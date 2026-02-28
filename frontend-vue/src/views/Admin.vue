<template>
  <div class="admin-page">
    <NavBar />

    <div class="admin-container">
      <!-- Header -->
      <header class="admin-header">
        <div class="header-left">
          <h1><i class="pi pi-sliders-h"></i> Панель управления</h1>
          <p class="subtitle">Обработка видео, утверждение вопросов, генерация ответов и управление контентом</p>
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
      <TabView class="admin-tabs" v-model:activeIndex="activeTab">
        <TabPanel>
          <template #header>
            <i class="pi pi-check-square mr-2"></i> Вопросы
          </template>
          <div class="tab-toolbar">
            <Button label="Массовая генерация ответов" icon="pi pi-sparkles" severity="help" size="small"
                    @click="bulkGenerate" :loading="bulkGenerating" 
                    v-tooltip="'Сгенерировать ответы для всех утверждённых вопросов без ответа'" />
          </div>
          <QuestionApproval ref="approvalComponent" />
        </TabPanel>

        <TabPanel>
          <template #header>
            <i class="pi pi-lightbulb mr-2"></i> Предложения
          </template>
          <SuggestionsManager ref="suggestionsComponent" />
        </TabPanel>

        <TabPanel>
          <template #header>
            <i class="pi pi-comments mr-2"></i> Обратная связь
          </template>
          <FeedbackManager ref="feedbackComponent" />
        </TabPanel>

        <TabPanel>
          <template #header>
            <i class="pi pi-video mr-2"></i> Видео
          </template>
          <div class="videos-manager">
            <div class="vm-toolbar">
              <InputText v-model="videoSearch" placeholder="Поиск видео..." class="vm-search" />
              <span class="vm-count">{{ filteredAdminVideos.length }} видео</span>
            </div>
            <div v-if="adminVideosLoading" class="vm-loading"><ProgressSpinner strokeWidth="3" /></div>
            <div v-else-if="filteredAdminVideos.length === 0" class="vm-empty">
              <i class="pi pi-video"></i>
              <p>Видео не найдены</p>
            </div>
            <DataTable v-else :value="filteredAdminVideos" stripedRows :paginator="true" :rows="10"
                       :rowsPerPageOptions="[10, 25, 50]" responsiveLayout="scroll">
              <Column field="title" header="Название" style="min-width:200px">
                <template #body="s">
                  <div v-if="editingVideoId === s.data.id" class="vm-edit-title">
                    <InputText v-model="editingVideoTitle" class="w-full" size="small" />
                    <Button icon="pi pi-check" size="small" severity="success" text @click="saveVideoTitle(s.data)" />
                    <Button icon="pi pi-times" size="small" severity="secondary" text @click="editingVideoId = null" />
                  </div>
                  <div v-else class="vm-title-cell">
                    <span>{{ s.data.title || 'Без названия' }}</span>
                    <Button icon="pi pi-pencil" size="small" text severity="secondary" 
                            @click="startEditVideo(s.data)" v-tooltip="'Переименовать'" />
                  </div>
                </template>
              </Column>
              <Column field="platform" header="Платформа" style="width:110px">
                <template #body="s"><Tag :value="s.data.platform" severity="info" /></template>
              </Column>
              <Column field="question_count" header="Вопросов" style="width:100px">
                <template #body="s"><Badge :value="s.data.question_count || s.data.linked_questions || 0" severity="info" /></template>
              </Column>
              <Column field="processed_at" header="Обработано" style="width:130px">
                <template #body="s">{{ formatTime(s.data.processed_at) }}</template>
              </Column>
              <Column header="" style="width:120px">
                <template #body="s">
                  <div class="vm-actions">
                    <Button icon="pi pi-external-link" size="small" text severity="info"
                            @click="openVideoUrl(s.data)" v-tooltip="'Открыть'" />
                    <Button icon="pi pi-trash" size="small" text severity="danger"
                            @click="deleteVideoConfirm(s.data)" v-tooltip="'Удалить'" />
                  </div>
                </template>
              </Column>
            </DataTable>
          </div>
        </TabPanel>
        
        <TabPanel>
          <template #header>
            <i class="pi pi-chart-bar mr-2"></i> Статистика
          </template>
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
            <Button label="Экспорт CSV" icon="pi pi-file" @click="exportCSV" severity="secondary" />
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
import SuggestionsManager from '../components/SuggestionsManager.vue'
import FeedbackManager from '../components/FeedbackManager.vue'
import api from '../api/client'

const questionsStore = useQuestionsStore()
const tasksStore = useTasksStore()

const showUploadDialog = ref(false)
const recalculating = ref(false)
const approvalComponent = ref(null)
const expandedLogs = ref({})
const suggestionsComponent = ref(null)
const feedbackComponent = ref(null)
const activeTab = ref(0)
const bulkGenerating = ref(false)

// Video management
const adminVideos = ref([])
const adminVideosLoading = ref(false)
const videoSearch = ref('')
const editingVideoId = ref(null)
const editingVideoTitle = ref('')

const filteredAdminVideos = computed(() => {
  if (!videoSearch.value) return adminVideos.value
  const s = videoSearch.value.toLowerCase()
  return adminVideos.value.filter(v => (v.title || '').toLowerCase().includes(s) || (v.youtube_url || '').toLowerCase().includes(s))
})

const loadAdminVideos = async () => {
  adminVideosLoading.value = true
  try {
    const r = await api.getProcessedVideos()
    adminVideos.value = r.data?.videos || r.data || []
  } catch (e) { console.error(e) }
  adminVideosLoading.value = false
}

const startEditVideo = (video) => {
  editingVideoId.value = video.id
  editingVideoTitle.value = video.title || ''
}

const saveVideoTitle = async (video) => {
  try {
    await api.updateVideo(video.id, { title: editingVideoTitle.value })
    video.title = editingVideoTitle.value
    editingVideoId.value = null
  } catch (e) { alert('Ошибка сохранения: ' + e.message) }
}

const openVideoUrl = (video) => {
  const url = video.youtube_url || video.url
  if (url) window.open(url, '_blank')
}

const deleteVideoConfirm = async (video) => {
  if (!confirm(`Удалить видео «${video.title || video.youtube_url}»? Связи с вопросами будут удалены.`)) return
  try {
    await api.deleteVideo(video.id)
    adminVideos.value = adminVideos.value.filter(v => v.id !== video.id)
  } catch (e) { alert('Ошибка удаления: ' + e.message) }
}

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
const bulkGenerate = async () => {
  const toGenerate = questionsStore.approvedQuestions.filter(q => !q.answer)
  if (toGenerate.length === 0) {
    alert('Все утверждённые вопросы уже имеют ответы!')
    return
  }
  if (!confirm(`Сгенерировать ответы для ${toGenerate.length} вопросов? Это может занять некоторое время.`)) return
  bulkGenerating.value = true
  let success = 0, fail = 0
  for (const q of toGenerate) {
    try {
      await questionsStore.generateAnswer(q.id)
      success++
    } catch { fail++ }
  }
  bulkGenerating.value = false
  alert(`Готово! Успешно: ${success}, ошибки: ${fail}`)
  await questionsStore.fetchQuestions()
}

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

const exportCSV = async () => {
  try {
    const r = await api.exportCSV()
    const blob = new Blob([r.data], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `questions-${Date.now()}.csv`; a.click()
    URL.revokeObjectURL(url)
  } catch (e) { alert('Ошибка экспорта CSV') }
}

onMounted(async () => {
  await Promise.all([
    questionsStore.fetchQuestions(),
    questionsStore.fetchAdminQuestions(),
    tasksStore.fetchAllTasks(),
    loadAdminVideos()
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
  padding: 1.5rem 0;
}

.admin-tabs :deep(.p-tabview-nav) {
  background: transparent;
  border-color: rgba(255,255,255,0.08);
}

.admin-tabs :deep(.p-tabview-nav li .p-tabview-nav-link) {
  padding: 0.85rem 1.5rem;
  font-weight: 600;
  font-size: 0.92rem;
  border-radius: 8px 8px 0 0;
  font-family: 'Inter', sans-serif;
}

/* Consistent fonts across all admin sub-components */
.admin-page :deep(h3),
.admin-page :deep(h4) {
  font-family: 'Inter', sans-serif;
  font-weight: 700;
}

.admin-page :deep(.p-datatable .p-datatable-thead > tr > th) {
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: rgba(255,255,255,0.6);
}

.admin-page :deep(.p-datatable .p-datatable-tbody > tr > td) {
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
}

.admin-page :deep(.p-card .p-card-title) {
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 1.1rem;
}

.admin-page :deep(.p-tag) {
  font-family: 'Inter', sans-serif;
  font-weight: 600;
}

.admin-page :deep(.p-button .p-button-label) {
  font-family: 'Inter', sans-serif;
  font-weight: 600;
}

.admin-page :deep(.p-dropdown .p-dropdown-label) {
  font-family: 'Inter', sans-serif;
}

.admin-page :deep(.p-inputtext) {
  font-family: 'Inter', sans-serif;
}

/* Fix Paginator dropdown alignment & spacing */
.admin-page :deep(.p-paginator) {
  font-family: 'Inter', sans-serif;
  background: transparent;
  border: none;
  padding: 0.75rem 0;
}

.admin-page :deep(.p-paginator .p-dropdown) {
  display: inline-flex;
  align-items: center;
  margin-left: 0.5rem;
}

.admin-page :deep(.p-paginator .p-dropdown .p-dropdown-label) {
  display: flex;
  align-items: center;
  padding: 0.35rem 0.5rem;
  min-width: 2.5rem;
  text-align: center;
}

.admin-page :deep(.p-paginator .p-dropdown .p-dropdown-trigger) {
  width: 2rem;
}

.admin-page :deep(.p-paginator .p-paginator-rpp-options) {
  margin-left: 0.5rem;
}

.tab-toolbar {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
}

.mr-2 { margin-right: 0.5rem; }

/* Video Manager */
.videos-manager { padding: 0.5rem 0; }
.vm-toolbar { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
.vm-search { min-width: 250px; }
.vm-count { color: rgba(255,255,255,0.45); font-size: 0.85rem; margin-left: auto; }
.vm-loading { display: flex; justify-content: center; padding: 2rem; }
.vm-empty { text-align: center; padding: 3rem; color: rgba(255,255,255,0.4); }
.vm-empty i { font-size: 2.5rem; display: block; margin-bottom: 0.5rem; }
.vm-title-cell { display: flex; align-items: center; gap: 0.25rem; }
.vm-edit-title { display: flex; align-items: center; gap: 0.25rem; }
.vm-actions { display: flex; gap: 0.25rem; }
</style>
