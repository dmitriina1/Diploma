<template>
  <div class="assignments-page">
    <NavBar />
    
    <div class="assignments-container">
      <h1 class="page-title">
        <i class="pi pi-file-edit"></i> Тестовые задания
      </h1>
      <p class="page-subtitle">Реальные тестовые задания от IT-компаний для практики</p>

      <!-- Filters -->
      <div class="filters">
        <Dropdown v-model="selectedProfession" :options="professionOptions" placeholder="Все профессии" 
                  showClear class="filter-item" />
        <Dropdown v-model="selectedDifficulty" :options="difficulties" optionLabel="label" optionValue="value"
                  placeholder="Любая сложность" showClear class="filter-item" />
        <InputText v-model="searchQuery" placeholder="Поиск..." class="filter-item search-input" />
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading">
        <ProgressSpinner />
      </div>

      <!-- Assignments Grid -->
      <div v-else class="assignments-grid">
        <Card v-for="a in assignments" :key="a.id" class="assignment-card">
          <template #header>
            <div class="assignment-header" :class="a.difficulty">
              <Tag :value="a.difficulty" :severity="diffSeverity(a.difficulty)" />
              <span class="company" v-if="a.company">{{ a.company }}</span>
            </div>
          </template>
          <template #title>
            <router-link :to="'/test-assignments/' + a.id" class="assignment-title-link">
              {{ a.title }}
            </router-link>
          </template>
          <template #content>
            <p class="assignment-desc">{{ a.description }}</p>
            
            <div v-if="a.profession" class="assignment-profession">
              <i class="pi pi-user"></i> {{ a.profession }}
            </div>
            
            <div v-if="a.skills_list && a.skills_list.length" class="assignment-skills">
              <Tag v-for="skill in a.skills_list" :key="skill" :value="skill" 
                   severity="info" rounded class="skill-tag" />
            </div>
          </template>
          <template #footer>
            <div class="assignment-footer">
              <Button label="Подробнее" icon="pi pi-arrow-right" size="small" severity="secondary" text
                      @click="router.push('/test-assignments/' + a.id)" />
              <Button v-if="a.link" label="Открыть" icon="pi pi-external-link" size="small"
                      @click.stop="openLink(a.link)" />
              <span class="assignment-date">{{ formatDate(a.created_at) }}</span>
            </div>
          </template>
        </Card>
      </div>

      <!-- Empty -->
      <div v-if="!loading && assignments.length === 0" class="empty-state">
        <i class="pi pi-inbox"></i>
        <h3>Тестовые задания не найдены</h3>
        <p>Попробуйте изменить фильтры</p>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination">
        <Button icon="pi pi-chevron-left" text :disabled="page <= 1" @click="page--; loadData()" />
        <span class="page-info">{{ page }} / {{ totalPages }}</span>
        <Button icon="pi pi-chevron-right" text :disabled="page >= totalPages" @click="page++; loadData()" />
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import api from '../api/client'

const router = useRouter()

const assignments = ref([])
const loading = ref(true)
const page = ref(1)
const total = ref(0)
const perPage = 12

const selectedProfession = ref(null)
const selectedDifficulty = ref(null)
const searchQuery = ref('')

const professionOptions = ref([
  'Frontend разработчик', 'Backend разработчик', 'Python разработчик',
  'Java разработчик', 'DevOps инженер', 'QA инженер', 
  'Data Scientist', 'Mobile разработчик'
])

const difficulties = [
  { label: 'Junior', value: 'junior' },
  { label: 'Middle', value: 'middle' },
  { label: 'Senior', value: 'senior' }
]

const totalPages = computed(() => Math.ceil(total.value / perPage))

const diffSeverity = (d) => {
  return { junior: 'success', middle: 'warning', senior: 'danger' }[d] || 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('ru-RU', { year: 'numeric', month: 'short', day: 'numeric' })
}

const openLink = (link) => {
  window.open(link, '_blank')
}

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, per_page: perPage }
    if (selectedProfession.value) params.profession = selectedProfession.value
    if (selectedDifficulty.value) params.difficulty = selectedDifficulty.value
    if (searchQuery.value) params.search = searchQuery.value

    const r = await api.getTestAssignments(params)
    assignments.value = r.data.assignments || []
    total.value = r.data.total || 0
  } catch (e) {
    console.error('Failed to load test assignments:', e)
  }
  loading.value = false
}

let searchTimer = null
watch([selectedProfession, selectedDifficulty], () => { page.value = 1; loadData() })
watch(searchQuery, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadData() }, 400)
})

onMounted(loadData)
</script>

<style scoped>
.assignments-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
}
.assignments-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}
.page-title {
  font-size: 2.2rem;
  text-align: center;
  color: white;
  margin-bottom: 0.5rem;
}
.page-title i { color: #fa709a; }
.page-subtitle {
  text-align: center;
  color: rgba(255,255,255,0.6);
  margin-bottom: 2rem;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  justify-content: center;
}
.filter-item { min-width: 200px; }
.search-input { flex: 1; max-width: 300px; }

.assignments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.assignment-card {
  transition: all 0.3s;
  border-radius: 16px;
  overflow: hidden;
}
.assignment-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(102,126,234,0.2);
}

.assignment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, rgba(102,126,234,0.2), rgba(118,75,162,0.2));
}
.assignment-header.junior { background: linear-gradient(135deg, rgba(34,197,94,0.15), rgba(20,184,166,0.15)); }
.assignment-header.middle { background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(234,88,12,0.15)); }
.assignment-header.senior { background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(190,18,60,0.15)); }
.company { 
  font-weight: 700; 
  color: rgba(255,255,255,0.9); 
  font-size: 0.95rem;
}

.assignment-desc {
  color: rgba(255,255,255,0.7);
  line-height: 1.6;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}
.assignment-profession {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: rgba(255,255,255,0.6);
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
}
.assignment-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}
.skill-tag { font-size: 0.75rem !important; }

.assignment-footer {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.assignment-footer .assignment-date { margin-left: auto; }
.assignment-title-link {
  color: white;
  text-decoration: none;
  transition: color 0.2s;
}
.assignment-title-link:hover { color: #60a5fa; }
.assignment-date {
  color: rgba(255,255,255,0.4);
  font-size: 0.8rem;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 4rem;
}
.empty-state {
  text-align: center;
  padding: 4rem;
  color: rgba(255,255,255,0.4);
}
.empty-state i { font-size: 4rem; display: block; margin-bottom: 1rem; }
.empty-state h3 { color: rgba(255,255,255,0.6); }

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}
.page-info { color: rgba(255,255,255,0.7); font-weight: 600; }

@media (max-width: 768px) {
  .filters { flex-direction: column; }
  .filter-item { min-width: auto; width: 100%; }
  .search-input { max-width: none; }
  .assignments-grid { grid-template-columns: 1fr; }
}
</style>
