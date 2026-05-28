<template>
  <div class="page assignments-page">
    <NavBar />
    <main class="screen narrow assignments">
      <section class="assignments-head">
        <div>
          <span class="eyebrow">Практика компаний</span>
          <h1>Тестовые задания</h1>
          <p>Карточки с требованиями, стеком и контекстом задачи без лишних блоков вокруг.</p>
        </div>
        <div class="head-stat glass">
          <b>{{ filteredAssignments.length }}</b>
          <span>доступно</span>
        </div>
      </section>

      <section class="assignment-toolbar glass">
        <select v-model="selectedProfession" class="field"><option value="">Все профессии</option><option v-for="p in profOptions" :key="p">{{ p }}</option></select>
        <select v-model="selectedDifficulty" class="field"><option value="">Любая сложность</option><option value="junior">Junior</option><option value="middle">Middle</option><option value="senior">Senior</option></select>
        <input v-model="searchQuery" class="field" placeholder="Поиск заданий, компаний, технологий..." />
      </section>

      <section class="assignment-grid">
        <article v-for="item in paginatedAssignments" :key="item.id" class="assignment-card glass" :class="levelOf(item)" @click="router.push(`/test-assignments/${item.id}`)">
          <header>
            <span :class="`tag ${levelOf(item)}`">{{ levelLabel(levelOf(item)) }}</span>
            <div class="company">
              <span>{{ item.company }}</span>
              <b :style="companyStyle(item.company)">{{ logoText(item) }}</b>
            </div>
          </header>
          <h2>{{ item.title }}</h2>
          <p>{{ item.text || item.description }}</p>
          <small>{{ item.role || item.profession }}</small>
          <div class="tags">
            <span v-for="tag in tagsOf(item)" :key="tag" class="tag">{{ tag }}</span>
          </div>
          <footer><router-link :to="`/test-assignments/${item.id}`" @click.stop>Подробнее <i class="pi pi-arrow-right"></i></router-link><time>{{ fmtDate(item.created_at) || '18 апр. 2026' }}</time></footer>
        </article>
      </section>
      <nav v-if="totalPages > 1" class="pagination" aria-label="Пагинация заданий">
        <button :disabled="page <= 1" @click="goToPage(page - 1)"><i class="pi pi-angle-left"></i></button>
        <button
          v-for="item in visiblePages"
          :key="item.key"
          :class="{ active: item.value === page, ellipsis: item.type === 'ellipsis' }"
          :disabled="item.type === 'ellipsis'"
          @click="item.type === 'page' && goToPage(item.value)"
        >
          {{ item.label }}
        </button>
        <button :disabled="page >= totalPages" @click="goToPage(page + 1)"><i class="pi pi-angle-right"></i></button>
      </nav>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import NavBar from '../components/NavBar.vue'
import api from '../api/client'
import { assignments as fallbackAssignments } from '../data/mock'

const router = useRouter()
const assignments = ref(fallbackAssignments)
const total = ref(0)
const selectedProfession = ref('')
const selectedDifficulty = ref('')
const searchQuery = ref('')
const page = ref(1)
const pageSize = 15
const profOptions = ['Frontend разработчик', 'Backend разработчик', 'Python разработчик', 'Java разработчик', 'DevOps инженер', 'QA инженер', 'Data Scientist']

