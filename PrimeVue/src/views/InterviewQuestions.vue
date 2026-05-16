<template>
  <div class="page">
    <NavBar />
    <main class="screen narrow catalog">
      <section class="page-title fade-up">
        <div class="title-left">
          <div class="icon-box"><i class="pi pi-comments"></i></div>
          <div>
            <h1>Каталог вопросов</h1>
            <p>Фильтруйте по технологиям, уровню и сложности, чтобы найти подходящие вопросы для подготовки.</p>
          </div>
        </div>
      </section>

      <div class="toolbar">
        <input v-model="search" class="field search" placeholder="Поиск вопросов..." />
        <select v-model="selectedTopic" class="field"><option value="">Все технологии</option><option v-for="topic in topics" :key="topic">{{ topic }}</option></select>
        <select v-model="selectedDifficulty" class="field"><option value="">Любая сложность</option><option value="junior">Junior</option><option value="middle">Middle</option><option value="senior">Senior</option></select>
        <select v-model="sortBy" class="field"><option value="probability">По встречаемости</option><option value="date">Сначала новые</option><option value="alpha">По алфавиту</option></select>
        <button class="btn small" @click="resetFilters"><i class="pi pi-refresh"></i>Сбросить</button>
      </div>

      <div class="meta-row">
        <span>{{ totalLabel }} вопросов найдено</span>
        <span>Обновлено сегодня <i class="dot"></i></span>
      </div>

      <section v-if="loading" class="empty-panel glass"><div class="loader"></div></section>
      <section v-else-if="loadError && !filteredQuestions.length" class="empty-panel glass"><div><h3>Не удалось загрузить вопросы</h3><p>{{ loadError }}</p><button class="btn small" @click="loadQuestions">Повторить</button></div></section>
      <section v-else class="question-list stagger">
        <router-link v-for="q in paginatedQuestions" :key="q.id" :to="`/question/${q.id}`" class="question-row glass">
          <span class="q-icon"><i :class="`pi ${iconFor(q)}`"></i></span>
          <span class="q-main">
            <strong>{{ q.question || q.title }}</strong>
            <span><b class="tag">{{ q.topic || 'General' }}</b><b :class="`tag ${difficultyOf(q)}`">{{ difficultyOf(q) }}</b></span>
          </span>
          <span class="q-score">
            <em>{{ frequencyLabel(probabilityOf(q)) }}</em>
            <strong>{{ probabilityOf(q) }}%</strong>
          </span>
          <i class="pi pi-angle-right chevron"></i>
        </router-link>
      </section>

      <nav v-if="totalPages > 1" class="pagination" aria-label="Пагинация вопросов">
        <button class="page-nav" :disabled="page <= 1" @click="goToPage(page - 1)" aria-label="Предыдущая страница">
          <i class="pi pi-angle-left"></i>
        </button>
        <button
          v-for="item in visiblePages"
          :key="item.key"
          class="page-number"
          :class="{ active: item.value === page, ellipsis: item.type === 'ellipsis' }"
          :disabled="item.type === 'ellipsis'"
          @click="item.type === 'page' && goToPage(item.value)"
        >
          {{ item.label }}
        </button>
        <button class="page-nav" :disabled="page >= totalPages" @click="goToPage(page + 1)" aria-label="Следующая страница">
          <i class="pi pi-angle-right"></i>
        </button>
      </nav>

      <section class="catalog-more">
        <article class="glass">
          <h2>Как пользоваться каталогом</h2>
          <p>Откройте вопрос, сохраните его в закладки, добавьте личную заметку и сравните свой ответ с ответами сообщества.</p>
        </article>
        <article class="glass">
          <h2>Следующий шаг</h2>
          <p>После отбора вопросов переходите в тренажёр: карточки SM-2 помогут повторять сложные темы в нужный момент.</p>
          <router-link to="/trainer" class="btn small">Открыть тренажёр</router-link>
        </article>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from '../components/NavBar.vue'
import api from '../api/client'
import { questions as fallbackQuestions } from '../data/mock'

const route = useRoute()
const loading = ref(true)
const loadError = ref('')
const questions = ref([])
const topics = ref([])
const search = ref('')
const selectedTopic = ref('')
const selectedDifficulty = ref('')
const sortBy = ref('probability')
const page = ref(1)
const pageSize = 30

