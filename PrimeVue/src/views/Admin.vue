<template>
  <div class="page admin-page">
    <NavBar />
    <main class="screen admin">
      <section class="admin-head">
        <div>
          <h1>Админ-панель</h1>
          <p>Модерация вопросов, видео, заданий и обратной связи</p>
        </div>
        <button class="btn primary" @click="showUpload = true"><i class="pi pi-cloud-upload"></i>Загрузить видео</button>
      </section>

      <section v-if="showCompleteBanner" class="complete glass neon-border">
        <button class="complete-close" title="Скрыть навсегда" @click="dismissCompleteBanner"><i class="pi pi-times"></i></button>
        <div class="check"><i class="pi pi-check"></i></div>
        <div>
          <h1>Обработка видео завершена</h1>
          <p>Все вопросы успешно извлечены и готовы к использованию</p>
          <button @click="showProcessingDetails = !showProcessingDetails"><i class="pi pi-chart-line"></i>{{ showProcessingDetails ? 'Скрыть детали обработки' : 'Показать детали обработки' }} <i :class="showProcessingDetails ? 'pi pi-angle-up' : 'pi pi-angle-down'"></i></button>
          <div v-if="showProcessingDetails" class="processing-details">
            <span>Скачивание: 100%</span>
            <span>Транскрибация Whisper: 100%</span>
            <span>Извлечение LLM: 12 вопросов</span>
          </div>
        </div>
        <div class="summary"><span>Источник</span><b><em>▶</em>YouTube</b></div>
        <div class="summary"><span>Длительность</span><b>19:04</b></div>
        <div class="summary"><span>Обработано</span><b>19.04.2024, 10:37</b></div>
        <div class="complete-actions">
          <button class="btn" @click="openPlayer"><i class="pi pi-play-circle"></i>Открыть в плеере</button>
          <button class="btn" @click="showCompleteActions = !showCompleteActions">Ещё действия <i class="pi pi-angle-down"></i></button>
          <div v-if="showCompleteActions" class="action-menu">
            <button @click="copyProcessingSummary">Скопировать сводку</button>
            <button @click="showUpload = true">Загрузить новое видео</button>
            <button @click="dismissCompleteBanner">Скрыть плашку</button>
          </div>
        </div>
      </section>

      <nav class="tabs">
        <a v-for="(tab, index) in tabs" :key="tab" :class="{ active: activeTab === index }" @click="activeTab = index">{{ tab }}</a>
      </nav>

      <section v-if="activeTab === 0" class="admin-tools">
        <button class="btn primary" :disabled="busy" @click="bulkGenerate"><i class="pi pi-sparkles"></i>{{ busy ? 'Генерация...' : 'Массовая генерация ответов' }}</button>
        <div class="toolbar">
          <input v-model="search" class="field" placeholder="Поиск по вопросам..." />
          <select v-model="topic" class="field"><option value="">Все темы</option><option v-for="item in topics" :key="item">{{ item }}</option></select>
          <select v-model="status" class="field"><option value="">Все статусы</option><option value="approved">Одобренные</option><option value="pending">Не одобренные</option></select>
          <button class="btn"><i class="pi pi-filter"></i>Фильтры</button>
        </div>
      </section>
      <section v-else class="admin-tools compact-tools">
        <button class="btn primary" @click="openEntityModal(null)"><i class="pi pi-plus"></i>{{ createButtonLabel }}</button>
        <button class="btn" @click="loadAdminData"><i class="pi pi-refresh"></i>Обновить данные</button>
      </section>

      <section v-if="activeTab === 0" class="glass admin-table">
        <div class="table-row table-head">
          <span><input type="checkbox" /></span><span>Вопрос</span><span>Тема</span><span>Сложность</span><span>Уверенность</span><span>Статус</span><span>Ответ</span><span>Действия</span>
        </div>
        <div v-for="row in paginatedRows" :key="row.id || row.title" class="table-row" @click="openQuestionModal(row)">
          <span><input type="checkbox" :checked="selectedIds.includes(row.id)" @click.stop @change="toggleRow(row.id)" /></span>
          <span>{{ row.title }}</span>
          <span><b :class="row.topic === 'General' ? 'tag purple' : 'tag'">{{ row.topic }}</b></span>
          <span><b :class="`tag ${row.level}`">{{ row.level }}</b></span>
          <span class="confidence">{{ row.conf }}% <i class="progress-line"><span :style="{ width: row.conf + '%' }"></span></i></span>
          <span><b :class="`tag ${row.status ? 'ok' : 'middle'}`">{{ row.status ? 'Да' : 'Нет' }}</b></span>
          <span>{{ row.answer ? 'Есть' : '—' }}</span>
          <span class="row-actions"><button @click.stop="toggleApprove(row)">{{ row.status ? 'Снять' : 'Одобрить' }}</button><button class="danger" @click.stop="deleteRow(row)"><i class="pi pi-trash"></i></button></span>
        </div>
      </section>
      <section v-else-if="activeTab === 4" class="assignment-admin-grid">
        <article v-for="item in activeEntities" :key="item.id" class="assignment-admin-card glass" @click="openEntityModal(item)">
          <header>
            <span :class="`tag ${item.level || 'middle'}`">{{ item.level || 'middle' }}</span>
            <div class="company"><span>{{ item.company }}</span><b>{{ item.logo }}</b></div>
          </header>
          <h2>{{ item.title }}</h2>
          <p>{{ item.text }}</p>
          <small>{{ item.role }}</small>
          <div class="tags"><span v-for="skill in item.skills" :key="skill" class="tag">{{ skill }}</span></div>
          <footer><b>{{ item.status }}</b><button @click.stop="openEntityModal(item)">Редактировать</button></footer>
        </article>
      </section>

      <section v-else-if="activeTab === 5" class="analytics-board">
        <article v-for="item in analyticsCards" :key="item.title" class="glass analytics-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.title }}</p>
        </article>
        <div class="glass analytics-actions">
          <h2>Очередь улучшений</h2>
          <button v-for="item in analyticsActions" :key="item"><i class="pi pi-arrow-right"></i>{{ item }}</button>
        </div>
      </section>

      <section v-else class="admin-list">
        <article v-for="item in activeEntities" :key="item.id" class="glass admin-list-row" :class="{ video: activeTab === 3 }" @click="openEntityModal(item)">
          <span :class="`tag ${item.statusType || 'ok'}`">{{ item.status }}</span>
          <div class="platform" v-if="activeTab === 3"><i :class="item.icon"></i></div>
          <div>
            <h2>{{ item.title }}</h2>
            <p>{{ item.text }}</p>
          </div>
          <b>{{ item.meta }}</b>
          <button @click.stop="openEntityModal(item)">Редактировать</button>
        </article>
      </section>
      <footer v-if="activeTab === 0" class="admin-footer">
        <span>Показано {{ firstShown }}–{{ lastShown }} из {{ filteredRows.length }} вопросов</span>
      </footer>
      <nav v-if="activeTab === 0 && totalPages > 1" class="admin-pagination">
        <button :disabled="page <= 1" @click="goToPage(page - 1)"><i class="pi pi-angle-left"></i></button>
        <button v-for="item in visiblePages" :key="item.key" :class="{ active: item.value === page, ellipsis: item.type === 'ellipsis' }" :disabled="item.type === 'ellipsis'" @click="item.type === 'page' && goToPage(item.value)">{{ item.label }}</button>
        <button :disabled="page >= totalPages" @click="goToPage(page + 1)"><i class="pi pi-angle-right"></i></button>
      </nav>
    </main>

    <div v-if="questionModalOpen" class="modal-layer" @click.self="questionModalOpen = false">
      <section class="modal neon-border edit-modal">
        <button class="close" @click="questionModalOpen = false"><i class="pi pi-times"></i></button>
        <h2>Редактирование вопроса</h2>
        <label>Вопрос<input v-model="editQuestion.title" class="field" /></label>
        <label>Тема<input v-model="editQuestion.topic" class="field" /></label>
        <label>Ответ<textarea v-model="editQuestion.answerText" class="field"></textarea></label>
        <div class="modal-actions">
          <button class="btn" @click="questionModalOpen = false">Отмена</button>
          <button class="btn primary" @click="saveQuestionModal">Сохранить</button>
        </div>
      </section>
    </div>

    <div v-if="entityModalOpen" class="modal-layer" @click.self="entityModalOpen = false">
      <section class="modal neon-border edit-modal">
        <button class="close" @click="entityModalOpen = false"><i class="pi pi-times"></i></button>
        <h2>{{ entityDraft.id ? 'Редактирование карточки' : modalTitle }}</h2>
        <div class="modal-section">
          <h3><i class="pi pi-info-circle"></i>Основное</h3>
          <label>Название<input v-model="entityDraft.title" class="field" /></label>
          <label>Описание<textarea v-model="entityDraft.text" class="field"></textarea></label>
          <label>Статус<input v-model="entityDraft.status" class="field" /></label>
        </div>
        <div v-if="activeTab === 1" class="modal-section two-cols">
          <label>Автор<input v-model="entityDraft.author" class="field" /></label>
          <label>Ссылка<input v-model="entityDraft.link" class="field" placeholder="https://..." /></label>
        </div>
        <div v-if="activeTab === 2" class="modal-section two-cols">
          <label>Тип обращения<input v-model="entityDraft.type" class="field" /></label>
          <label>Email<input v-model="entityDraft.email" class="field" /></label>
        </div>
        <div v-if="activeTab === 3" class="modal-section">
          <h3><i class="pi pi-video"></i>Видео</h3>
          <div class="two-cols">
            <label>Платформа<input v-model="entityDraft.platform" class="field" placeholder="YouTube" /></label>
            <label>Длительность<input v-model="entityDraft.duration" class="field" /></label>
            <label>Количество вопросов<input v-model="entityDraft.questions" class="field" /></label>
            <label>Иконка<input v-model="entityDraft.icon" class="field" placeholder="pi pi-youtube" /></label>
          </div>
          <label>URL<input v-model="entityDraft.link" class="field" placeholder="https://..." /></label>
        </div>
        <div v-if="activeTab === 4" class="modal-section">
          <h3><i class="pi pi-file-edit"></i>Параметры задания</h3>
          <div class="two-cols">
            <label>Компания<input v-model="entityDraft.company" class="field" /></label>
            <label>Логотип<input v-model="entityDraft.logo" class="field" /></label>
            <label>Роль<input v-model="entityDraft.role" class="field" /></label>
            <label>Уровень
              <select v-model="entityDraft.level" class="field">
                <option value="junior">junior</option>
                <option value="middle">middle</option>
                <option value="senior">senior</option>
              </select>
            </label>
          </div>
          <label>Навыки<input v-model="entityDraft.skillsText" class="field" placeholder="React, TypeScript, API" /></label>
          <label>Ссылка на задание<input v-model="entityDraft.link" class="field" placeholder="https://github.com/..." /></label>
          <div v-if="entityDraft.skillsText" class="skill-preview">
            <span v-for="skill in entityDraft.skillsText.split(',').map((s) => s.trim()).filter(Boolean)" :key="skill" class="tag">{{ skill }}</span>
          </div>
        </div>
        <div v-if="activeTab === 5" class="modal-section two-cols">
          <label>Метрика<input v-model="entityDraft.metric" class="field" /></label>
          <label>Период<input v-model="entityDraft.period" class="field" /></label>
        </div>
        <div class="modal-actions">
          <button class="btn" @click="entityModalOpen = false">Отмена</button>
          <button class="btn primary" @click="saveEntityModal">Сохранить</button>
        </div>
      </section>
    </div>
    <div v-if="showUpload" class="modal-layer" @click.self="showUpload = false">
      <section class="modal neon-border">
        <button class="close" @click="showUpload = false"><i class="pi pi-times"></i></button>
        <h2>Запустить обработку видео</h2>
        <p>Вставьте ссылку на интервью или выберите локальный файл для существующего backend pipeline.</p>
        <div class="upload-tabs">
          <button :class="{ active: uploadMode === 'url' }" @click="uploadMode = 'url'"><i class="pi pi-link"></i>По ссылке</button>
          <button :class="{ active: uploadMode === 'file' }" @click="uploadMode = 'file'"><i class="pi pi-upload"></i>Файл</button>
        </div>
        <template v-if="uploadMode === 'url'">
          <input v-model="videoUrl" class="field" placeholder="https://youtube.com/watch?v=..." />
          <span v-if="detectedPlatform" class="detected"><i class="pi pi-check-circle"></i>{{ detectedPlatform }}</span>
        </template>
        <label v-else class="file-drop">
          <i class="pi pi-cloud-upload"></i>
          <span>{{ uploadFile?.name || 'Выберите видео или аудиофайл' }}</span>
          <input type="file" accept="video/*,audio/*,.mp4,.mkv,.avi,.mp3,.wav,.webm" @change="uploadFile = $event.target.files[0]" />
        </label>
        <button class="btn primary" :disabled="busy || (uploadMode === 'url' ? !videoUrl : !uploadFile)" @click="processVideo">{{ busy ? 'Отправляем...' : 'Отправить в обработку' }}</button>
      </section>
    </div>
    <div v-if="toast" class="toast">{{ toast }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import NavBar from '../components/NavBar.vue'
import api from '../api/client'

const tabs = ['Вопросы', 'Предложения', 'Обратная связь', 'Видео', 'Тестовые задания', 'Аналитика']
const activeTab = ref(0)
const busy = ref(false)
const showUpload = ref(false)
const showProcessingDetails = ref(false)
const showCompleteActions = ref(false)
const showCompleteBanner = ref(localStorage.getItem('admin_processing_banner_hidden') !== '1')
const questionModalOpen = ref(false)
const entityModalOpen = ref(false)
const videoUrl = ref('')
const uploadMode = ref('url')
const uploadFile = ref(null)
const toast = ref('')
const page = ref(1)
const pageSize = 30
const editQuestion = ref({})
const entityDraft = ref({})
const rows = ref([
  { id: 1, title: 'Почему вы выбрали именно нашу компанию?', topic: 'Общие вопросы', level: 'junior', conf: 100, status: true, answer: true },
  { id: 2, title: 'Чем вы занимаетесь на текущем месте работы?', topic: 'Общие вопросы', level: 'junior', conf: 100, status: true, answer: true },
  { id: 3, title: 'Как вы считаете, почему мы должны выбрать именно вас?', topic: 'General', level: 'junior', conf: 50, status: false, answer: false },
  { id: 4, title: 'Расскажите о ваших хобби.', topic: 'General', level: 'junior', conf: 50, status: false, answer: false },
  { id: 5, title: 'Сколько тоненьных магий поместится в автобусе?', topic: 'General', level: 'middle', conf: 50, status: false, answer: false },
  { id: 6, title: 'Вы допускаете, что на рассматриваемой вакансии придётся...', topic: 'General', level: 'junior', conf: 50, status: false, answer: false },
  { id: 7, title: 'Кем вы видите себя через пять лет?', topic: 'General', level: 'junior', conf: 50, status: false, answer: false },
  ...Array.from({ length: 28 }, (_, index) => ({
    id: index + 8,
    title: `Демо-вопрос для модерации #${index + 1}`,
    topic: index % 3 === 0 ? 'Backend' : index % 3 === 1 ? 'Frontend' : 'General',
    level: index % 5 === 0 ? 'senior' : index % 2 === 0 ? 'middle' : 'junior',
    conf: 52 + (index % 43),
    status: index % 4 === 0,
    answer: index % 3 === 0
  }))
])
const search = ref('')
const topic = ref('')
const status = ref('')
const selectedIds = ref([])
const selectedRow = ref(null)
const topics = computed(() => [...new Set(rows.value.map((r) => r.topic))])
const adminEntities = ref({
  1: [
    { id: 's1', status: 'Новая', statusType: 'middle', title: 'Добавить интервью по Python', text: 'Пользователь предложил YouTube-запись для обработки.', meta: '2 часа назад' },
    { id: 's2', status: 'Принято', statusType: 'ok', title: 'Подборка System Design', text: 'Список материалов для senior-подготовки.', meta: '12 вопросов' }
  ],
  2: [
    { id: 'f1', status: 'Открыто', statusType: 'middle', title: 'Нет фильтра по уровню', text: 'Пользователь просит сохранить выбранный уровень между страницами.', meta: 'UX' },
    { id: 'f2', status: 'Закрыто', statusType: 'ok', title: 'Опечатка в ответе', text: 'Исправить формулировку ответа в карточке React.', meta: 'Контент' }
  ],
  3: [
    { id: 'v1', status: 'Готово', statusType: 'ok', title: 'Backend Developer Interview', text: 'YouTube · 12 вопросов', meta: '54:32', icon: 'pi pi-video', duration: '54:32', questions: 12 },
    { id: 'v2', status: 'Очередь', statusType: 'middle', title: 'DevOps Engineer Interview', text: 'Rutube · 8 вопросов', meta: '45:07', icon: 'pi pi-video', duration: '45:07', questions: 8 },
    { id: 'v3', status: 'Ошибка', statusType: 'senior', title: 'Frontend Live Coding', text: 'YouTube · 0 вопросов', meta: '31:22', icon: 'pi pi-video', duration: '31:22', questions: 0 }
  ],
  4: [
    { id: 't1', status: 'Активно', statusType: 'ok', title: 'REST API на Spring Boot', text: 'Задание для Java middle с JWT и PostgreSQL.', meta: 'Middle', company: 'СБЕР', logo: '✓', role: 'Java разработчик', level: 'middle', skills: ['Java', 'Spring Boot', 'PostgreSQL', 'JWT'] },
    { id: 't2', status: 'Черновик', statusType: 'middle', title: 'Telegram бот на Python', text: 'Карточка задания ожидает проверки описания.', meta: 'Junior', company: 'Т-Банк', logo: 'T', role: 'Python разработчик', level: 'junior', skills: ['Python', 'aiogram', 'SQLite'] },
    { id: 't3', status: 'На проверке', statusType: 'middle', title: 'CI/CD пайплайн', text: 'Настроить деплой Node.js приложения с тестами и rollback.', meta: 'Middle', company: 'Wildberries', logo: 'WB', role: 'DevOps инженер', level: 'middle', skills: ['GitLab CI', 'Docker', 'Nginx'] }
  ],
  5: [
    { id: 'a1', status: '+18%', statusType: 'ok', title: 'Рост добавления вопросов', text: 'За неделю база пополнилась быстрее обычного.', meta: '7 дней' },
    { id: 'a2', status: 'Риск', statusType: 'senior', title: 'Много вопросов без ответа', text: 'Нужно запустить генерацию ответов для новых карточек.', meta: '23 карточки' }
  ]
})
const filteredRows = computed(() => rows.value.filter((row) => {
  if (search.value && !row.title.toLowerCase().includes(search.value.toLowerCase())) return false
  if (topic.value && row.topic !== topic.value) return false
  if (status.value === 'approved' && !row.status) return false
  if (status.value === 'pending' && row.status) return false
  return true
}))
const totalPages = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / pageSize)))
const paginatedRows = computed(() => filteredRows.value.slice((page.value - 1) * pageSize, page.value * pageSize))
const firstShown = computed(() => filteredRows.value.length ? (page.value - 1) * pageSize + 1 : 0)
const lastShown = computed(() => Math.min(page.value * pageSize, filteredRows.value.length))
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
const activeEntities = computed(() => adminEntities.value[activeTab.value] || [])
const createButtonLabel = computed(() => ({
  1: 'Добавить предложение',
  2: 'Добавить обращение',
  3: 'Добавить видео',
  4: 'Добавить задание',
  5: 'Добавить метрику'
})[activeTab.value] || 'Создать карточку')
const modalTitle = computed(() => ({
  1: 'Новое предложение',
  2: 'Новое обращение',
  3: 'Новое видео',
  4: 'Новое тестовое задание',
  5: 'Новая метрика'
})[activeTab.value] || 'Новая карточка')
const detectedPlatform = computed(() => {
  const url = videoUrl.value.toLowerCase()
  if (url.includes('youtube.com') || url.includes('youtu.be')) return 'YouTube'
  if (url.includes('rutube.ru')) return 'Rutube'
  if (url.includes('vk.com') || url.includes('vk.video')) return 'VK Video'
  if (url.includes('vimeo.com')) return 'Vimeo'
  return ''
})
const analyticsCards = [
  { label: 'Модерация', value: '23', title: 'карточки ждут решения' },
  { label: 'Ответы', value: '71%', title: 'вопросов имеют готовый ответ' },
  { label: 'Видео', value: '4', title: 'записи требуют повторной обработки' },
  { label: 'Задания', value: '12', title: 'активных тестовых заданий' }
]
const analyticsActions = [
  'Сгенерировать ответы для вопросов без ответа',
  'Проверить видео с ошибкой транскрибации',
  'Обновить HH-навыки для Backend и Frontend',
  'Опубликовать задания со статусом На проверке'
]
const showToast = (msg) => { toast.value = msg; setTimeout(() => { toast.value = '' }, 2200) }
const mapQuestion = (q) => ({ id: q.id, title: q.question, topic: q.topic || 'General', level: q.difficulty || 'junior', conf: Math.round(q.probability || 50), status: !!q.approved, answer: !!q.answer })

