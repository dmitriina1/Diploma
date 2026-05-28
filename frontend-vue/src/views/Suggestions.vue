<template>
  <div class="suggest-page">
    <NavBar />
    
    <div class="page-container">
      <header class="page-header">
        <h1><i class="pi pi-lightbulb"></i> Предложить видео</h1>
        <p class="subtitle">Знаете хорошее видео с IT-собеседованием? Предложите его для обработки!</p>
      </header>

      <!-- Форма предложения -->
      <Card class="suggest-card">
        <template #content>
          <div class="form-grid">
            <!-- Mode toggle -->
            <div class="mode-toggle">
              <Button :label="inputMode === 'url' ? '🔗 Ссылка' : '🔗 Ссылка'" size="small"
                      :severity="inputMode === 'url' ? 'primary' : 'secondary'"
                      :outlined="inputMode !== 'url'"
                      @click="inputMode = 'url'" />
              <Button :label="inputMode === 'file' ? '📁 Файл' : '📁 Файл'" size="small"
                      :severity="inputMode === 'file' ? 'primary' : 'secondary'"
                      :outlined="inputMode !== 'file'"
                      @click="inputMode = 'file'" />
            </div>

            <!-- URL mode -->
            <div v-if="inputMode === 'url'" class="field">
              <label>Ссылка на видео *</label>
              <InputText v-model="form.url" placeholder="https://youtube.com/watch?v=... или rutube.ru/video/..." class="w-full" />
              <small v-if="detectedPlatform" class="platform-badge">
                {{ platformIcons[detectedPlatform] }} {{ platformNames[detectedPlatform] }}
              </small>
            </div>

            <!-- File upload mode -->
            <div v-if="inputMode === 'file'" class="field">
              <label>Видеофайл *</label>
              <div class="file-drop-zone" :class="{ 'drag-over': isDragging }"
                   @dragover.prevent="isDragging = true" @dragleave="isDragging = false"
                   @drop.prevent="handleFileDrop">
                <div v-if="!selectedFile" class="drop-placeholder">
                  <i class="pi pi-cloud-upload"></i>
                  <p>Перетащите видеофайл сюда или <a href="#" @click.prevent="$refs.fileInput.click()">выберите</a></p>
                  <small>MP4, AVI, MKV, MOV, WEBM — до 2 ГБ</small>
                </div>
                <div v-else class="drop-selected">
                  <i class="pi pi-file-edit"></i>
                  <div>
                    <strong>{{ selectedFile.name }}</strong>
                    <small>{{ (selectedFile.size / 1024 / 1024).toFixed(1) }} MB</small>
                  </div>
                  <Button icon="pi pi-times" size="small" text severity="danger" @click="selectedFile = null" />
                </div>
              </div>
              <input ref="fileInput" type="file" accept="video/*" style="display:none" @change="handleFileSelect" />
              <ProgressBar v-if="uploadProgress > 0 && uploadProgress < 100" :value="uploadProgress" :showValue="true" class="mt-2" />
            </div>

            <div class="field">
              <label>Комментарий</label>
              <Textarea v-model="form.comment" rows="3" placeholder="Почему стоит обработать это видео?" class="w-full" />
            </div>

            <div class="field">
              <label>Email (необязательно)</label>
              <InputText v-model="form.user_email" placeholder="ivan@example.com" class="w-full" />
            </div>

            <Button label="Отправить предложение" icon="pi pi-send" @click="submitSuggestion" 
                    :loading="submitting" :disabled="inputMode === 'url' ? !form.url : !selectedFile" class="submit-btn" />
          </div>
        </template>
      </Card>

      <!-- Список предложений -->
      <section class="suggestions-list" v-if="suggestions.length > 0">
        <h2><i class="pi pi-list"></i> Предложенные видео</h2>
        <div class="suggestion-cards">
          <div v-for="s in suggestions" :key="s.id" class="suggestion-item">
            <div class="suggestion-header">
              <Tag :value="statusLabels[s.status]" :severity="statusSeverity[s.status]" />
              <span class="suggestion-platform">{{ platformIcons[s.platform] || '📹' }}</span>
            </div>
            <a :href="s.url" target="_blank" class="suggestion-url">{{ s.url }}</a>
            <div class="suggestion-meta">
              <span v-if="s.topic"><i class="pi pi-tag"></i> {{ s.topic }}</span>
              <span v-if="s.user_name"><i class="pi pi-user"></i> {{ s.user_name }}</span>
              <span class="suggestion-date"><i class="pi pi-calendar"></i> {{ formatDate(s.created_at) }}</span>
            </div>
            <p v-if="s.comment" class="suggestion-comment">{{ s.comment }}</p>
            <p v-if="s.admin_comment" class="admin-comment"><i class="pi pi-reply"></i> {{ s.admin_comment }}</p>
          </div>
        </div>
      </section>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import api from '../api/client'