const extraFallbackQuestions = [
  ['Что происходит при ререндере компонента React?', 'Frontend', 'junior', 91, 'pi-code'],
  ['Как вы проектируете структуру REST API?', 'Backend', 'middle', 89, 'pi-server'],
  ['Чем SQL JOIN отличается от подзапроса?', 'Базы данных', 'junior', 87, 'pi-database'],
  ['Как работает индекс в PostgreSQL?', 'Базы данных', 'middle', 85, 'pi-database'],
  ['Что такое идемпотентность HTTP-методов?', 'Backend', 'middle', 83, 'pi-server'],
  ['Как вы проверяете гипотезу о причине бага?', 'QA', 'junior', 81, 'pi-check-circle'],
  ['Расскажите про опыт с Docker.', 'DevOps', 'junior', 79, 'pi-box'],
  ['Как устроен CI/CD pipeline?', 'DevOps', 'middle', 78, 'pi-sync'],
  ['Что такое race condition?', 'Backend', 'middle', 76, 'pi-cog'],
  ['Как вы декомпозируете большую задачу?', 'Поведенческие', 'middle', 75, 'pi-users'],
  ['Как вы работаете с конфликтами в команде?', 'Поведенческие', 'middle', 73, 'pi-users'],
  ['Что вы делаете, если требования неполные?', 'Product', 'middle', 72, 'pi-briefcase'],
  ['Как оценить сложность алгоритма?', 'Алгоритмы', 'junior', 71, 'pi-chart-line'],
  ['Чем стек отличается от очереди?', 'Алгоритмы', 'junior', 70, 'pi-list'],
  ['Как защитить API от частых запросов?', 'Security', 'middle', 69, 'pi-shield'],
  ['Что такое JWT и где его хранить?', 'Security', 'junior', 68, 'pi-shield'],
  ['Как вы строите логирование сервиса?', 'SRE', 'middle', 67, 'pi-chart-bar'],
  ['Какие метрики важны для production-сервиса?', 'SRE', 'middle', 66, 'pi-chart-bar'],
  ['Как вы проводите code review?', 'Team Lead', 'middle', 65, 'pi-comments'],
  ['Как объяснить технический долг бизнесу?', 'Team Lead', 'senior', 64, 'pi-comments'],
  ['Что такое eventual consistency?', 'System Design', 'senior', 63, 'pi-cog'],
  ['Как выбрать между монолитом и микросервисами?', 'System Design', 'senior', 62, 'pi-sitemap'],
  ['Как масштабировать очередь фоновых задач?', 'System Design', 'senior', 61, 'pi-sitemap'],
  ['Чем Kafka отличается от RabbitMQ?', 'Backend', 'middle', 60, 'pi-database'],
  ['Как работает debounce в интерфейсе?', 'Frontend', 'junior', 59, 'pi-code'],
  ['Что такое accessibility в веб-приложении?', 'Frontend', 'middle', 58, 'pi-desktop'],
  ['Как валидировать форму на клиенте и сервере?', 'Fullstack', 'junior', 57, 'pi-window-maximize'],
  ['Как вы организуете обработку ошибок?', 'Fullstack', 'middle', 56, 'pi-exclamation-triangle'],
  ['Как проверить качество ML-модели?', 'ML Engineer', 'middle', 55, 'pi-chart-line'],
  ['Как аналитик проверяет корректность данных?', 'Data Analyst', 'junior', 54, 'pi-table']
]

const normalizedFallback = [
  ...fallbackQuestions.map((q) => ({ id: q.id, question: q.title, topic: q.topic, difficulty: q.level, probability: q.probability, icon: q.icon })),
  ...extraFallbackQuestions.map((item, index) => ({
    id: `demo-${index + 1}`,
    question: item[0],
    topic: item[1],
    difficulty: item[2],
    probability: item[3],
    icon: item[4]
  }))
]

const difficultyOf = (q) => (q.difficulty || q.level || 'junior').toLowerCase()
const probabilityOf = (q) => Math.round(q.probability || q.frequency_percent || q.score || 50)
const iconFor = (q) => q.icon || (String(q.topic || '').toLowerCase().includes('техничес') ? 'pi-code' : 'pi-comments')
const frequencyLabel = (p) => p >= 95 ? 'Задают почти всегда' : p >= 85 ? 'Очень часто' : p >= 70 ? 'Часто встречается' : p >= 55 ? 'Средняя частота' : 'Иногда встречается'