function goToPage(nextPage) {
  page.value = Math.min(Math.max(nextPage, 1), totalPages.value)
}

function dismissCompleteBanner() {
  showCompleteBanner.value = false
  localStorage.setItem('admin_processing_banner_hidden', '1')
}

function copyProcessingSummary() {
  navigator.clipboard?.writeText('Обработка видео завершена: 12 вопросов, источник YouTube, длительность 19:04')
  showToast('Сводка скопирована')
}

function openQuestionModal(row) {
  editQuestion.value = { ...row, answerText: row.answer ? 'Ответ уже создан. Отредактируйте текст перед публикацией.' : '' }
  questionModalOpen.value = true
}

function saveQuestionModal() {
  const index = rows.value.findIndex((row) => row.id === editQuestion.value.id)
  if (index >= 0) rows.value[index] = { ...rows.value[index], ...editQuestion.value, answer: !!editQuestion.value.answerText }
  questionModalOpen.value = false
  showToast('Вопрос сохранён')
}

function openEntityModal(item) {
  entityDraft.value = item
    ? { ...item, skillsText: item.skills?.join(', ') || '' }
    : { title: '', text: '', status: 'Черновик', statusType: 'middle', meta: 'Новая карточка', company: '', logo: 'IH', role: '', level: 'middle', platform: 'YouTube', icon: 'pi pi-video', duration: '', questions: '', skillsText: '' }
  entityModalOpen.value = true
}

