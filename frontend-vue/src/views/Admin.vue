<template>
  <div class="admin-page">
    <NavBar />
    
    <div class="admin-container">
      <div class="admin-header">
        <h1>
          <i class="pi pi-cog"></i>
          Панель администратора
        </h1>
        <p>Управление видео, вопросами и генерация ответов</p>
      </div>
      
      <TabView>
        <TabPanel header="Загрузка видео">
          <div class="tab-content">
            <Card>
              <template #title>
                <i class="pi pi-upload"></i>
                Загрузить новое видео
              </template>
              <template #content>
                <p>
                  Загрузите видео с собеседованием для автоматического извлечения вопросов.
                  Поддерживаются платформы: YouTube, VK.video, Rutube, OK.ru, Dailymotion, Vimeo.
                </p>
                
                <Button label="Загрузить видео" 
                        icon="pi pi-plus" 
                        @click="showUploadDialog = true" 
                        size="large" />
              </template>
            </Card>
            
            <Card class="mt-4">
              <template #title>
                <i class="pi pi-history"></i>
                История обработки
              </template>
              <template #content>
                <DataTable :value="taskHistory" 
                           :loading="loadingTasks"
                           showGridlines
                           stripedRows
                           :paginator="true"
                           :rows="10">
                  <Column field="task_id" header="Task ID" style="width: 200px">
                    <template #body="slotProps">
                      <code>{{ slotProps.data.task_id.substring(0, 8) }}...</code>
                    </template>
                  </Column>
                  
                  <Column field="video_url" header="URL видео" style="min-width: 300px">
                    <template #body="slotProps">
                      <a :href="slotProps.data.video_url" target="_blank" rel="noopener">
                        {{ slotProps.data.video_url }}
                      </a>
                    </template>
                  </Column>
                  
                  <Column field="status" header="Статус" style="width: 150px">
                    <template #body="slotProps">
                      <Tag :value="slotProps.data.status" 
                           :severity="getStatusSeverity(slotProps.data.status)" 
                           :icon="getStatusIcon(slotProps.data.status)" />
                    </template>
                  </Column>
                  
                  <Column field="questions_count" header="Вопросов" style="width: 100px">
                    <template #body="slotProps">
                      <Badge v-if="slotProps.data.questions_count" 
                             :value="slotProps.data.questions_count" 
                             severity="info" />
                    </template>
                  </Column>
                  
                  <Column field="created_at" header="Дата" style="width: 150px">
                    <template #body="slotProps">
                      {{ formatDate(slotProps.data.created_at) }}
                    </template>
                  </Column>
                </DataTable>
              </template>
            </Card>
          </div>
        </TabPanel>
        
        <TabPanel header="Утверждение вопросов">
          <div class="tab-content">
            <QuestionApproval ref="approvalComponent" />
          </div>
        </TabPanel>
        
        <TabPanel header="Генерация ответов">
          <div class="tab-content">
            <AnswerGenerator />
          </div>
        </TabPanel>
        
        <TabPanel header="Статистика">
          <div class="tab-content">
            <div class="stats-grid">
              <Card>
                <template #title>
                  <div class="stat-card-title">
                    <i class="pi pi-question-circle"></i>
                    <span>Всего вопросов</span>
                  </div>
                </template>
                <template #content>
                  <div class="stat-value">{{ totalQuestions }}</div>
                </template>
              </Card>
              
              <Card>
                <template #title>
                  <div class="stat-card-title">
                    <i class="pi pi-check-circle"></i>
                    <span>Утверждено</span>
                  </div>
                </template>
                <template #content>
                  <div class="stat-value approved">{{ approvedCount }}</div>
                </template>
              </Card>
              
              <Card>
                <template #title>
                  <div class="stat-card-title">
                    <i class="pi pi-clock"></i>
                    <span>Ожидают утверждения</span>
                  </div>
                </template>
                <template #content>
                  <div class="stat-value pending">{{ unapprovedCount }}</div>
                </template>
              </Card>
              
              <Card>
                <template #title>
                  <div class="stat-card-title">
                    <i class="pi pi-book"></i>
                    <span>С ответами</span>
                  </div>
                </template>
                <template #content>
                  <div class="stat-value">{{ questionsWithAnswers }}</div>
                </template>
              </Card>
              
              <Card>
                <template #title>
                  <div class="stat-card-title">
                    <i class="pi pi-bookmark"></i>
                    <span>Технологий</span>
                  </div>
                </template>
                <template #content>
                  <div class="stat-value">{{ topicsCount }}</div>
                </template>
              </Card>
              
              <Card>
                <template #title>
                  <div class="stat-card-title">
                    <i class="pi pi-video"></i>
                    <span>Видео обработано</span>
                  </div>
                </template>
                <template #content>
                  <div class="stat-value">{{ videosProcessed }}</div>
                </template>
              </Card>
            </div>
            
            <Card class="mt-4">
              <template #title>
                Распределение по технологиям
              </template>
              <template #content>
                <DataTable :value="topicDistribution" 
                           showGridlines
                           stripedRows>
                  <Column field="topic" header="Технология" />
                  <Column field="count" header="Количество вопросов">
                    <template #body="slotProps">
                      <Badge :value="slotProps.data.count" severity="info" />
                    </template>
                  </Column>
                  <Column field="approved" header="Утверждено">
                    <template #body="slotProps">
                      <Badge :value="slotProps.data.approved" severity="success" />
                    </template>
                  </Column>
                  <Column field="with_answers" header="С ответами">
                    <template #body="slotProps">
                      <Badge :value="slotProps.data.with_answers" severity="info" />
                    </template>
                  </Column>
                </DataTable>
              </template>
            </Card>
            
            <div class="actions-section mt-4">
              <Card>
                <template #title>
                  Системные действия
                </template>
                <template #content>
                  <div class="system-actions">
                    <Button label="Пересчитать вероятности" 
                            icon="pi pi-refresh" 
                            @click="recalculateProbabilities" 
                            :loading="recalculating" />
                    
                    <Button label="Экспортировать в JSON" 
                            icon="pi pi-download" 
                            @click="exportJSON" 
                            severity="secondary" />
                    
                    <Button label="Экспортировать в CSV" 
                            icon="pi pi-file-excel" 
                            @click="exportCSV" 
                            severity="secondary" />
                  </div>
                </template>
              </Card>
            </div>
          </div>
        </TabPanel>
      </TabView>
    </div>
    
    <VideoUpload v-model:visible="showUploadDialog" @success="onUploadSuccess" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuestionsStore, useTasksStore } from '../store'