import { useToast } from 'primevue/usetoast'

const toast = useToast()
const submitting = ref(false)
const suggestions = ref([])
const inputMode = ref('url')
const selectedFile = ref(null)
const isDragging = ref(false)
const uploadProgress = ref(0)

const form = ref({
  url: '',
  topic: '',
  difficulty: 'middle',
  comment: '',
  user_name: '',
  user_email: ''
})

const topicOptions = ['JavaScript', 'Python', 'Java', 'C#', 'React', 'Vue', 'Angular', 'Node.js', 'Docker', 'Kubernetes', 'SQL', 'System Design', 'Algorithms', 'DevOps', 'Backend', 'Frontend', 'General']
const difficultyOptions = [
  { label: 'Junior', value: 'junior' },
  { label: 'Middle', value: 'middle' },
  { label: 'Senior', value: 'senior' }
]

const platformNames = { youtube: 'YouTube', vk: 'VK Video', rutube: 'Rutube', ok: 'OK.ru', dailymotion: 'Dailymotion', vimeo: 'Vimeo' }
const platformIcons = { youtube: '🎬', vk: '🔵', rutube: '🎥', ok: '🟠', dailymotion: '🎞️', vimeo: '💙' }
const statusLabels = { pending: 'На рассмотрении', approved: 'Одобрено', rejected: 'Отклонено', processing: 'Обрабатывается', completed: 'Обработано' }
const statusSeverity = { pending: 'info', approved: 'success', rejected: 'danger', processing: 'warning', completed: 'success' }

const detectedPlatform = computed(() => {
  const url = form.value.url.toLowerCase()
  if (url.includes('youtube.com') || url.includes('youtu.be')) return 'youtube'
  if (url.includes('rutube.ru')) return 'rutube'
  if (url.includes('vk.com') || url.includes('vkvideo.ru')) return 'vk'
  if (url.includes('ok.ru')) return 'ok'
  if (url.includes('dailymotion.com')) return 'dailymotion'
  if (url.includes('vimeo.com')) return 'vimeo'
  return null
})

const submitSuggestion = async () => {
  submitting.value = true
  try {
    if (inputMode.value === 'file' && selectedFile.value) {
      // File upload mode — use the upload-video-file endpoint
      uploadProgress.value = 0
      const formData = new FormData()
      formData.append('file', selectedFile.value)
      formData.append('topic', form.value.topic || 'General')
      formData.append('difficulty', form.value.difficulty || 'middle')
      const response = await api.uploadVideoFile(formData, {
        onUploadProgress: (e) => { uploadProgress.value = Math.round((e.loaded * 100) / e.total) }
      })
      toast.add({ severity: 'success', summary: 'Загружено!', detail: `Видео отправлено на обработку (${response.data?.task_id || ''})`, life: 5000 })
      selectedFile.value = null
      uploadProgress.value = 0
    } else {
      // URL mode — use suggestions endpoint
      await api.createSuggestion(form.value)
      toast.add({ severity: 'success', summary: 'Отправлено!', detail: 'Ваше предложение отправлено на рассмотрение', life: 5000 })
    }
    form.value = { url: '', topic: '', difficulty: 'middle', comment: '', user_name: '', user_email: '' }
    await loadSuggestions()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: e.response?.data?.detail || 'Не удалось отправить', life: 5000 })
  } finally {
    submitting.value = false
  }
}