const totalLabel = computed(() => (questions.value.length <= normalizedFallback.length && !search.value && !selectedTopic.value && !selectedDifficulty.value) ? '12 458' : filteredQuestions.value.length.toLocaleString('ru-RU'))
const filteredQuestions = computed(() => {
  const query = search.value.trim().toLowerCase()
  const result = questions.value.filter((q) => {
    const text = (q.question || q.title || '').toLowerCase()
    if (query && !text.includes(query)) return false
    if (selectedTopic.value && q.topic !== selectedTopic.value) return false
    if (selectedDifficulty.value && difficultyOf(q) !== selectedDifficulty.value) return false
    return true
  })
  return [...result].sort((a, b) => {
    if (sortBy.value === 'alpha') return (a.question || '').localeCompare(b.question || '', 'ru')
    if (sortBy.value === 'date') return new Date(b.created_at || 0) - new Date(a.created_at || 0)
    return probabilityOf(b) - probabilityOf(a)
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredQuestions.value.length / pageSize)))
const paginatedQuestions = computed(() => filteredQuestions.value.slice((page.value - 1) * pageSize, page.value * pageSize))
const visiblePages = computed(() => {
  const total = totalPages.value
  const current = page.value
  const pages = new Set([1, total, current, current - 1, current + 1])
  const normalized = [...pages].filter((p) => p >= 1 && p <= total).sort((a, b) => a - b)
  const result = []
  normalized.forEach((p, index) => {
    const prev = normalized[index - 1]
    if (index > 0 && p - prev > 1) {
      result.push({ type: 'ellipsis', key: `ellipsis-${prev}-${p}`, label: '...' })
    }
    result.push({ type: 'page', key: `page-${p}`, value: p, label: p })
  })
  return result
})

watch([search, selectedTopic, selectedDifficulty, sortBy], () => { page.value = 1 })
watch(totalPages, (total) => { if (page.value > total) page.value = total })
watch(() => route.query.topic, (topic) => { if (topic) selectedTopic.value = String(topic) })

function resetFilters() {
  search.value = ''
  selectedTopic.value = ''
  selectedDifficulty.value = ''
  sortBy.value = 'probability'
}

function goToPage(nextPage) {
  page.value = Math.min(Math.max(nextPage, 1), totalPages.value)
}

async function loadQuestions() {
  loading.value = true
  loadError.value = ''
  try {
    const r = route.query.profession
      ? await api.getProfessionQuestions(route.query.profession, { limit: 1000 })
      : await api.getQuestions({ status: 'approved', limit: 1000 })
    questions.value = r.data.questions || r.data || normalizedFallback
  } catch (e) {
    loadError.value = 'Показываю демо-данные, backend сейчас недоступен.'
    questions.value = normalizedFallback
  }
  topics.value = [...new Set(questions.value.map((q) => q.topic).filter(Boolean))].sort()
  if (route.query.topic) selectedTopic.value = String(route.query.topic)
  loading.value = false
}

onMounted(loadQuestions)
</script>

<style scoped>
.catalog { padding-top: 48px; padding-bottom: 80px; }
.title-left { display: flex; gap: 20px; align-items: center; }
.toolbar { grid-template-columns: 2fr .96fr .9fr .78fr 160px; margin-bottom: 24px; }
.meta-row { display: flex; }
.meta-row > span:last-child { text-align: right; }
.question-list { display: grid; gap: 8px; }
.question-row { min-height: 104px; display: grid; grid-template-columns: 76px 1fr 210px 34px; align-items: center; padding: 0 32px 0 24px; background: linear-gradient(90deg, rgba(10, 42, 67, .78), rgba(8, 31, 54, .84)); transition: transform .18s ease, border-color .18s ease; }
.question-row:hover { transform: translateX(6px); border-color: var(--line-strong); }
.q-icon { width: 62px; height: 62px; display: grid; place-items: center; border: 1px solid rgba(18, 230, 209, .18); border-radius: var(--radius); color: var(--cyan); font-size: 28px; background: rgba(0, 229, 209, .035); }
.q-main strong { display: block; font-size: 20px; margin-bottom: 12px; }
.q-main span { display: flex; gap: 10px; }
.q-score em { display: block; color: var(--cyan); font-style: normal; font-size: 16px; margin-bottom: 4px; }
.q-score strong { font-size: 30px; }
.chevron { color: var(--muted); font-size: 28px; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 10px; margin: 28px 0 0; color: var(--muted); flex-wrap: wrap; }
.pagination button { width: 42px; height: 42px; display: grid; place-items: center; border: 1px solid rgba(83, 137, 174, .2); background: rgba(4, 20, 37, .62); color: var(--text); border-radius: 8px; font-weight: 800; transition: .18s ease; }
.pagination button:not(:disabled):hover { border-color: var(--line-strong); color: var(--cyan); transform: translateY(-1px); }
.pagination button:disabled { opacity: .45; cursor: not-allowed; }
.pagination .page-number.active { background: var(--cyan); color: #002c31; border-color: transparent; box-shadow: 0 12px 32px rgba(18, 230, 209, .18); }
.pagination .page-number.ellipsis { background: transparent; border-color: transparent; color: var(--soft); }
.catalog-more { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 34px; }
.catalog-more article { padding: 28px; }
.catalog-more h2 { margin: 0 0 10px; font-size: 25px; }
.catalog-more p { color: var(--muted); line-height: 1.55; }
@media (max-width: 900px) { .meta-row, .catalog-more { grid-template-columns: 1fr; gap: 12px; } .meta-row > span:last-child { text-align: left; } .question-row { grid-template-columns: 62px 1fr; gap: 14px; padding: 18px; } .q-score, .chevron { display: none; } }
</style>