const levelOf = (item) => (item.level || item.difficulty || 'junior').toLowerCase()
const tagsOf = (item) => item.tags || item.skills_list || []
const levelLabel = (level) => ({ junior: 'Junior', middle: 'Middle', senior: 'Senior' }[level] || level)
const logoText = (item) => String(item.logo || item.company || 'IH').replace(/[^\p{L}\p{N}✓●]/gu, '').slice(0, 2).toUpperCase()
const companyPalette = ['#ff4d3d', '#111827', '#1687ff', '#ffd629', '#7c3aed', '#ef233c', '#0ea5e9', '#12b981', '#f97316', '#2563eb']
const companyStyle = (company = '') => {
  const code = [...company].reduce((sum, char) => sum + char.charCodeAt(0), 0)
  const bg = companyPalette[code % companyPalette.length]
  const darkText = bg === '#ffd629'
  return { background: bg, color: darkText ? '#111827' : '#fff', borderColor: darkText ? 'rgba(255,255,255,.18)' : 'rgba(255,255,255,.12)' }
}
const fmtDate = (date) => date ? new Date(date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' }) : ''
const demoAssignments = [
  ['Интерактивная доска задач на Vue', 'Ozon', 'OZ', 'Frontend разработчик', 'junior', ['Vue', 'Pinia', 'CSS'], 'Собрать kanban-доску с drag-and-drop, фильтрами и сохранением состояния.'],
  ['API бронирования переговорок', 'Авито', 'A', 'Backend разработчик', 'middle', ['Python', 'FastAPI', 'PostgreSQL'], 'Реализовать сервис бронирования с конфликтами времени и ролями пользователей.'],
  ['Сервис уведомлений', 'Яндекс', 'Я', 'Backend разработчик', 'middle', ['Go', 'Kafka', 'Redis'], 'Спроектировать отправку email/push-уведомлений с очередью и повторными попытками.'],
  ['Дашборд продаж', 'СБЕР', '✓', 'Data Analyst', 'junior', ['SQL', 'Python', 'BI'], 'Подготовить витрины данных и визуализацию ключевых метрик продаж.'],
  ['Автотесты для формы оплаты', 'VK', 'vk', 'QA инженер', 'junior', ['Playwright', 'TypeScript', 'API'], 'Покрыть критический путь оплаты UI и API-тестами.'],
  ['Инфраструктура staging', 'МТС', '●', 'DevOps инженер', 'middle', ['Docker', 'Nginx', 'CI/CD'], 'Настроить окружение staging с деплоем по веткам и health-check.'],
  ['Рекомендательная модель', 'Wildberries', 'WB', 'Data Scientist', 'middle', ['Python', 'pandas', 'ML'], 'Построить baseline рекомендаций и объяснить метрики качества.'],
  ['Поиск по каталогу товаров', 'Т-Банк', 'T', 'Backend разработчик', 'middle', ['Elasticsearch', 'Java', 'REST'], 'Реализовать полнотекстовый поиск с фильтрами, сортировкой и подсказками.'],
  ['Личный кабинет кандидата', 'HH', 'HH', 'Frontend разработчик', 'middle', ['React', 'TypeScript', 'Forms'], 'Собрать кабинет с профилем, загрузкой файлов и валидацией форм.'],
  ['План нагрузочного тестирования', 'Ростелеком', 'RT', 'QA инженер', 'middle', ['JMeter', 'SQL', 'Monitoring'], 'Подготовить профиль нагрузки, сценарии и отчёт по bottleneck в API.'],
  ['Сервис коротких ссылок', '2ГИС', '2G', 'Backend разработчик', 'junior', ['Node.js', 'Redis', 'PostgreSQL'], 'Сделать генерацию коротких ссылок, статистику переходов и TTL.'],
  ['Мобильный экран избранного', 'Самокат', 'S', 'Frontend разработчик', 'junior', ['Vue', 'Responsive', 'API'], 'Сверстать адаптивный экран с состояниями загрузки, пустым списком и ошибками.'],
  ['ML pipeline для классификации', 'МегаФон', 'MF', 'Data Scientist', 'senior', ['Python', 'Airflow', 'MLflow'], 'Описать и реализовать pipeline обучения, валидации и версионирования модели.'],
  ['Observability для микросервиса', 'Selectel', 'SL', 'DevOps инженер', 'senior', ['Prometheus', 'Grafana', 'Tracing'], 'Подключить метрики, алерты, трассировку и dashboard для production-сервиса.'],
  ['Парсер вакансий и отчёт', 'Хабр', 'H', 'Data Analyst', 'junior', ['Python', 'SQL', 'Charts'], 'Собрать данные, очистить их и подготовить отчёт по востребованным навыкам.']
].map((item, index) => ({ id: `demo-${index + 1}`, title: item[0], company: item[1], logo: item[2], role: item[3], level: item[4], tags: item[5], text: item[6] }))
const visibleAssignments = computed(() => [...assignments.value, ...demoAssignments])
const filteredAssignments = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return visibleAssignments.value.filter((item) => {
    const haystack = [item.title, item.company, item.role, item.profession, item.text, item.description, ...(tagsOf(item))].join(' ').toLowerCase()
    if (selectedProfession.value && (item.profession || item.role) !== selectedProfession.value) return false
    if (selectedDifficulty.value && levelOf(item) !== selectedDifficulty.value) return false
    return !q || haystack.includes(q)
  })
})
const totalPages = computed(() => Math.max(1, Math.ceil(filteredAssignments.value.length / pageSize)))
const paginatedAssignments = computed(() => filteredAssignments.value.slice((page.value - 1) * pageSize, page.value * pageSize))
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

