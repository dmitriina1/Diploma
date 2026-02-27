<template>
  <div class="video-manager">
    <div class="section-header">
      <h3><i class="pi pi-video"></i> Управление видео</h3>
      <Button icon="pi pi-refresh" @click="loadVideos" text rounded />
    </div>

    <!-- Загрузка локального файла -->
    <Panel header="Загрузить видео с компьютера" toggleable :collapsed="true" class="upload-panel mb-3">
      <div class="upload-form">
        <div class="form-row">
          <label>Видеофайл:</label>
          <FileUpload mode="basic" accept="video/*,audio/*" :maxFileSize="2000000000"
                      chooseLabel="Выбрать файл" :auto="false" ref="fileUploadRef"
                      @select="onFileSelect" class="upload-btn" />
          <small v-if="uploadFile" class="file-info">{{ uploadFile.name }} ({{ formatSize(uploadFile.size) }})</small>
        </div>
        <div class="form-row">
          <label>Название:</label>
          <InputText v-model="uploadTitle" placeholder="Название видео" class="w-full" />
        </div>
        <div class="form-grid">
          <div class="form-row">
            <label>Тема:</label>
            <Dropdown v-model="uploadTopic" :options="topics" placeholder="Выберите тему" class="w-full" />
          </div>
          <div class="form-row">
            <label>Сложность:</label>
            <Dropdown v-model="uploadDifficulty" :options="difficulties" optionLabel="label" optionValue="value" 
                      placeholder="Сложность" class="w-full" />
          </div>
        </div>
        <Button label="Загрузить и обработать" icon="pi pi-upload" :loading="uploading" 
                @click="uploadVideo" :disabled="!uploadFile || !uploadTitle" class="mt-2" />
        
        <ProgressBar v-if="uploading" :value="uploadProgress" :showValue="true" class="mt-2" />
      </div>
    </Panel>

    <!-- Список обработанных видео -->
    <div v-if="loading" class="loading"><ProgressSpinner strokeWidth="3" /></div>
    <div v-else-if="videos.length === 0" class="empty"><p>Нет обработанных видео</p></div>

    <DataTable v-else :value="videos" :paginator="true" :rows="10" stripedRows
               dataKey="id" responsiveLayout="scroll">
      <Column field="title" header="Название">
        <template #body="s">
          <div class="video-title">
            <a v-if="s.data.url" :href="s.data.url" target="_blank" class="title-link">{{ s.data.title || 'Без названия' }}</a>
            <span v-else>{{ s.data.title || 'Без названия' }}</span>
          </div>
        </template>
      </Column>
      <Column field="platform" header="Платформа">
        <template #body="s">
          <Tag :value="s.data.platform || 'youtube'" size="small" />
        </template>
      </Column>
      <Column field="topic" header="Тема" />
      <Column field="questions_count" header="Вопросов" :style="{ width: '100px' }">
        <template #body="s">
          <Badge :value="s.data.questions_count || 0" severity="info" />
        </template>
      </Column>
      <Column field="duration" header="Длительность">
        <template #body="s">{{ formatDuration(s.data.duration) }}</template>
      </Column>
      <Column field="processed_at" header="Обработано">
        <template #body="s">{{ formatDate(s.data.processed_at || s.data.created_at) }}</template>
      </Column>
      <Column header="Действия" :style="{ width: '120px' }">
        <template #body="s">
          <div class="action-buttons">
            <Button icon="pi pi-replay" size="small" text rounded 
                    v-tooltip="'Переобработать'" @click="reprocess(s.data)" :loading="reprocessing === s.data.id" />
          </div>
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { useToast } from 'primevue/usetoast'

const toast = useToast()
const loading = ref(false)
const videos = ref([])
const uploading = ref(false)
const uploadProgress = ref(0)
const reprocessing = ref(null)

const uploadFile = ref(null)
const uploadTitle = ref('')
const uploadTopic = ref(null)
const uploadDifficulty = ref(null)
const fileUploadRef = ref(null)

const topics = ['JavaScript', 'TypeScript', 'React', 'Vue', 'Angular', 'Node.js', 'Python', 'Java', 'C#', 'Go', 'SQL', 'DevOps', 'System Design', 'Algorithms', 'HTML/CSS', 'General']
const difficulties = [
  { label: 'Junior', value: 'junior' },
  { label: 'Middle', value: 'middle' },
  { label: 'Senior', value: 'senior' },
  { label: 'Все уровни', value: 'all' }
]

const loadVideos = async () => {
  loading.value = true
  try {
    const r = await api.getProcessedVideos()
    videos.value = r.data.videos || r.data || []
  } catch (e) { console.error(e) }
  loading.value = false
}

const onFileSelect = (event) => {
  uploadFile.value = event.files?.[0] || null
}

const uploadVideo = async () => {
  if (!uploadFile.value || !uploadTitle.value) return
  uploading.value = true
  uploadProgress.value = 0

  try {
    const formData = new FormData()
    formData.append('file', uploadFile.value)
    formData.append('title', uploadTitle.value)
    if (uploadTopic.value) formData.append('topic', uploadTopic.value)
    if (uploadDifficulty.value) formData.append('difficulty', uploadDifficulty.value)

    const r = await api.uploadVideoFile(formData, {
      onUploadProgress: (p) => {
        uploadProgress.value = Math.round((p.loaded * 100) / p.total)
      }
    })

    toast.add({ severity: 'success', summary: 'Загружено', detail: `Task ID: ${r.data.task_id}`, life: 5000 })
    uploadFile.value = null
    uploadTitle.value = ''
    uploadTopic.value = null
    uploadDifficulty.value = null
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка загрузки', detail: e.response?.data?.detail || 'Ошибка', life: 5000 })
  }
  uploading.value = false
}

const reprocess = async (video) => {
  if (!video.url) { toast.add({ severity: 'warn', summary: 'Нет URL', detail: 'Нельзя переобработать локальный файл без URL', life: 3000 }); return }
  reprocessing.value = video.id
  try {
    const r = await api.processVideo(video.url)
    toast.add({ severity: 'success', summary: 'Запущена переобработка', detail: `Task: ${r.data.task_id}`, life: 5000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: e.response?.data?.detail || 'Ошибка', life: 5000 })
  }
  reprocessing.value = null
}

const formatDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : ''
const formatDuration = (s) => {
  if (!s) return '—'
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${String(sec).padStart(2, '0')}`
}
const formatSize = (bytes) => {
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

onMounted(loadVideos)

defineExpose({ refresh: loadVideos })
</script>

<style scoped>
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.section-header h3 { display: flex; align-items: center; gap: 0.5rem; color: rgba(255,255,255,0.85); }
.loading { text-align: center; padding: 2rem; }
.empty { text-align: center; padding: 2rem; color: rgba(255,255,255,0.4); }
.upload-panel { margin-bottom: 1.5rem; }
.upload-form { display: flex; flex-direction: column; gap: 0.8rem; }
.form-row { display: flex; flex-direction: column; gap: 0.3rem; }
.form-row label { font-weight: 600; font-size: 0.85rem; color: rgba(255,255,255,0.7); }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.file-info { color: rgba(255,255,255,0.5); }
.video-title { max-width: 300px; }
.title-link { color: #667eea; text-decoration: none; }
.title-link:hover { text-decoration: underline; }
.action-buttons { display: flex; gap: 0.4rem; }
</style>