function saveEntityModal() {
  const list = adminEntities.value[activeTab.value] || []
  const draft = {
    ...entityDraft.value,
    skills: entityDraft.value.skillsText ? entityDraft.value.skillsText.split(',').map((s) => s.trim()).filter(Boolean) : entityDraft.value.skills
  }
  if (entityDraft.value.id) {
    const index = list.findIndex((item) => item.id === entityDraft.value.id)
    if (index >= 0) list[index] = draft
  } else {
    list.unshift({ ...draft, id: `${activeTab.value}-${Date.now()}` })
    adminEntities.value[activeTab.value] = list
  }
  entityModalOpen.value = false
  showToast('Карточка сохранена')
}

function toggleRow(id) {
  selectedIds.value = selectedIds.value.includes(id) ? selectedIds.value.filter((item) => item !== id) : [...selectedIds.value, id]
}
async function loadAdminData() {
  try {
    const r = await api.getAdminQuestions()
    const list = r.data.questions || r.data || []
    if (list.length) rows.value = list.map(mapQuestion)
  } catch {}
}
async function toggleApprove(row) {
  try {
    if (row.status) await api.revokeQuestions([row.id])
    else await api.approveQuestions([row.id])
    row.status = !row.status
  } catch { row.status = !row.status }
}
async function deleteRow(row) {
  try { await api.deleteQuestion(row.id) } catch {}
  rows.value = rows.value.filter((item) => item.id !== row.id)
}
async function bulkGenerate() {
  busy.value = true
  try { await api.generateAnswersBulk(selectedIds.value, selectedIds.value.length || 10); showToast('Генерация запущена') }
  catch { showToast('Демо: генерация отмечена') }
  busy.value = false
}
async function processVideo() {
  busy.value = true
  try {
    if (uploadMode.value === 'url') await api.processVideoWithClient({ video_url: videoUrl.value })
    else {
      const fd = new FormData()
      fd.append('file', uploadFile.value)
      await api.uploadVideoFile(fd)
    }
    showToast('Видео отправлено в обработку')
    showUpload.value = false
    videoUrl.value = ''
    uploadFile.value = null
  }
  catch { showToast('Не удалось отправить видео') }
  busy.value = false
}
function openPlayer() { window.open('https://youtube.com', '_blank') }
watch([search, topic, status], () => { page.value = 1 })
watch(activeTab, () => { showCompleteActions.value = false })
onMounted(loadAdminData)
</script>