const handleFileDrop = (e) => {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file && file.type.startsWith('video/')) {
    selectedFile.value = file
  }
}

const handleFileSelect = (e) => {
  const file = e.target.files?.[0]
  if (file) selectedFile.value = file
}

const loadSuggestions = async () => {
  try {
    const r = await api.getSuggestions()
    suggestions.value = r.data.suggestions || []
  } catch (e) { console.error(e) }
}

const formatDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : ''

onMounted(loadSuggestions)
</script>

<style scoped>
.suggest-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #0f0f1e 0%, #1a1a2e 50%, #16213e 100%);
}
.page-container { max-width: 900px; margin: 0 auto; padding: 1.5rem 2rem 3rem; }
.page-header { margin-bottom: 2rem; }
.page-header h1 {
  display: flex; align-items: center; gap: 0.75rem;
  font-size: 1.8rem; font-weight: 800;
  background: linear-gradient(135deg, #667eea, #f093fb);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.subtitle { color: rgba(255,255,255,0.5); margin-top: 0.3rem; }
.suggest-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; }
.form-grid { display: flex; flex-direction: column; gap: 1.2rem; }
.field label { display: block; margin-bottom: 0.4rem; font-weight: 600; color: rgba(255,255,255,0.7); font-size: 0.9rem; }
.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.platform-badge { color: #667eea; font-weight: 600; }
.submit-btn { width: 100%; font-weight: 700; padding: 0.8rem; }
.suggestions-list { margin-top: 2.5rem; }
.suggestions-list h2 { display: flex; align-items: center; gap: 0.5rem; font-size: 1.3rem; margin-bottom: 1rem; color: rgba(255,255,255,0.85); }
.suggestion-cards { display: flex; flex-direction: column; gap: 0.75rem; }
.suggestion-item {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px; padding: 1rem 1.25rem;
}
.suggestion-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
.suggestion-url { color: #667eea; font-size: 0.85rem; word-break: break-all; text-decoration: none; }
.suggestion-url:hover { text-decoration: underline; }
.suggestion-meta { display: flex; gap: 1rem; margin-top: 0.4rem; font-size: 0.8rem; color: rgba(255,255,255,0.45); }
.suggestion-meta span { display: flex; align-items: center; gap: 0.25rem; }
.suggestion-comment { margin-top: 0.5rem; font-size: 0.85rem; color: rgba(255,255,255,0.6); }
.admin-comment { margin-top: 0.4rem; font-size: 0.85rem; color: #4ade80; font-style: italic; }

.mode-toggle { display: flex; gap: 0.5rem; }
.file-drop-zone {
  border: 2px dashed rgba(255,255,255,0.15); border-radius: 12px;
  padding: 2rem; text-align: center; transition: all 0.2s; cursor: pointer;
}
.file-drop-zone.drag-over { border-color: #667eea; background: rgba(102,126,234,0.08); }
.drop-placeholder i { font-size: 2.5rem; color: rgba(255,255,255,0.3); margin-bottom: 0.5rem; display: block; }
.drop-placeholder p { color: rgba(255,255,255,0.6); margin: 0.3rem 0; }
.drop-placeholder a { color: #667eea; text-decoration: underline; cursor: pointer; }
.drop-placeholder small { color: rgba(255,255,255,0.35); }
.drop-selected {
  display: flex; align-items: center; gap: 1rem; text-align: left;
}
.drop-selected i { font-size: 2rem; color: #667eea; }
.drop-selected strong { display: block; color: white; }
.drop-selected small { color: rgba(255,255,255,0.45); }

@media (max-width: 768px) {
  .field-row { grid-template-columns: 1fr; }
  .page-container { padding: 1rem; }
}
</style>
