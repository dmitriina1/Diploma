<template>
  <div class="page recordings-page">
    <NavBar />
    <main class="screen recordings">
      <section class="page-title">
        <div>
          <h1>Загруженные собеседования</h1>
          <p>Ваши записи интервью и результаты анализа</p>
        </div>
        <button class="btn primary" @click="uploadOpen = true"><i class="pi pi-cloud-upload"></i>Загрузить запись</button>
      </section>

      <div class="records-grid">
        <aside>
          <input v-model="search" class="field" placeholder="Поиск по собеседованиям..." />
          <div class="side-head">Название собеседования</div>
          <button v-for="rec in paginatedRecordings" :key="rec.id" class="rec-item" @click="viewQuestions(rec)">
            <span><i class="pi pi-play"></i></span>
            <b>{{ rec.title }}</b>
            <small>{{ rec.role }}</small>
          </button>
        </aside>

        <section class="glass rec-table">
          <div class="table-row table-head">
            <span></span><span>Длительность</span><span>Дата <i class="pi pi-sort-alt"></i></span><span></span>
          </div>
          <div v-for="rec in paginatedRecordings" :key="rec.id" class="table-row" :class="{ active: selectedVideo?.id === rec.id }" @click="viewQuestions(rec)">
            <span></span><span>{{ rec.duration }}</span><span>{{ rec.date }}</span><button @click.stop="openActions(rec)">...</button>
          </div>
          <footer v-if="totalPages > 1">
            <button class="page-arrow" :disabled="page <= 1" @click="goToPage(page - 1)"><i class="pi pi-angle-left"></i></button>
            <button
              v-for="item in visiblePages"
              :key="item.key"
              :class="{ active: item.value === page, ellipsis: item.type === 'ellipsis' }"
              :disabled="item.type === 'ellipsis'"
              @click="item.type === 'page' && goToPage(item.value)"
            >
              {{ item.label }}
            </button>
            <button class="page-arrow" :disabled="page >= totalPages" @click="goToPage(page + 1)"><i class="pi pi-angle-right"></i></button>
          </footer>
        </section>
      </div>
    </main>

    <div v-if="modalOpen" class="modal-layer" @click.self="modalOpen = false">
      <section class="modal neon-border">
        <button class="close" @click="modalOpen = false"><i class="pi pi-times"></i></button>
        <h2>{{ selectedVideo?.title || 'Собеседование на Backend Developer' }}</h2>
        <p>Запись от {{ selectedVideo?.date || '23 мая 2025' }} <span>•</span> {{ selectedVideo?.duration || '54:32' }} <span>•</span> {{ modalQuestions.length }} вопросов</p>
        <div class="modal-list">
          <div v-for="q in modalQuestions" :key="q.id">
            <b>{{ q.id }}</b>
            <router-link :to="`/question/${q.id}`" @click="modalOpen = false">{{ q.title || q.question }}</router-link>
            <em :class="`tag ${q.level || q.difficulty || 'junior'}`">{{ q.level || q.difficulty || 'junior' }}</em>
            <i class="pi pi-angle-right"></i>
          </div>
        </div>
        <footer><span><i class="pi pi-sparkles"></i>Вопросы выделены и сгенерированы AI. Возможны неточности.</span><button class="btn small"><i class="pi pi-copy"></i>Скопировать список</button></footer>
      </section>
    </div>

    <div v-if="uploadOpen" class="modal-layer" @click.self="uploadOpen = false">
      <section class="modal upload-modal neon-border">
        <button class="close" @click="uploadOpen = false"><i class="pi pi-times"></i></button>
        <h2>Загрузить запись</h2>
        <p>Добавьте ссылку на видео или выберите локальный файл для запуска обработки.</p>
        <div class="upload-tabs">
          <button :class="{ active: uploadMode === 'url' }" @click="uploadMode = 'url'">Ссылка</button>
          <button :class="{ active: uploadMode === 'file' }" @click="uploadMode = 'file'">Файл</button>
        </div>
        <input v-if="uploadMode === 'url'" v-model="uploadUrl" class="field" placeholder="https://youtube.com/watch?v=..." />
        <input v-else type="file" class="field file-field" accept="video/*" @change="uploadFile = $event.target.files[0]" />
        <button class="btn primary" :disabled="uploadBusy || (uploadMode === 'url' ? !uploadUrl : !uploadFile)" @click="submitUpload">{{ uploadBusy ? 'Отправляем...' : 'Запустить обработку' }}</button>
      </section>
    </div>
    <div v-if="toast" class="toast">{{ toast }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import NavBar from '../components/NavBar.vue'
import api from '../api/client'
import { recordings as fallbackRecordings, extractedQuestions } from '../data/mock'

const demoRecordings = [
  ['Golang Developer Interview', 'Golang Developer', '49:20', '15 мая 2025'],
  ['Java System Design Interview', 'Java Developer', '1:08:14', '14 мая 2025'],
  ['ML Engineer Interview', 'ML Engineer', '57:36', '13 мая 2025'],
  ['Product Analyst Interview', 'Product Analyst', '42:18', '12 мая 2025']
].map((item, index) => ({ id: `demo-${index + 1}`, title: item[0], role: item[1], duration: item[2], date: item[3] }))
const recordings = ref([...fallbackRecordings, ...demoRecordings])
const modalOpen = ref(false)
const uploadOpen = ref(false)
const selectedVideo = ref(fallbackRecordings[0])
const modalQuestions = ref(extractedQuestions)
const search = ref('')
const page = ref(1)
const pageSize = 8
const uploadMode = ref('url')
const uploadUrl = ref('')
const uploadFile = ref(null)
const uploadBusy = ref(false)
const toast = ref('')

const filteredRecordings = computed(() => {
  const q = search.value.toLowerCase()
  return recordings.value.filter((item) => !q || [item.title, item.role].join(' ').toLowerCase().includes(q))
})
const totalPages = computed(() => Math.max(1, Math.ceil(filteredRecordings.value.length / pageSize)))
const paginatedRecordings = computed(() => filteredRecordings.value.slice((page.value - 1) * pageSize, page.value * pageSize))
const visiblePages = computed(() => {
  const pages = new Set([1, totalPages.value, page.value, page.value - 1, page.value + 1])
  const normalized = [...pages].filter((p) => p >= 1 && p <= totalPages.value).sort((a, b) => a - b)
  const result = []
  normalized.forEach((p, index) => {
    const prev = normalized[index - 1]
    if (index > 0 && p - prev > 1) result.push({ type: 'ellipsis', key: `ellipsis-${prev}-${p}`, label: '...' })
    result.push({ type: 'page', key: `page-${p}`, value: p, label: p })
  })
  return result
})
const showToast = (msg) => { toast.value = msg; setTimeout(() => { toast.value = '' }, 2200) }

function goToPage(nextPage) {
  page.value = Math.min(Math.max(nextPage, 1), totalPages.value)
}
watch(search, () => { page.value = 1 })

function selectRecording(video) {
  selectedVideo.value = video
}

function openActions(video) {
  selectedVideo.value = video
  viewQuestions(video)
}

async function loadRecordings() {
  try {
    const r = await api.getProcessedVideos()
    const list = r.data.videos || []
    if (list.length) recordings.value = list.map((v) => ({
      ...v,
      title: v.title || 'Без названия',
      role: v.profession || v.platform || 'Interview',
      duration: v.duration || v.duration_text || '—',
      date: v.processed_at ? new Date(v.processed_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'
    }))
  } catch {}
}

async function viewQuestions(video) {
  selectedVideo.value = video
  modalOpen.value = true
  modalQuestions.value = extractedQuestions
  try {
    const r = await api.getVideoQuestions(video.id)
    const list = r.data.questions || []
    if (list.length) modalQuestions.value = list
  } catch {}
}

async function submitUpload() {
  uploadBusy.value = true
  try {
    if (uploadMode.value === 'url') await api.processVideoWithClient({ video_url: uploadUrl.value })
    else {
      const fd = new FormData()
      fd.append('file', uploadFile.value)
      await api.uploadVideoFile(fd)
    }
    uploadOpen.value = false
    showToast('Видео отправлено на обработку')
    await loadRecordings()
  } catch {
    showToast('Не удалось запустить обработку')
  }
  uploadBusy.value = false
}

onMounted(loadRecordings)
</script>

<style scoped>
.recordings { padding-top: 34px; }
.records-grid { display: grid; grid-template-columns: 470px 1fr; gap: 42px; align-items: start; }
aside .field { height: 56px; margin-bottom: 20px; }
.side-head { height: 80px; display: flex; align-items: center; color: var(--soft); text-transform: uppercase; font-size: 14px; font-weight: 800; margin: 0 0 0 90px; }
.rec-item {
  width: 100%;
  min-height: 80px;
  display: grid;
  grid-template-columns: 58px 1fr;
  column-gap: 18px;
  align-items: center;
  text-align: left;
  border: 0;
  border-bottom: 1px solid rgba(83, 121, 148, .12);
  background: transparent;
  color: var(--text);
  padding: 0 0 0 18px;
}
.rec-item:hover { background: rgba(8, 31, 54, .32); }
.rec-item span { grid-row: span 2; width: 48px; height: 48px; display: grid; place-items: center; border: 1px solid rgba(18, 230, 209, .22); border-radius: var(--radius); color: var(--cyan); }
.rec-item b { font-size: 18px; }
.rec-item small { color: var(--muted); font-size: 16px; }
.rec-table { margin-top: 70px; overflow: hidden; }
.rec-table .table-row { grid-template-columns: 1fr 170px 170px 80px; min-height: 80px; padding: 0 26px; color: var(--muted); }
.rec-table .table-row.active { background: rgba(18, 230, 209, .04); }
.rec-table button { background: none; border: 0; color: var(--muted); font-size: 24px; }
.rec-table footer { height: 90px; display: flex; justify-content: center; align-items: center; gap: 10px; color: var(--muted); }
.rec-table footer button { width: 42px; height: 42px; border-radius: 10px; display: grid; place-items: center; border: 1px solid rgba(83, 121, 148, .16); background: rgba(4, 20, 37, .62); color: var(--text); font-size: 16px; font-weight: 800; transition: .18s ease; }
.rec-table footer button:not(:disabled):hover { color: var(--cyan); border-color: var(--line-strong); }
.rec-table footer button:disabled { opacity: .45; cursor: not-allowed; }
.rec-table footer .active { background: rgba(18, 230, 209, .28); color: var(--cyan); border-color: transparent; }
.rec-table footer .ellipsis { background: transparent; border-color: transparent; color: var(--soft); }
.page-arrow { width: 42px; height: 42px; border: 1px solid rgba(83, 121, 148, .16) !important; border-radius: 10px; }

.modal-layer { position: fixed; inset: 92px 0 0; display: grid; place-items: start center; padding-top: 18px; background: rgba(2, 13, 27, .28); z-index: 30; }
.modal {
  width: 835px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(5, 24, 44, .98), rgba(4, 23, 42, .98));
  padding: 28px 34px 18px;
  position: relative;
}
.close { position: absolute; right: 28px; top: 28px; background: none; border: 0; color: var(--muted); font-size: 24px; }
.modal h2 { margin: 0 0 8px; font-size: 28px; }
.modal p { margin: 0 0 24px; color: var(--muted); font-size: 18px; }
.modal p span { margin: 0 10px; }
.modal-list { display: grid; gap: 8px; }
.modal-list div {
  min-height: 54px;
  display: grid;
  grid-template-columns: 42px 1fr 92px 28px;
  align-items: center;
  gap: 16px;
  border: 1px solid rgba(83, 121, 148, .16);
  background: rgba(11, 42, 65, .72);
  border-radius: 10px;
  padding: 0 14px;
}
.modal-list b { width: 36px; height: 36px; display: grid; place-items: center; border-radius: 9px; background: rgba(18, 230, 209, .11); color: #b9f9f4; }
.modal-list span { font-size: 17px; }
.modal-list a { font-size: 17px; color: var(--text); }
.modal-list i { color: var(--muted); }
.modal footer { display: flex; justify-content: space-between; align-items: center; color: var(--muted); margin-top: 22px; }
.upload-modal { display: grid; gap: 16px; }
.upload-tabs { display: flex; gap: 10px; }
.upload-tabs button { height: 42px; padding: 0 20px; border-radius: 8px; border: 1px solid rgba(83, 137, 174, .2); background: rgba(4, 20, 37, .62); color: var(--text); }
.upload-tabs .active { background: var(--cyan); color: #032b31; }
.file-field { padding-top: 16px; }

@media (max-width: 1100px) {
  .records-grid { grid-template-columns: 1fr; }
  .modal { width: calc(100vw - 32px); }
}
</style>