<style scoped>
.admin { padding-top: 26px; }
.admin-head { display: flex; justify-content: space-between; align-items: center; gap: 24px; margin-bottom: 22px; }
.admin-head h1 { margin: 0 0 6px; font-size: 42px; letter-spacing: -.03em; }
.admin-head p { margin: 0; color: var(--muted); font-size: 18px; }
.complete {
  position: relative;
  min-height: 198px;
  display: grid;
  grid-template-columns: 120px 1fr 160px 170px 250px 230px;
  gap: 28px;
  align-items: center;
  padding: 34px 40px;
}
.complete-close { position: absolute; right: 18px; top: 18px; width: 34px; height: 34px; border: 1px solid rgba(83, 121, 148, .2) !important; border-radius: 8px; color: var(--muted) !important; margin: 0 !important; }
.check { width: 88px; height: 88px; border: 4px solid var(--cyan); border-radius: 50%; display: grid; place-items: center; color: var(--cyan); font-size: 42px; box-shadow: 0 0 28px rgba(18, 230, 209, .25); }
.complete h1 { margin: 0 0 10px; font-size: 26px; }
.complete p, .summary span { color: var(--muted); margin: 0; }
.complete button:not(.btn) { margin-top: 24px; background: transparent; border: 0; color: var(--cyan); font-weight: 700; }
.summary b { display: block; margin-top: 10px; font-size: 17px; }
.summary em { color: red; font-style: normal; margin-right: 8px; }
.processing-details { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.processing-details span { padding: 7px 10px; border-radius: 8px; background: rgba(18, 230, 209, .09); color: var(--cyan); font-size: 13px; }
.complete-actions { display: grid; gap: 26px; position: relative; }
.action-menu { position: absolute; right: 0; top: 58px; width: 230px; z-index: 5; display: grid; gap: 4px; padding: 8px; border: 1px solid var(--line); border-radius: var(--radius); background: #06192c; box-shadow: var(--shadow); }
.action-menu button { height: 38px; margin: 0 !important; padding: 0 10px; text-align: left; border: 0 !important; border-radius: 6px; color: var(--text) !important; background: transparent; }
.action-menu button:hover { background: rgba(18, 230, 209, .09); color: var(--cyan) !important; }
.tabs { display: flex; gap: 44px; height: 82px; align-items: end; border-bottom: 1px solid rgba(83, 121, 148, .14); margin-bottom: 24px; }
.tabs a { height: 52px; color: var(--muted); font-weight: 700; }
.tabs .active { color: var(--cyan); border-bottom: 3px solid var(--cyan); }
.admin-tools { display: flex; justify-content: space-between; align-items: center; gap: 36px; margin-bottom: 22px; }
.compact-tools { justify-content: flex-start; }
.admin-tools .toolbar { flex: 1; grid-template-columns: 1.1fr .5fr .5fr auto; margin: 0; }
.admin-tools .field { height: 52px; }
.admin-table .table-row { grid-template-columns: 52px 1.7fr .55fr .52fr .65fr .42fr .42fr .78fr; min-height: 68px; padding: 0 24px; }
.confidence { display: flex; align-items: center; gap: 14px; }
.row-actions { display: flex; gap: 14px; justify-content: flex-end; }
.row-actions button { height: 42px; min-width: 92px; border-radius: 8px; background: rgba(3, 39, 56, .66); color: var(--cyan); border: 1px solid rgba(18, 230, 209, .35); font-weight: 700; }
.row-actions .danger { min-width: 42px; color: var(--red); border-color: rgba(255, 93, 108, .6); }
.admin-footer { display: flex; justify-content: space-between; color: var(--muted); padding-top: 14px; }
.admin-footer b { color: var(--text); border: 1px solid rgba(83, 121, 148, .16); padding: 12px 28px; border-radius: 10px; margin-left: 16px; }
.admin-pagination { display: flex; justify-content: center; align-items: center; gap: 10px; margin-top: 18px; }
.admin-pagination button { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 8px; border: 1px solid rgba(83, 121, 148, .16); background: rgba(4, 20, 37, .62); color: var(--text); font-weight: 800; transition: .18s ease; }
.admin-pagination button:not(:disabled):hover { color: var(--cyan); border-color: var(--line-strong); }
.admin-pagination button:disabled { opacity: .45; cursor: not-allowed; }
.admin-pagination .active { background: var(--cyan); color: #002c31; border-color: transparent; }
.admin-pagination .ellipsis { background: transparent; border-color: transparent; color: var(--soft); }
.tab-placeholder { min-height: 360px; padding: 36px; display: grid; align-content: center; justify-items: start; gap: 14px; }
.tab-placeholder h2 { font-size: 34px; margin: 0; }
.tab-placeholder p { color: var(--muted); max-width: 720px; line-height: 1.55; }
.admin-card-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.admin-card { min-height: 250px; padding: 24px; display: flex; flex-direction: column; cursor: pointer; transition: .18s ease; }
.admin-card:hover { transform: translateY(-3px); border-color: var(--line-strong); }
.admin-card h2 { margin: 20px 0 10px; font-size: 24px; }
.admin-card p { margin: 0; color: var(--muted); line-height: 1.55; }
.admin-card footer { display: flex; justify-content: space-between; align-items: center; gap: 14px; margin-top: auto; padding-top: 20px; color: var(--muted); }
.admin-card footer button { height: 38px; padding: 0 12px; border-radius: 8px; border: 1px solid rgba(18, 230, 209, .35); background: rgba(3, 39, 56, .66); color: var(--cyan); font-weight: 700; }
.admin-list { display: grid; gap: 10px; }
.admin-list-row { min-height: 78px; display: grid; grid-template-columns: 120px 1fr 120px 150px; align-items: center; gap: 16px; padding: 14px 18px; cursor: pointer; transition: .18s ease; }
.admin-list-row.video { grid-template-columns: 120px 54px 1fr 120px 150px; }
.admin-list-row:hover { border-color: var(--line-strong); transform: translateX(4px); }
.admin-list-row h2 { margin: 0 0 4px; font-size: 20px; }
.admin-list-row p { margin: 0; color: var(--muted); }
.admin-list-row > b { color: var(--muted); }
.admin-list-row button { height: 40px; border-radius: 8px; border: 1px solid rgba(18, 230, 209, .35); background: rgba(3, 39, 56, .66); color: var(--cyan); font-weight: 700; }
.platform { width: 46px; height: 46px; display: grid; place-items: center; border-radius: 8px; border: 1px solid rgba(18, 230, 209, .2); color: var(--cyan); font-size: 22px; }
.assignment-admin-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.assignment-admin-card { min-height: 310px; padding: 22px 24px 0; display: flex; flex-direction: column; border-left: 3px solid var(--yellow); cursor: pointer; transition: .18s ease; }
.assignment-admin-card:hover { transform: translateY(-3px); border-color: var(--line-strong); }
.assignment-admin-card header, .assignment-admin-card footer { display: flex; justify-content: space-between; align-items: center; gap: 14px; }
.assignment-admin-card h2 { margin: 26px 0 10px; font-size: 24px; letter-spacing: -.03em; }
.assignment-admin-card p { margin: 0 0 18px; color: var(--muted); line-height: 1.45; }
.assignment-admin-card small { color: #cdd6e3; font-size: 16px; margin-bottom: 16px; }
.assignment-admin-card .tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }
.assignment-admin-card footer { margin: auto -24px 0; min-height: 54px; padding: 0 24px; border-top: 1px solid rgba(83, 121, 148, .14); color: var(--muted); }
.assignment-admin-card footer button { height: 38px; padding: 0 12px; border-radius: 8px; border: 1px solid rgba(18, 230, 209, .35); background: rgba(3, 39, 56, .66); color: var(--cyan); font-weight: 700; }
.company { display: flex; align-items: center; gap: 10px; font-weight: 800; }
.company b { width: 42px; height: 42px; border-radius: 50%; display: grid; place-items: center; background: #1687ff; color: white; }
.analytics-board { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.analytics-card { padding: 22px; }
.analytics-card span { color: var(--cyan); font-weight: 800; text-transform: uppercase; font-size: 13px; }
.analytics-card strong { display: block; margin: 12px 0 4px; font-size: 42px; }
.analytics-card p { margin: 0; color: var(--muted); }
.analytics-actions { grid-column: 1 / -1; padding: 24px; display: grid; gap: 10px; }
.analytics-actions h2 { margin: 0 0 8px; font-size: 26px; }
.analytics-actions button { min-height: 48px; text-align: left; border: 1px solid rgba(83, 121, 148, .16); border-radius: 8px; background: rgba(3, 20, 37, .38); color: var(--text); padding: 0 16px; }
.analytics-actions i { color: var(--cyan); margin-right: 10px; }
.modal-layer { position: fixed; inset: 92px 0 0; display: grid; place-items: center; background: rgba(2, 13, 27, .38); z-index: 30; }
.modal { width: min(760px, calc(100vw - 32px)); display: grid; gap: 16px; border-radius: 16px; background: #06192c; padding: 32px; position: relative; max-height: calc(100vh - 130px); overflow: auto; }
.edit-modal label { display: grid; gap: 8px; color: var(--muted); font-weight: 700; }
.edit-modal textarea.field { min-height: 130px; padding-top: 16px; resize: vertical; }
.modal-section { display: grid; gap: 14px; padding: 16px; border: 1px solid rgba(83, 121, 148, .14); border-radius: 12px; background: rgba(4, 20, 37, .42); }
.modal-section h3 { margin: 0; display: flex; align-items: center; gap: 8px; color: var(--text); font-size: 16px; }
.two-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.skill-preview { display: flex; flex-wrap: wrap; gap: 8px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 12px; }
.modal .close { position: absolute; right: 22px; top: 22px; background: none; border: 0; color: var(--muted); font-size: 22px; }
.modal p { color: var(--muted); }
.upload-tabs { display: flex; gap: 10px; }
.upload-tabs button { height: 42px; padding: 0 18px; border-radius: 8px; border: 1px solid rgba(83, 137, 174, .2); background: rgba(4, 20, 37, .62); color: var(--text); font-weight: 800; }
.upload-tabs .active { background: var(--cyan); color: #032b31; border-color: transparent; }
.detected { width: fit-content; display: inline-flex; align-items: center; gap: 8px; color: var(--cyan); border: 1px solid rgba(18, 230, 209, .3); background: rgba(18, 230, 209, .08); border-radius: 8px; padding: 8px 12px; font-weight: 800; }
.file-drop { min-height: 150px; display: grid !important; place-items: center; gap: 10px; border: 2px dashed rgba(83, 137, 174, .28); border-radius: 14px; background: rgba(4, 20, 37, .44); color: var(--muted); cursor: pointer; }
.file-drop i { font-size: 34px; color: var(--cyan); }
.file-drop input { display: none; }

@media (max-width: 1300px) {
  .complete { grid-template-columns: 90px 1fr 1fr; }
  .admin-table { overflow: hidden; }
  .admin-table .table-row { grid-template-columns: 44px minmax(300px, 1.6fr) .55fr .5fr .62fr .4fr .38fr .72fr; }
  .admin-card-grid { grid-template-columns: 1fr 1fr; }
  .assignment-admin-grid, .analytics-board { grid-template-columns: 1fr 1fr; }
  .admin-list-row { grid-template-columns: 110px 1fr 110px; }
  .admin-list-row .platform { display: none; }
}
@media (max-width: 760px) {
  .admin-card-grid { grid-template-columns: 1fr; }
  .assignment-admin-grid, .analytics-board { grid-template-columns: 1fr; }
  .admin-head { flex-direction: column; align-items: flex-start; }
  .admin-list-row { grid-template-columns: 1fr; }
  .two-cols { grid-template-columns: 1fr; }
  .admin-footer { flex-direction: column; gap: 12px; }
}
</style>