import NavBar from '../components/NavBar.vue'
import VideoUpload from '../components/VideoUpload.vue'
import QuestionApproval from '../components/QuestionApproval.vue'
import AnswerGenerator from '../components/AnswerGenerator.vue'
import api from '../api/client'

const questionsStore = useQuestionsStore()
const tasksStore = useTasksStore()

const showUploadDialog = ref(false)
const loadingTasks = ref(false)
const recalculating = ref(false)
const approvalComponent = ref(null)

const totalQuestions = computed(() => questionsStore.questions.length)
const approvedCount = computed(() => questionsStore.approvedQuestions.length)
const unapprovedCount = computed(() => questionsStore.unapprovedQuestions.length)
const questionsWithAnswers = computed(() => 
  questionsStore.questions.filter(q => q.answer).length
)
const topicsCount = computed(() => questionsStore.topics.length)
const videosProcessed = computed(() => {
  const uniqueVideos = new Set(questionsStore.questions.map(q => q.video_url))
  return uniqueVideos.size
})

const taskHistory = computed(() => tasksStore.taskHistory)

const topicDistribution = computed(() => {
  return questionsStore.topics.map(topic => {
    const questions = questionsStore.questions.filter(q => q.topic === topic)
    return {
      topic,
      count: questions.length,
      approved: questions.filter(q => q.is_approved).length,
      with_answers: questions.filter(q => q.answer).length
    }
  }).sort((a, b) => b.count - a.count)
})

const getStatusSeverity = (status) => {
  const severities = {
    pending: 'info',
    downloading: 'info',
    transcribing: 'warning',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return severities[status] || 'info'
}

const getStatusIcon = (status) => {
  const icons = {
    pending: 'pi-clock',
    downloading: 'pi-download',
    transcribing: 'pi-microphone',
    processing: 'pi-cog',
    completed: 'pi-check',
    failed: 'pi-times'
  }
  return icons[status] || 'pi-circle'
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString('ru-RU')
}

const onUploadSuccess = async () => {
  // Refresh task history
  await tasksStore.fetchTaskHistory()
  
  // Refresh admin questions (unapproved)
  await questionsStore.fetchAdminQuestions()
  
  // Refresh approval component
  if (approvalComponent.value) {
    approvalComponent.value.refresh()
  }
}

const recalculateProbabilities = async () => {
  if (!confirm('Пересчитать вероятности для всех вопросов?')) {
    return
  }
  
  recalculating.value = true
  try {
    await api.recalculateProbabilities()
    await questionsStore.fetchQuestions()
    alert('Вероятности успешно пересчитаны!')
  } catch (error) {
    alert('Ошибка при пересчете вероятностей')
    console.error(error)
  } finally {
    recalculating.value = false
  }
}

const exportJSON = async () => {
  try {
    const response = await api.exportJSON()
    const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `questions-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    alert('Ошибка при экспорте в JSON')
    console.error(error)
  }
}

const exportCSV = async () => {
  try {
    const response = await api.exportCSV()
    const blob = new Blob([response.data], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `questions-${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    alert('Ошибка при экспорте в CSV')
    console.error(error)
  }
}

onMounted(async () => {
  loadingTasks.value = true
  await Promise.all([
    questionsStore.fetchQuestions(),
    questionsStore.fetchAdminQuestions(),
    tasksStore.fetchTaskHistory()
  ])
  loadingTasks.value = false
})
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
}

.admin-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.admin-header {
  margin-bottom: 2rem;
}

.admin-header h1 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0 0 0.5rem 0;
  font-size: 2.5rem;
}

.admin-header p {
  margin: 0;
  color: var(--text-color-secondary);
  font-size: 1.1rem;
}

.tab-content {
  padding: 1.5rem 0;
}

.mt-4 {
  margin-top: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.stat-card-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
}

.stat-value {
  font-size: 3rem;
  font-weight: 700;
  color: var(--primary-color);
}

.stat-value.approved {
  color: rgb(34, 197, 94);
}

.stat-value.pending {
  color: rgb(255, 193, 7);
}

.system-actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.actions-section {
  margin-top: 2rem;
}
</style>
