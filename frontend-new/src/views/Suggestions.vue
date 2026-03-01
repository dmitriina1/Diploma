<template>
  <div class="page">
    <NavBar />
    <div class="container" style="padding-top:2rem;padding-bottom:3rem">
      <h1 class="sec-title" style="font-size:1.4rem;margin-bottom:.25rem">💡 Предложить видео</h1>
      <p class="sub">Знаете хорошее видео с IT-собеседованием? Предложите его для обработки!</p>

      <div class="card form-card">
        <!-- Mode Toggle -->
        <div class="mode-toggle">
          <button class="btn btn-sm" :class="mode === 'url' ? 'btn-primary' : 'btn-secondary'" @click="mode = 'url'">🔗 Ссылка</button>
          <button class="btn btn-sm" :class="mode === 'file' ? 'btn-primary' : 'btn-secondary'" @click="mode = 'file'">📁 Файл</button>
        </div>

        <!-- URL mode -->
        <div v-if="mode === 'url'" class="field">
          <label>Ссылка на видео *</label>
          <input v-model="form.url" class="input" placeholder="https://youtube.com/watch?v=... или rutube.ru/video/..." />
          <small v-if="detectedPlatform" class="platform-hint">{{ platformIcons[detectedPlatform] }} {{ platformNames[detectedPlatform] }}</small>
        </div>

        <!-- File upload -->
        <div v-if="mode === 'file'" class="field">
          <label>Видеофайл *</label>
          <div class="drop-zone" :class="{ over: dragging }" @dragover.prevent="dragging = true" @dragleave="dragging = false" @drop.prevent="onDrop">
            <template v-if="!selectedFile">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--c-text-4)" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>
              <p>Перетащите файл сюда или <a href="#" @click.prevent="$refs.fi.click()">выберите</a></p>
              <small>MP4, AVI, MKV, MOV, WEBM — до 2 ГБ</small>
            </template>
            <template v-else>
              <div class="file-info">
                <span class="fname">{{ selectedFile.name }}</span>
                <span class="fsize">{{ (selectedFile.size / 1024 / 1024).toFixed(1) }} MB</span>
                <button class="btn btn-ghost btn-icon btn-sm" @click="selectedFile = null">✕</button>
              </div>
            </template>
          </div>
          <input ref="fi" type="file" accept="video/*" style="display:none" @change="onFileSelect" />
          <div v-if="uploadPct > 0 && uploadPct < 100" class="progress" style="margin-top:.5rem"><div class="progress-fill" :style="{ width: uploadPct + '%' }"></div></div>
        </div>

        <div class="field">
          <label>Комментарий</label>
          <textarea v-model="form.comment" class="input" rows="3" placeholder="Почему стоит обработать это видео?"></textarea>
        </div>
        <div class="field">
          <label>Email (необязательно)</label>
          <input v-model="form.user_email" class="input" placeholder="ivan@example.com" />
        </div>
        <button class="btn btn-primary btn-lg" style="width:100%" @click="submit" :disabled="submitting || (mode === 'url' ? !form.url : !selectedFile)">
          {{ submitting ? 'Отправка...' : 'Отправить предложение' }}
        </button>
        <div v-if="feedback" class="fb-msg" :class="feedback.type">{{ feedback.text }}</div>
      </div>

      <!-- List -->
      <section v-if="suggestions.length > 0" class="list-section">
        <h2 class="sec-title" style="font-size:1.1rem;margin-bottom:1rem">Предложенные видео</h2>
        <div class="sug-list">
          <div v-for="s in suggestions" :key="s.id" class="sug-card card">
            <div class="sug-top">
              <span class="badge" :class="statusClass[s.status]">{{ statusLabels[s.status] }}</span>
              <span class="sug-plat">{{ platformIcons[s.platform] || '📹' }}</span>
            </div>
            <a :href="s.url" target="_blank" class="sug-url">{{ s.url }}</a>
            <div class="sug-meta">
              <span v-if="s.topic">{{ s.topic }}</span>
              <span v-if="s.user_name">{{ s.user_name }}</span>
              <span>{{ fmtDate(s.created_at) }}</span>
            </div>
            <p v-if="s.comment" class="sug-comment">{{ s.comment }}</p>
            <p v-if="s.admin_comment" class="sug-admin">↩ {{ s.admin_comment }}</p>
          </div>
        </div>
      </section>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import api from '../api/client'

const submitting = ref(false)
const suggestions = ref([])
const mode = ref('url')
const selectedFile = ref(null)
const dragging = ref(false)
const uploadPct = ref(0)
const feedback = ref(null)

const form = ref({ url: '', comment: '', user_email: '' })

