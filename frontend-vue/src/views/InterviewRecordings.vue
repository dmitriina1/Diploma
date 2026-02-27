<template>
  <div class="recordings-page">
    <NavBar />
    <div class="page-container">
      <h1 class="page-title"><i class="pi pi-video"></i> Записи собеседований</h1>
      <p class="page-subtitle">Реальные записи IT-собеседований с извлечёнными вопросами</p>

      <div class="filters">
        <Dropdown v-model="selectedPlatform" :options="platforms" placeholder="Все платформы" showClear />
        <InputText v-model="search" placeholder="Поиск по названию..." class="search-input" />
      </div>

      <div v-if="loading" class="loading"><ProgressSpinner /></div>

      <div v-else-if="filteredVideos.length === 0" class="empty">
        <i class="pi pi-inbox"></i>
        <p>Записи не найдены</p>
      </div>

      <div v-else class="recordings-grid">
        <div v-for="video in filteredVideos" :key="video.id" class="recording-card">
          <div class="recording-header">
            <Tag :value="video.platform" severity="info" />
            <span class="recording-date">{{ formatDate(video.processed_at || video.created_at) }}</span>
          </div>
          <h3>{{ video.title || 'Без названия' }}</h3>
          <p class="recording-meta">
            <span><i class="pi pi-question-circle"></i> {{ video.question_count || 0 }} вопросов</span>
          </p>
          <div class="recording-actions">
            <Button label="Смотреть" icon="pi pi-external-link" size="small" text 
                    @click="openVideo(video.youtube_url || video.url)" />
            <Button label="Вопросы" icon="pi pi-list" size="small" outlined
                    @click="viewQuestions(video)" />
          </div>
        </div>
      </div>

      <!-- Questions Dialog -->
      <Dialog v-model:visible="showQuestions" :header="selectedVideo?.title || 'Вопросы'" 
              :style="{ width: '700px' }" modal>
        <div v-if="videoQuestions.length === 0" class="empty-dialog">
          <p>Нет извлечённых вопросов</p>
        </div>
        <div v-else class="questions-list">
          <div v-for="(q, i) in videoQuestions" :key="q.id" class="q-item">
            <span class="q-num">{{ i + 1 }}</span>
            <div class="q-content">
              <router-link :to="`/question/${q.id}`" class="q-link">{{ q.question }}</router-link>
              <div class="q-meta">
                <Tag :value="q.difficulty" :severity="diffSev(q.difficulty)" size="small" />
                <span v-if="q.timecode" class="tc"><i class="pi pi-clock"></i> {{ q.timecode }}</span>
              </div>
            </div>
          </div>
        </div>
      </Dialog>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import api from '../api/client'

const loading = ref(true)
const videos = ref([])
const search = ref('')
const selectedPlatform = ref(null)
const platforms = ['YouTube', 'RuTube', 'VK']
const showQuestions = ref(false)
const selectedVideo = ref(null)
const videoQuestions = ref([])

const filteredVideos = computed(() => {
  return videos.value.filter(v => {
    const matchSearch = !search.value || (v.title || '').toLowerCase().includes(search.value.toLowerCase())
    const matchPlatform = !selectedPlatform.value || v.platform === selectedPlatform.value
    return matchSearch && matchPlatform
  })
})

const formatDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU', { year: 'numeric', month: 'short', day: 'numeric' }) : ''
const diffSev = (d) => ({ junior: 'success', middle: 'warning', senior: 'danger' }[d] || 'info')
const openVideo = (url) => { if (url) window.open(url, '_blank') }

const viewQuestions = async (video) => {
  selectedVideo.value = video
  videoQuestions.value = []
  showQuestions.value = true
  try {
    const r = await api.getVideoQuestions?.(video.id) || await api.get(`/api/processed-videos/${video.id}/questions`)
    videoQuestions.value = r.data?.questions || r.data || []
  } catch (e) { console.error(e) }
}

onMounted(async () => {
  try {
    const r = await api.getProcessedVideos?.() || await api.get('/api/processed-videos')
    videos.value = r.data?.videos || r.data || []
  } catch (e) { console.error(e) }
  loading.value = false
})
</script>

<style scoped>
.recordings-page { min-height: 100vh; background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%); }
.page-container { max-width: 1100px; margin: 0 auto; padding: 2rem; }
.page-title { color: white; font-size: 2rem; text-align: center; margin-bottom: 0.5rem; }
.page-title i { color: #667eea; }
.page-subtitle { text-align: center; color: rgba(255,255,255,0.5); margin-bottom: 2rem; }
.filters { display: flex; gap: 1rem; margin-bottom: 2rem; justify-content: center; flex-wrap: wrap; }
.search-input { min-width: 250px; }
.loading { display: flex; justify-content: center; padding: 3rem; }
.empty { text-align: center; padding: 4rem; color: rgba(255,255,255,0.4); }
.empty i { font-size: 3rem; margin-bottom: 1rem; display: block; }

.recordings-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.25rem; }
.recording-card {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px; padding: 1.5rem; transition: all 0.2s;
}
.recording-card:hover { background: rgba(255,255,255,0.07); border-color: rgba(102,126,234,0.3); }
.recording-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.recording-date { color: rgba(255,255,255,0.4); font-size: 0.8rem; }
.recording-card h3 { color: white; font-size: 1.05rem; margin: 0 0 0.5rem; line-height: 1.4; }
.recording-meta { color: rgba(255,255,255,0.5); font-size: 0.85rem; display: flex; gap: 1rem; margin-bottom: 1rem; }
.recording-meta i { margin-right: 0.3rem; }
.recording-actions { display: flex; gap: 0.5rem; }

.empty-dialog { text-align: center; padding: 2rem; color: var(--text-color-secondary); }
.questions-list { display: flex; flex-direction: column; gap: 0.75rem; }
.q-item { display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.5rem 0; }
.q-num { background: var(--primary-color); color: white; min-width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700; }
.q-content { flex: 1; }
.q-link { color: var(--primary-color); text-decoration: none; font-weight: 500; }
.q-link:hover { text-decoration: underline; }
.q-meta { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.3rem; }
.tc { color: var(--text-color-secondary); font-size: 0.8rem; }
</style>
