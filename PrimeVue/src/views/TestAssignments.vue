<template>
  <div class="page">
    <NavBar />
    <div class="max-w-container ta-page">
      <div class="ta-headline">
        <div>
          <p class="eyebrow">Assignments</p>
          <h1 class="heading h-page"><BrandIcon name="assignments" :size="30" /> Тестовые задания</h1>
          <p class="sub">Реальные тестовые задания от IT-компаний для практики</p>
        </div>
        <div class="ta-kpi">{{ total }} в базе</div>
      </div>

      <!-- Filters -->
      <div class="filters">
        <select v-model="selectedProfession" class="input">
          <option value="">Все профессии</option>
          <option v-for="p in profOptions" :key="p" :value="p">{{ p }}</option>
        </select>
        <select v-model="selectedDifficulty" class="input">
          <option value="">Любая сложность</option>
          <option value="junior">Junior</option>
          <option value="middle">Middle</option>
          <option value="senior">Senior</option>
        </select>
        <div class="search-wrap">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
          <input v-model="searchQuery" class="input search-input" placeholder="Поиск..." />
        </div>
      </div>

      <div v-if="loading" class="center-block"><div class="spinner"></div></div>

      <template v-else-if="assignments.length">
        <div class="list-meta">
          <span>Показано {{ assignments.length }} из {{ total }}</span>
        </div>

        <div class="grid">
          <div v-for="a in assignments" :key="a.id" class="ta-card card card-hover">
            <div class="ta-head" :class="a.difficulty">
              <span class="badge" :class="diffBadge(a.difficulty)">{{ a.difficulty }}</span>
              <span v-if="a.company" class="company">{{ a.company }}</span>
            </div>
            <router-link :to="'/test-assignments/' + a.id" class="ta-title">{{ a.title }}</router-link>
            <p class="ta-desc">{{ a.description }}</p>
            <div v-if="a.profession" class="ta-prof">{{ a.profession }}</div>
            <div v-if="a.skills_list?.length" class="ta-skills">
              <span v-for="s in a.skills_list" :key="s" class="badge badge-info">{{ s }}</span>
            </div>
            <div class="ta-foot">
              <router-link :to="'/test-assignments/' + a.id" class="btn btn-ghost btn-sm">Подробнее →</router-link>
              <a v-if="a.link" :href="a.link" target="_blank" class="btn btn-secondary btn-sm">Открыть</a>
              <span class="ta-date">{{ fmtDate(a.created_at) }}</span>
            </div>
          </div>
        </div>
      </template>

      <div v-else class="empty-state">
        <p>Тестовые задания не найдены</p>
        <small>Попробуйте изменить фильтры</small>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pg">
        <button class="btn btn-ghost btn-sm" :disabled="page <= 1" @click="page--; loadData()">←</button>
        <span>{{ page }} / {{ totalPages }}</span>
        <button class="btn btn-ghost btn-sm" :disabled="page >= totalPages" @click="page++; loadData()">→</button>
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
import BrandIcon from '../components/BrandIcon.vue'
import api from '../api/client'

const router = useRouter()
const assignments = ref([])
const loading = ref(true)
const page = ref(1)
const total = ref(0)
const perPage = 12

const selectedProfession = ref('')
const selectedDifficulty = ref('')
const searchQuery = ref('')

const profOptions = ['Frontend разработчик', 'Backend разработчик', 'Python разработчик', 'Java разработчик', 'DevOps инженер', 'QA инженер', 'Data Scientist', 'Mobile разработчик']
const totalPages = computed(() => Math.ceil(total.value / perPage))
const diffBadge = (d) => ({ junior: 'badge-ok', middle: 'badge-warn', senior: 'badge-err' }[d] || 'badge-muted')
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU', { year: 'numeric', month: 'short', day: 'numeric' }) : ''

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, per_page: perPage }
    if (selectedProfession.value) params.profession = selectedProfession.value
    if (selectedDifficulty.value) params.difficulty = selectedDifficulty.value
    if (searchQuery.value) params.search = searchQuery.value
    const r = await api.getTestAssignments(params)
    assignments.value = r.data.assignments || []; total.value = r.data.total || 0
  } catch (e) { console.error(e) }
  loading.value = false
}

let timer = null
watch([selectedProfession, selectedDifficulty], () => { page.value = 1; loadData() })
watch(searchQuery, () => { clearTimeout(timer); timer = setTimeout(() => { page.value = 1; loadData() }, 400) })
onMounted(loadData)
</script>

<style scoped>
.ta-page {
  padding-top: 1.2rem;
  padding-bottom: 3rem;
}

