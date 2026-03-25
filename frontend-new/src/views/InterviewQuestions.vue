<template>
  <div class="page">
    <NavBar />
    <div class="container" style="padding-top:2rem; padding-bottom:3rem;">

      <!-- Header -->
      <div class="page-top">
        <div>
          <h1 class="page-heading h-page">{{ pageHeading }}</h1>
          <p class="page-desc p-muted">Реальные вопросы с IT-собеседований</p>
        </div>
        <button v-if="professionSlug" class="btn btn-ghost btn-sm" @click="clearProfession">✕ Сбросить профессию</button>
      </div>

      <!-- Filters -->
      <div class="filters">
        <div class="search-wrap">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          <input v-model="search" placeholder="Поиск вопроса..." class="input search-input" />
        </div>
        <select v-model="selectedTopic" class="input filter-select">
          <option value="">Все технологии</option>
          <option v-for="t in topics" :key="t" :value="t">{{ t }}</option>
        </select>
        <select v-model="selectedDifficulty" class="input filter-select">
          <option value="">Любая сложность</option>
          <option value="junior">Junior</option>
          <option value="middle">Middle</option>
          <option value="senior">Senior</option>
        </select>
        <select v-model="sortBy" class="input filter-select filter-sort">
          <option value="probability">По вероятности</option>
          <option value="date">По дате</option>
          <option value="alpha">По алфавиту</option>
        </select>
      </div>

      <!-- Count -->
      <div class="list-meta">
        <span class="count">{{ filteredQuestions.length }} вопросов</span>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="q-list">
        <div v-for="i in 8" :key="i" class="q-row card">
          <div class="q-body" style="width:100%">
            <div class="skeleton-line lg" style="margin-bottom:.55rem"></div>
            <div class="skeleton-line" style="width:65%"></div>
          </div>
        </div>
      </div>

      <div v-else-if="loadError" class="state-panel">
        <h3>Ошибка загрузки</h3>
        <p>{{ loadError }}</p>
        <button class="btn btn-secondary btn-sm" style="margin-top:.7rem" @click="loadQuestions">Повторить</button>
      </div>

      <!-- Empty -->
      <div v-else-if="filteredQuestions.length === 0" class="empty-state">
        <p>Вопросы не найдены</p>
        <span>Попробуйте изменить фильтры</span>
      </div>

      <!-- List -->
      <div v-else class="q-list stagger">
        <router-link
          v-for="q in paginatedQuestions" :key="q.id"
          :to="`/question/${q.id}`"
          class="q-row card interactive-card"
        >
          <div class="q-body">
            <p class="q-text">{{ q.question }}</p>
            <div class="q-tags">
              <span class="badge badge-info">{{ q.topic }}</span>
              <span class="badge" :class="diffBadge(q.difficulty)">{{ q.difficulty }}</span>
              <span class="q-prob">{{ (q.probability||0).toFixed(0) }}%</span>
            </div>
          </div>
          <svg class="q-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
        </router-link>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination">
        <button class="btn btn-secondary btn-sm" :disabled="page <= 1" @click="page--">←</button>
        <span class="pag-info">{{ page }} / {{ totalPages }}</span>
        <button class="btn btn-secondary btn-sm" :disabled="page >= totalPages" @click="page++">→</button>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import api from '../api/client'

const route = useRoute()
const loading = ref(true)
const questions = ref([])
const topics = ref([])
const selectedTopic = ref('')
const selectedDifficulty = ref('')
const search = ref('')
const sortBy = ref('probability')
const page = ref(1)
const pageSize = ref(20)
const professionSlug = ref(null)
const professionTitle = ref('')
const loadError = ref('')

const pageHeading = computed(() => professionTitle.value ? `Вопросы: ${professionTitle.value}` : 'Вопросы с собеседований')

const clearProfession = () => { professionSlug.value = null; professionTitle.value = ''; loadQuestions() }

const diffBadge = (d) => ({ junior: 'badge-ok', middle: 'badge-warn', senior: 'badge-err' }[d] || 'badge-muted')

const filteredQuestions = computed(() => {
  let r = questions.value.filter(q => {
    if (selectedTopic.value && q.topic !== selectedTopic.value) return false
    if (selectedDifficulty.value && q.difficulty !== selectedDifficulty.value) return false
    if (search.value && !q.question.toLowerCase().includes(search.value.toLowerCase())) return false
    return true
  })
  if (sortBy.value === 'probability') r.sort((a, b) => (b.probability||0) - (a.probability||0))
  else if (sortBy.value === 'date') r.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  else if (sortBy.value === 'alpha') r.sort((a, b) => a.question.localeCompare(b.question, 'ru'))
  return r
})

