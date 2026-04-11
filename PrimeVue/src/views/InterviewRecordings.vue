<template>
  <div class="page">
    <NavBar />
    <div class="container-lg" style="padding-top:2rem;padding-bottom:3rem">
      <h1 class="heading h-page"><BrandIcon name="recordings" :size="34" /> Записи собеседований</h1>
      <p class="sub">Реальные записи IT-собеседований с извлечёнными вопросами</p>

      <!-- Filters -->
      <div class="filters">
        <select v-model="selectedPlatform" class="input">
          <option value="">Все платформы</option>
          <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
        </select>
        <div class="search-wrap">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
          <input v-model="search" class="input search-input" placeholder="Поиск по названию..." />
        </div>
      </div>

      <div v-if="loading" class="grid">
        <div v-for="i in 6" :key="i" class="skeleton-card">
          <div class="skeleton-line lg" style="margin-bottom:.55rem"></div>
          <div class="skeleton-line" style="width:50%;margin-bottom:.85rem"></div>
          <div class="skeleton-line" style="width:75%"></div>
        </div>
      </div>

      <StatePanel
        v-else-if="loadError"
        icon="warning"
        type="error"
        title="Не удалось загрузить записи"
        :description="loadError"
      >
        <button class="btn btn-secondary btn-sm" @click="reload">Повторить</button>
      </StatePanel>

      <StatePanel
        v-else-if="filtered.length === 0"
        icon="empty"
        title="Записи не найдены"
        description="Измени фильтры или попробуй другой поисковый запрос"
      />

      <div v-else class="grid">
        <div v-for="v in filtered" :key="v.id" class="rec-card card card-hover">
          <div class="rec-top">
            <span class="badge badge-info">{{ v.platform }}</span>
            <span class="rec-date">{{ fmtDate(v.processed_at || v.created_at) }}</span>
          </div>
          <h3>{{ v.title || 'Без названия' }}</h3>
          <p class="rec-meta">{{ videoQuestionCount(v) }} вопросов</p>
          <div class="rec-actions">
            <a v-if="v.youtube_url || v.url" :href="v.youtube_url || v.url" target="_blank" class="btn btn-ghost btn-sm">Смотреть</a>
            <button class="btn btn-secondary btn-sm" @click="viewQuestions(v)">Вопросы</button>
          </div>
        </div>
      </div>

      <!-- Questions Dialog -->
      <Teleport to="body">
        <div v-if="showDialog" class="overlay" @click.self="showDialog = false">
          <div class="dialog card">
            <div class="dialog-head">
              <h3>{{ selectedVideo?.title || 'Вопросы' }}</h3>
              <button class="btn btn-ghost btn-icon btn-sm" @click="showDialog = false">×</button>
            </div>
            <div v-if="videoQuestions.length === 0" class="dialog-empty">Нет извлечённых вопросов</div>
            <div v-else class="q-list">
              <div v-for="(q, i) in videoQuestions" :key="q.id" class="q-item">
                <span class="q-num">{{ i + 1 }}</span>
                <div class="q-body">
                  <router-link :to="'/question/' + q.id" class="q-link" @click="showDialog = false">{{ q.question }}</router-link>
                  <div class="q-meta">
                    <span class="badge" :class="diffBadge(q.difficulty)">{{ q.difficulty }}</span>
                    <span v-if="q.timecode" class="tc">{{ q.timecode }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Teleport>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import BrandIcon from '../components/BrandIcon.vue'
import StatePanel from '../components/StatePanel.vue'
import api from '../api/client'

const loading = ref(true)
const videos = ref([])
const search = ref('')
const selectedPlatform = ref('')
const platforms = ['YouTube', 'RuTube', 'VK']
const showDialog = ref(false)
const selectedVideo = ref(null)
const videoQuestions = ref([])
const loadError = ref('')

const filtered = computed(() => videos.value.filter(v => {
  const ms = !search.value || (v.title || '').toLowerCase().includes(search.value.toLowerCase())
  const mp = !selectedPlatform.value || v.platform === selectedPlatform.value
  return ms && mp
}))

const fmtDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU', { year: 'numeric', month: 'short', day: 'numeric' }) : ''
const diffBadge = (d) => ({ junior: 'badge-ok', middle: 'badge-warn', senior: 'badge-err' }[d] || 'badge-muted')
const videoQuestionCount = (v) => {
  const raw = v?.question_count ?? v?.questions_count ?? v?.linked_questions ?? 0
  const n = Number(raw)
  return Number.isFinite(n) ? n : 0
}

const viewQuestions = async (v) => {
  selectedVideo.value = v; videoQuestions.value = []; showDialog.value = true
  try { const r = await api.getVideoQuestions(v.id); videoQuestions.value = r.data?.questions || [] } catch (e) { console.error(e) }
}

const reload = async () => {
  loading.value = true
  loadError.value = ''
  try { const r = await api.getProcessedVideos(); videos.value = r.data?.videos || [] }
  catch (e) { console.error(e); loadError.value = 'Сервис записей временно недоступен.' }
  loading.value = false
}

onMounted(async () => {
  await reload()
})
</script>

<style scoped>
.heading { display:flex; align-items:center; justify-content:center; gap:.55rem; margin-bottom: .35rem; }
.sub { text-align: center; color: var(--c-text-3); font-size: .94rem; margin-bottom: 1.5rem; }
.filters { display: flex; gap: .75rem; justify-content: center; margin-bottom: 1.5rem; flex-wrap: wrap; }
.filters .input { min-width: 180px; }
.search-wrap { position: relative; min-width: 240px; }
.search-icon { position: absolute; left: .65rem; top: 50%; transform: translateY(-50%); color: var(--c-text-4); pointer-events: none; }
.search-input { padding-left: 2.1rem; width: 100%; }
.center-block { display: flex; justify-content: center; padding: 3rem; }
.empty-state { text-align: center; padding: 3rem; color: var(--c-text-4); }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }
.rec-card { padding: 1.25rem; display: flex; flex-direction: column; }
.rec-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: .5rem; }
.rec-date { color: var(--c-text-4); font-size: .84rem; }
.rec-card h3 { font-size: 1.06rem; font-weight: 600; margin-bottom: .35rem; line-height: 1.35; }
.rec-meta { color: var(--c-text-3); font-size: .88rem; margin-bottom: .75rem; flex: 1; }
.rec-actions { display: flex; gap: .4rem; }

/* Dialog */
.overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0,0,0,.6); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; padding: 1.5rem;
}
.dialog { width: 100%; max-width: 640px; max-height: 80vh; overflow-y: auto; padding: 1.5rem; }
.dialog-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.dialog-head h3 { font-size: 1.1rem; font-weight: 600; }
.dialog-empty { text-align: center; padding: 2rem; color: var(--c-text-4); }
.q-list { display: flex; flex-direction: column; gap: .6rem; }
.q-item { display: flex; align-items: flex-start; gap: .65rem; padding: .4rem 0; }
.q-num {
  min-width: 26px; height: 26px; border-radius: 50%;
  background: var(--c-brand); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: .75rem; font-weight: 700;
}
.q-body { flex: 1; }
.q-link { color: var(--c-brand); text-decoration: none; font-weight: 500; font-size: .96rem; }
.q-link:hover { text-decoration: underline; }
.q-meta { display: flex; align-items: center; gap: .4rem; margin-top: .2rem; }
.tc { color: var(--c-text-4); font-size: .84rem; }

@media (max-width: 640px) {
  .grid { grid-template-columns: 1fr; }
  .filters { flex-direction: column; }
  .search-wrap { min-width: auto; width: 100%; }
}
</style>