.eyebrow {
  margin: 0 0 .28rem;
  font-family: var(--app-font-mono);
  color: var(--text-secondary);
  font-size: .76rem;
  letter-spacing: .03em;
}

.ta-headline {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: .75rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.heading { display:flex; align-items:center; justify-content:flex-start; gap:.55rem; margin-bottom: .3rem; }
.sub { text-align: left; color: var(--text-secondary); font-size: .95rem; margin-bottom: 1rem; }

.ta-kpi {
  border: 1px solid color-mix(in srgb, var(--c-border-h) 82%, transparent);
  background: color-mix(in srgb, var(--c-brand-bg) 58%, transparent);
  border-radius: 999px;
  padding: .45rem .85rem;
  font-size: .82rem;
  color: var(--c-brand-h);
  font-weight: 700;
}

.filters {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: .75rem;
  margin-bottom: .85rem;
  position: sticky;
  top: calc(var(--nav-h) + .55rem);
  z-index: 15;
  padding: .55rem;
  border-radius: 10px;
  background: color-mix(in srgb, var(--c-bg-1) 68%, transparent);
  border: 1px solid color-mix(in srgb, var(--c-border-h) 72%, transparent);
  backdrop-filter: blur(10px);
}
.filters .input { min-width: 180px; }
.search-wrap { position: relative; }
.search-icon { position: absolute; left: .65rem; top: 50%; transform: translateY(-50%); color: var(--c-text-4); pointer-events: none; }
.search-input { padding-left: 2.1rem; width: 100%; }
.center-block { display: flex; justify-content: center; padding: 3rem; }

.list-meta {
  margin-bottom: .85rem;
  color: var(--c-text-4);
  font-size: .84rem;
}

.grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .9rem; }
.ta-card { 
  padding: 0; 
  overflow: hidden; 
  display: flex; 
  flex-direction: column;
  border: 1px solid var(--c-border);
  border-radius: 10px;
  transition: transform var(--dur-250) var(--ease-curve-a), box-shadow var(--dur-250) var(--ease-curve-a), border-color var(--dur-250) ease;
}
.ta-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
  border-color: var(--c-border-h);
}
.ta-head { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  padding: 1rem 1.25rem; 
  background: linear-gradient(145deg, color-mix(in srgb, var(--c-bg-2) 82%, transparent), color-mix(in srgb, var(--c-surface-a) 72%, transparent));
  border-bottom: 1px solid var(--c-border);
}
.ta-head.junior { border-left: 4px solid var(--c-ok); }
.ta-head.middle { border-left: 4px solid var(--c-warn); }
.ta-head.senior { border-left: 4px solid var(--c-err); }
.company { 
  font-weight: 700; 
  font-size: .95rem;
  color: var(--c-text);
}
.ta-title { 
  padding: .82rem 1rem 0; 
  font-weight: 600; 
  font-size: 1.02rem; 
  color: var(--c-text); 
  text-decoration: none;
  line-height: 1.35;
  transition: color var(--dur);
}
.ta-title:hover { color: var(--c-brand); }
.ta-desc { 
  padding: .42rem 1rem; 
  font-size: .89rem; 
  color: var(--c-text-3); 
  line-height: 1.5; 
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.ta-prof { 
  padding: 0 1rem; 
  font-size: .84rem; 
  color: var(--c-text-2); 
  margin-bottom: .6rem;
  font-weight: 500;
}
.ta-skills { 
  padding: 0 1rem .6rem; 
  display: flex; 
  flex-wrap: wrap; 
  gap: .28rem;
  max-height: none;
  overflow: visible;
}
.ta-skills .badge {
  text-transform: none;
  letter-spacing: 0;
  font-size: .78rem;
}
.ta-foot { 
  display: flex; 
  align-items: center; 
  gap: .45rem; 
  padding: .72rem 1rem; 
  border-top: 1px solid var(--c-border);
  background: var(--c-surface);
}
.ta-date { 
  margin-left: auto; 
  color: var(--c-text-4); 
  font-size: .82rem;
  white-space: nowrap;
}
.pg { display: flex; justify-content: center; align-items: center; gap: .75rem; margin-top: 1.5rem; color: var(--c-text-2); font-size: .88rem; }
.empty-state { text-align: center; padding: 3rem; color: var(--c-text-4); }

@media (max-width: 1024px) {
  .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 640px) {
  .heading,
  .sub {
    text-align: left;
    justify-content: flex-start;
  }

  .filters {
    grid-template-columns: 1fr;
    top: calc(var(--nav-h) + .45rem);
  }
  .filters .input, .search-wrap { min-width: auto; max-width: none; width: 100%; }
  .grid { grid-template-columns: 1fr; }
}
</style>