const platformNames = { youtube: 'YouTube', vk: 'VK Video', rutube: 'Rutube', ok: 'OK.ru' }
const platformIcons = { youtube: '🎬', vk: '🔵', rutube: '🎥', ok: '🟠' }
const statusLabels = { pending: 'На рассмотрении', approved: 'Одобрено', rejected: 'Отклонено', processing: 'Обрабатывается', completed: 'Обработано' }
const statusClass = { pending: 'badge-info', approved: 'badge-ok', rejected: 'badge-err', processing: 'badge-warn', completed: 'badge-ok' }

const detectedPlatform = computed(() => {
  const u = form.value.url.toLowerCase()
  if (u.includes('youtube.com') || u.includes('youtu.be')) return 'youtube'
  if (u.includes('rutube.ru')) return 'rutube'
  if (u.includes('vk.com') || u.includes('vkvideo.ru')) return 'vk'
  if (u.includes('ok.ru')) return 'ok'
  return null
})

const onDrop = (e) => { dragging.value = false; const f = e.dataTransfer?.files?.[0]; if (f?.type.startsWith('video/')) selectedFile.value = f }
const onFileSelect = (e) => { const f = e.target.files?.[0]; if (f) selectedFile.value = f }
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : ''

const submit = async () => {
  submitting.value = true; feedback.value = null
  try {
    if (mode.value === 'file' && selectedFile.value) {
      uploadPct.value = 0
      const fd = new FormData(); fd.append('file', selectedFile.value); fd.append('topic', 'General'); fd.append('difficulty', 'middle')
      await api.uploadVideoFile(fd, { onUploadProgress: (e) => { uploadPct.value = Math.round((e.loaded * 100) / e.total) } })
      feedback.value = { type: 'ok', text: 'Видео загружено и отправлено на обработку!' }
      selectedFile.value = null; uploadPct.value = 0
    } else {
      await api.createSuggestion(form.value)
      feedback.value = { type: 'ok', text: 'Предложение отправлено на рассмотрение!' }
    }
    form.value = { url: '', comment: '', user_email: '' }
    await loadSuggestions()
  } catch (e) {
    feedback.value = { type: 'err', text: e.response?.data?.detail || 'Не удалось отправить' }
  }
  submitting.value = false
}

const loadSuggestions = async () => { try { const r = await api.getSuggestions(); suggestions.value = r.data.suggestions || [] } catch {} }
onMounted(loadSuggestions)
</script>

<style scoped>
.sub { color: var(--c-text-3); font-size: .9rem; margin-bottom: 1.5rem; }
.form-card { padding: 1.75rem; display: flex; flex-direction: column; gap: 1.1rem; }
.mode-toggle { display: flex; gap: .5rem; }
.field { display: flex; flex-direction: column; gap: .3rem; }
.field label { font-size: .85rem; color: var(--c-text-2); font-weight: 500; }
.field textarea { resize: vertical; font-family: inherit; }
.platform-hint { color: var(--c-brand); font-weight: 600; font-size: .82rem; }
.drop-zone {
  border: 2px dashed var(--c-border); border-radius: var(--r-md);
  padding: 2rem; text-align: center; cursor: pointer; transition: all var(--dur);
}
.drop-zone.over { border-color: var(--c-brand); background: var(--c-brand-bg); }
.drop-zone p { color: var(--c-text-3); margin: .3rem 0; font-size: .88rem; }
.drop-zone a { color: var(--c-brand); text-decoration: underline; cursor: pointer; }
.drop-zone small { color: var(--c-text-4); font-size: .78rem; }
.file-info { display: flex; align-items: center; gap: .75rem; }
.fname { font-weight: 600; color: var(--c-text); }
.fsize { color: var(--c-text-3); font-size: .82rem; }
.fb-msg { padding: .6rem .8rem; border-radius: var(--r-sm); font-size: .85rem; font-weight: 500; }
.fb-msg.ok { background: var(--c-ok-bg); color: var(--c-ok); }
.fb-msg.err { background: var(--c-err-bg); color: var(--c-err); }

.list-section { margin-top: 2.5rem; }
.sug-list { display: flex; flex-direction: column; gap: .5rem; }
.sug-card { padding: 1rem 1.15rem; }
.sug-top { display: flex; align-items: center; gap: .5rem; margin-bottom: .4rem; }
.sug-url { color: var(--c-brand); font-size: .82rem; word-break: break-all; text-decoration: none; }
.sug-url:hover { text-decoration: underline; }
.sug-meta { display: flex; gap: .75rem; margin-top: .35rem; font-size: .78rem; color: var(--c-text-4); }
.sug-comment { margin-top: .4rem; font-size: .85rem; color: var(--c-text-3); }
.sug-admin { margin-top: .3rem; font-size: .85rem; color: var(--c-ok); font-style: italic; }
</style>