async function loadData() {
  try {
    const r = await api.getTestAssignments({ page: 1, per_page: 30 })
    const list = r.data.assignments || []
    if (list.length) assignments.value = list
    total.value = Math.max(r.data.total || list.length, visibleAssignments.value.length)
  } catch {
    total.value = visibleAssignments.value.length
  }
}

function goToPage(nextPage) {
  page.value = Math.min(Math.max(nextPage, 1), totalPages.value)
}

watch([selectedProfession, selectedDifficulty, searchQuery], () => { page.value = 1 })
onMounted(loadData)
</script>

<style scoped>
.assignments { padding-top: 34px; padding-bottom: 56px; }
.assignments-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 28px; margin-bottom: 24px; }
.eyebrow { display: inline-block; margin-bottom: 10px; color: var(--cyan); text-transform: uppercase; font-size: 13px; font-weight: 800; letter-spacing: .08em; }
.assignments-head h1 { margin: 0 0 8px; font-size: 46px; line-height: 1.05; letter-spacing: -.04em; }
.assignments-head p { margin: 0; max-width: 760px; color: var(--muted); font-size: 19px; line-height: 1.45; }
.head-stat { min-width: 150px; padding: 18px 22px; text-align: right; }
.head-stat b { display: block; font-size: 34px; line-height: 1; }
.head-stat span { color: var(--muted); font-weight: 700; }
.assignment-toolbar { display: grid; grid-template-columns: .9fr .8fr 1.4fr; gap: 14px; padding: 14px; margin-bottom: 22px; }
.assignment-toolbar .field { height: 54px; }
.assignment-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.assignment-card {
  min-height: 314px;
  padding: 20px 22px 0;
  display: flex;
  flex-direction: column;
  border-left: 3px solid transparent;
  cursor: pointer;
  overflow: hidden;
  transition: transform .18s ease, border-color .18s ease, background .18s ease;
}
.assignment-card:hover { transform: translateY(-3px); border-color: var(--line-strong); background: linear-gradient(180deg, rgba(11, 43, 70, .92), rgba(5, 27, 48, .88)); }
.assignment-card.junior { border-left-color: var(--cyan); }
.assignment-card.middle { border-left-color: var(--yellow); }
.assignment-card.senior { border-left-color: var(--red); }
.assignment-card header, .assignment-card footer { display: flex; justify-content: space-between; align-items: center; gap: 18px; }
.company { min-width: 0; display: flex; align-items: center; gap: 10px; font-weight: 800; }
.company span { max-width: 128px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #dfe8f4; }
.company b { width: 46px; height: 46px; flex: 0 0 46px; border-radius: 50%; display: grid; place-items: center; border: 1px solid rgba(255,255,255,.12); font-size: 16px; line-height: 1; letter-spacing: 0; overflow: hidden; }
.assignment-card h2 { margin: 24px 0 10px; font-size: 24px; line-height: 1.16; letter-spacing: -.03em; }
.assignment-card p { margin: 0 0 18px; color: var(--muted); font-size: 17px; line-height: 1.45; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.assignment-card small { color: #cdd6e3; font-size: 15px; margin-bottom: 16px; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }
.tags .tag { min-height: 26px; font-size: 13px; padding: 4px 10px; }
.assignment-card footer {
  margin: auto -22px 0;
  min-height: 54px;
  padding: 0 22px;
  border-top: 1px solid rgba(83, 121, 148, .14);
  color: var(--muted);
}
.assignment-card footer a { color: #dbe3ef; font-weight: 800; display: inline-flex; align-items: center; gap: 7px; }
.assignment-card time { font-size: 14px; white-space: nowrap; }
.pagination { display: flex; justify-content: center; align-items: center; gap: 10px; margin-top: 28px; color: var(--muted); }
.pagination button { width: 45px; height: 45px; display: grid; place-items: center; border-radius: 8px; border: 1px solid rgba(83, 121, 148, .16); background: rgba(4, 20, 37, .62); color: var(--text); font-weight: 800; transition: .18s ease; }
.pagination button:not(:disabled):hover { border-color: var(--line-strong); color: var(--cyan); transform: translateY(-1px); }
.pagination button:disabled { opacity: .45; cursor: not-allowed; }
.pagination .active { background: linear-gradient(135deg, var(--cyan), #0aa894); color: white; border-color: transparent; }
.pagination .ellipsis { background: transparent; border-color: transparent; color: var(--soft); }

@media (max-width: 1100px) {
  .assignment-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 720px) {
  .assignments-head { display: block; }
  .head-stat { margin-top: 16px; text-align: left; }
  .assignment-grid { grid-template-columns: 1fr; }
  .assignment-toolbar { grid-template-columns: 1fr; }
}
</style>
