<template>
  <div class="iq-page">
    <NavBar />
    <div class="page-container">
      <h1 class="page-title"><i class="pi pi-list"></i> Вопросы с собеседований</h1>
      <p class="page-subtitle">Реальные вопросы, задаваемые на IT-собеседованиях</p>

      <div class="filters">
        <Dropdown v-model="selectedTopic" :options="topics" placeholder="Все технологии" showClear />
        <Dropdown v-model="selectedDifficulty" :options="difficulties" optionLabel="label" optionValue="value" placeholder="Любая сложность" showClear />
        <InputText v-model="search" placeholder="Поиск вопроса..." class="search-input" />
      </div>

      <div class="sort-row">
        <span class="result-count">Найдено: {{ filteredQuestions.length }}</span>
        <Dropdown v-model="sortBy" :options="sortOptions" optionLabel="label" optionValue="value" placeholder="Сортировка" />
      </div>

      <div v-if="loading" class="loading"><ProgressSpinner /></div>

      <div v-else-if="filteredQuestions.length === 0" class="empty">
        <i class="pi pi-search"></i>
        <p>Вопросы не найдены</p>
      </div>

      <div v-else class="questions-list">
        <div v-for="q in paginatedQuestions" :key="q.id" class="question-row" @click="$router.push(`/question/${q.id}`)">
          <div class="q-main">
            <h3>{{ q.question }}</h3>
            <div class="q-meta">
              <Tag :value="q.topic" severity="info" size="small" />
              <Tag :value="q.difficulty" :severity="diffSev(q.difficulty)" size="small" />
              <span class="q-prob">
                <i class="pi pi-chart-line"></i> {{ (q.probability || 0).toFixed(0) }}%
              </span>
            </div>
          </div>
          <i class="pi pi-chevron-right q-arrow"></i>
        </div>
      </div>

      <Paginator v-if="filteredQuestions.length > pageSize" 
                 :rows="pageSize" :totalRecords="filteredQuestions.length"
                 v-model:first="first" :rowsPerPageOptions="[20, 50, 100]"
                 @update:rows="val => pageSize = val" />
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
const selectedTopic = ref(null)
const selectedDifficulty = ref(null)
const search = ref('')
const sortBy = ref('probability')
const first = ref(0)
const pageSize = ref(20)

const difficulties = [
  { label: 'Junior', value: 'junior' },
  { label: 'Middle', value: 'middle' },
  { label: 'Senior', value: 'senior' }
]
const sortOptions = [
  { label: 'По вероятности', value: 'probability' },
  { label: 'По дате', value: 'date' },
  { label: 'По алфавиту', value: 'alpha' }
]

const diffSev = (d) => ({ junior: 'success', middle: 'warning', senior: 'danger' }[d] || 'info')

const filteredQuestions = computed(() => {
  let result = questions.value.filter(q => {
    const matchTopic = !selectedTopic.value || q.topic === selectedTopic.value
    const matchDiff = !selectedDifficulty.value || q.difficulty === selectedDifficulty.value
    const matchSearch = !search.value || q.question.toLowerCase().includes(search.value.toLowerCase())
    return matchTopic && matchDiff && matchSearch
  })

  if (sortBy.value === 'probability') result.sort((a, b) => (b.probability || 0) - (a.probability || 0))
  else if (sortBy.value === 'date') result.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  else if (sortBy.value === 'alpha') result.sort((a, b) => a.question.localeCompare(b.question, 'ru'))

  return result
})

const paginatedQuestions = computed(() => {
  return filteredQuestions.value.slice(first.value, first.value + pageSize.value)
})

// Watch for query param changes (e.g. navigating from TechSelector)
watch(() => route.query.topic, (newTopic) => {
  selectedTopic.value = newTopic || null
  first.value = 0
})

onMounted(async () => {
  // Apply topic filter from query param if present
  if (route.query.topic) {
    selectedTopic.value = route.query.topic
  }
  try {
    const r = await api.getQuestions({ status: 'approved', limit: 1000 })
    questions.value = r.data.questions || r.data || []
    topics.value = [...new Set(questions.value.map(q => q.topic).filter(Boolean))]
  } catch (e) { console.error(e) }
  loading.value = false
})
</script>

<style scoped>
.iq-page { min-height: 100vh; background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%); }
.page-container { max-width: 1000px; margin: 0 auto; padding: 2rem; }
.page-title { color: white; font-size: 2rem; text-align: center; margin-bottom: 0.5rem; }
.page-title i { color: #667eea; }
.page-subtitle { text-align: center; color: rgba(255,255,255,0.5); margin-bottom: 2rem; }
.filters { display: flex; gap: 1rem; margin-bottom: 1rem; justify-content: center; flex-wrap: wrap; }
.search-input { min-width: 250px; }
.sort-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.result-count { color: rgba(255,255,255,0.5); font-size: 0.9rem; }
.loading { display: flex; justify-content: center; padding: 3rem; }
.empty { text-align: center; padding: 4rem; color: rgba(255,255,255,0.4); }
.empty i { font-size: 3rem; margin-bottom: 1rem; display: block; }

.questions-list { display: flex; flex-direction: column; gap: 0.5rem; }
.question-row {
  display: flex; align-items: center; justify-content: space-between;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px; padding: 1rem 1.25rem; cursor: pointer; transition: all 0.2s;
}
.question-row:hover { background: rgba(255,255,255,0.07); border-color: rgba(102,126,234,0.3); transform: translateX(4px); }
.q-main { flex: 1; }
.q-main h3 { color: white; font-size: 0.95rem; margin: 0 0 0.5rem; font-weight: 500; line-height: 1.4; }
.q-meta { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.q-prob { color: rgba(255,255,255,0.5); font-size: 0.8rem; display: flex; align-items: center; gap: 0.3rem; }
.q-arrow { color: rgba(255,255,255,0.2); }
</style>