const totalPages = computed(() => Math.ceil(filteredQuestions.value.length / pageSize.value))
const paginatedQuestions = computed(() => filteredQuestions.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value))

watch([selectedTopic, selectedDifficulty, search, sortBy], () => { page.value = 1 })
watch(() => route.query.topic, (t) => { if (t) selectedTopic.value = t })
watch(() => route.query.profession, (p) => { if (p) { professionSlug.value = p; professionTitle.value = route.query.profTitle || p; loadQuestions() } })

const loadQuestions = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const r = professionSlug.value
      ? await api.getProfessionQuestions(professionSlug.value, { limit: 1000 })
      : await api.getQuestions({ status: 'approved', limit: 1000 })
    questions.value = r.data.questions || r.data || []
    topics.value = [...new Set(questions.value.map(q => q.topic).filter(Boolean))].sort()
  } catch (e) { console.error(e); loadError.value = 'Не удалось получить вопросы. Проверь соединение с сервером.' }
  loading.value = false
}

onMounted(async () => {
  if (route.query.topic) selectedTopic.value = route.query.topic
  if (route.query.profession) { professionSlug.value = route.query.profession; professionTitle.value = route.query.profTitle || route.query.profession }
  await loadQuestions()
})
</script>

<style scoped>
.page-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; gap: 1rem; }
.page-heading { font-size: 1.85rem; font-weight: 700; }
.page-desc { color: var(--c-text-3); font-size: 1rem; margin-top: .3rem; }

.page-top { position: relative; }
.page-top::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -10px;
  height: 1px;
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--c-brand) 60%, transparent), transparent);
}

.filters {
  display: flex;
  gap: .6rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  position: sticky;
  top: calc(var(--nav-h) + .45rem);
  z-index: 20;
  background: color-mix(in srgb, var(--c-surface) 64%, transparent);
  backdrop-filter: blur(12px);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  padding: .75rem;
}
.search-wrap {
  position: relative;
  flex: 1;
  min-width: 200px;
}
.search-icon {
  position: absolute;
  left: .7rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--c-text-4);
  pointer-events: none;
}
.search-input { padding-left: 2.2rem; }
.filter-select { max-width: 180px; }
.filter-sort { max-width: 160px; }

.list-meta { display: flex; justify-content: space-between; align-items: center; margin-bottom: .75rem; }
.count { font-size: .88rem; color: var(--c-text-3); }

.center-block { display: flex; justify-content: center; padding: 3rem; }
.empty-state { text-align: center; padding: 4rem; color: var(--c-text-3); }
.empty-state p { font-size: 1.05rem; margin-bottom: .25rem; }
.empty-state span { font-size: .85rem; color: var(--c-text-4); }

/* Question list */
.q-list { display: flex; flex-direction: column; gap: .4rem; }
.q-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.1rem 1.3rem;
  text-decoration: none;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.q-row::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 2px;
  background: linear-gradient(180deg, var(--c-brand), var(--c-accent));
  opacity: 0;
  transition: opacity var(--dur);
}
.q-row:hover { background: var(--c-surface-h); border-color: var(--c-border-h); }
.q-row:hover::before { opacity: 1; }
.q-body { flex: 1; min-width: 0; }
.q-text { font-size: 1.05rem; color: var(--c-text); line-height: 1.5; margin-bottom: .4rem; }
.q-tags { display: flex; align-items: center; gap: .35rem; flex-wrap: wrap; }
.q-prob { font-size: .78rem; color: var(--c-text-3); margin-left: .25rem; }
.q-arrow { color: var(--c-text-4); flex-shrink: 0; opacity: 0; transition: opacity var(--dur); }
.q-row:hover .q-arrow { opacity: 1; }

.pagination { display: flex; justify-content: center; align-items: center; gap: 1rem; margin-top: 1.5rem; }
.pag-info { font-size: .85rem; color: var(--c-text-3); font-weight: 500; }

@media (max-width: 640px) {
  .filters { flex-direction: column; }
  .filter-select, .filter-sort { max-width: none; }
  .page-top { flex-direction: column; }
}
</style>
