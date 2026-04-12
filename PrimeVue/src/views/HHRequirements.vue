<template>
  <div class="page">
    <NavBar />
    <div class="container-lg" style="padding-top:2rem;padding-bottom:3rem">
      <h1 class="heading h-page"><BrandIcon name="skills" :size="34" /> Навыки из вакансий</h1>
      <p class="sub">Какие навыки требуют работодатели и как часто они встречаются (данные обновляются автоматически из hh.ru)</p>

      <div v-if="auth.isAdmin" class="sync-actions">
        <button class="btn btn-secondary btn-sm" :disabled="syncing" @click="runSyncNow">
          {{ syncing ? 'Синхронизация...' : 'Обновить из HH сейчас' }}
        </button>
        <span class="muted">Автообновление: примерно раз в 24 часа</span>
      </div>

      <!-- Source Filters -->
      <div class="source-filters">
        <div class="sf-label">Источник данных:</div>
        <label class="sf-check">
          <input type="checkbox" v-model="sources.skills" @change="loadSkills" />
          <span>Навыки</span>
        </label>
        <label class="sf-check">
          <input type="checkbox" v-model="sources.description" @change="loadSkills" />
          <span>Описание</span>
        </label>
        <label class="sf-check">
          <input type="checkbox" v-model="sources.title" @change="loadSkills" />
          <span>Заголовок</span>
        </label>
      </div>

      <!-- Professions -->
      <div class="prof-row">
        <button v-for="p in professions" :key="p.profession" class="btn btn-sm"
                :class="selected === p.profession ? 'btn-primary' : 'btn-secondary'"
                @click="selectProfession(p.profession)">{{ p.profession }}</button>
      </div>

      <div v-if="loading" class="chart">
        <div v-for="i in 8" :key="i" class="skeleton-card"><div class="skeleton-line lg" style="margin-bottom:.45rem"></div><div class="skeleton-line" style="width:72%"></div></div>
      </div>

      <StatePanel
        v-else-if="loadError"
        icon="warning"
        type="error"
        title="Не удалось загрузить HH-аналитику"
        :description="loadError"
      >
        <button class="btn btn-secondary btn-sm" @click="loadSkills">Повторить</button>
      </StatePanel>

      <template v-else-if="skills.length > 0">
        <div class="skills-head">
          <h2>{{ selected || 'Все профессии' }}</h2>
          <span v-if="skills[0]?.total_vacancies" class="muted">~{{ skills[0].total_vacancies }} вакансий</span>
          <span class="muted">{{ totalSkills }} навыков</span>
          <span class="muted">Режим: {{ activeSourceTitle }}</span>
        </div>

        <div class="chart">
          <div v-for="(s, i) in skills" :key="s.skill" class="skill-row" :style="{ animationDelay: (i * .04) + 's' }">
            <div class="sk-info"><span class="sk-rank">#{{ i + 1 }}</span><span class="sk-name">{{ s.skill }}</span></div>
            <div class="sk-bar-wrap">
              <div class="sk-bar" :style="{ width: s.percentage + '%', background: barColor(s.percentage) }"></div>
              <span class="sk-pct">{{ s.percentage.toFixed(0) }}%</span>
            </div>
            <span class="sk-count">{{ s.vacancy_count }} вак.</span>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="totalSkills > perPage" class="pg">
          <button class="btn btn-ghost btn-sm" :disabled="page <= 1" @click="page--; loadSkills()">←</button>
          <span>{{ page }} / {{ Math.ceil(totalSkills / perPage) }}</span>
          <button class="btn btn-ghost btn-sm" :disabled="page >= Math.ceil(totalSkills / perPage)" @click="page++; loadSkills()">→</button>
        </div>

        <!-- Summary -->
        <div class="summary-grid">
          <div class="sum-card must"><h4>Must-have (&gt;50%)</h4><div class="sum-tags"><span v-for="s in mustHave" :key="s.skill" class="badge badge-err">{{ s.skill }} ({{ s.percentage.toFixed(0) }}%)</span></div></div>
          <div class="sum-card nice"><h4>Nice-to-have (20–50%)</h4><div class="sum-tags"><span v-for="s in niceToHave" :key="s.skill" class="badge badge-warn">{{ s.skill }} ({{ s.percentage.toFixed(0) }}%)</span></div></div>
          <div class="sum-card bonus"><h4>Дополнительно (&lt;20%)</h4><div class="sum-tags"><span v-for="s in bonusSkills" :key="s.skill" class="badge badge-info">{{ s.skill }} ({{ s.percentage.toFixed(0) }}%)</span></div></div>
        </div>

        <p class="method-note">Категории зависят от выбранного источника: при переключении между навыками, описанием и заголовками распределение может заметно меняться.</p>
      </template>

      <StatePanel
        v-else
        icon="empty"
        title="Нет данных для отображения"
        description="Выберите профессию для просмотра навыков"
      />
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
import { useAuthStore } from '../store/auth'

const loading = ref(false)
const syncing = ref(false)
const professions = ref([])
const skills = ref([])
const selected = ref(null)
const page = ref(1)
const perPage = ref(30)
const totalSkills = ref(0)
const loadError = ref('')
const auth = useAuthStore()

// Source filters
const sources = ref({
  skills: true,
  description: true,
  title: true
})

const mustHave = computed(() => skills.value.filter(s => s.percentage > 50))
const niceToHave = computed(() => skills.value.filter(s => s.percentage >= 20 && s.percentage <= 50))
const bonusSkills = computed(() => skills.value.filter(s => s.percentage < 20))

const activeSourceTitle = computed(() => {
  const labels = []
  if (sources.value.skills) labels.push('Навыки')
  if (sources.value.description) labels.push('Описание')
  if (sources.value.title) labels.push('Заголовок')
  return labels.length ? labels.join(' + ') : 'Навыки'
})

const barColor = (p) => {
  if (p >= 70) return 'linear-gradient(90deg, var(--c-err), #dc2626)'
  if (p >= 50) return 'linear-gradient(90deg, var(--c-warn), #ea580c)'
  if (p >= 30) return 'linear-gradient(90deg, var(--c-brand), var(--c-brand-h))'
  return 'linear-gradient(90deg, var(--c-ok), #14b8a6)'
}

const selectProfession = async (p) => { selected.value = p; page.value = 1; await loadSkills() }

const loadSkills = async () => {
  loading.value = true
  loadError.value = ''
  try {
    // Build sources string from checkboxes
    const selectedSources = []
    if (sources.value.skills) selectedSources.push('skills')
    if (sources.value.description) selectedSources.push('description')
    if (sources.value.title) selectedSources.push('title')

    // Keep at least one source selected; default back to combined mode.
    if (!selectedSources.length) {
      sources.value.skills = true
      sources.value.description = true
      sources.value.title = true
      selectedSources.push('skills', 'description', 'title')
    }

    const sourcesParam = selectedSources.join(',')
    
    const r = await api.getHHSkills(selected.value, page.value, perPage.value, sourcesParam)
    skills.value = (r.data.skills || []).sort((a, b) => b.percentage - a.percentage)
    totalSkills.value = r.data.total || 0
  } catch (e) { 
    console.error(e)
    loadError.value = 'Проверь подключение к backend и повтори позже.' 
  }
  loading.value = false
}

const runSyncNow = async () => {
  syncing.value = true
  try {
    await api.runHHSyncNow()
    page.value = 1
    await loadSkills()
  } catch (e) {
    console.error(e)
    alert(e.response?.data?.detail || 'Не удалось запустить синхронизацию HH')
  }
  syncing.value = false
}

onMounted(async () => {
  try {
    const r = await api.getHHProfessions()
    professions.value = r.data.professions || []
    if (professions.value.length) await selectProfession(professions.value[0].profession)
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
.heading { display:flex; align-items:center; justify-content:center; gap:.55rem; margin-bottom: .35rem; }
.sub { text-align: center; color: var(--c-text-3); font-size: .94rem; margin-bottom: 1.5rem; }
.sync-actions {
  display: flex;
  align-items: center;
  gap: .75rem;
  justify-content: center;
  flex-wrap: wrap;
  margin: -.5rem 0 1.2rem;
}

.source-filters {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  flex-wrap: wrap;
}
.source-filters:has(input:checked) {
  border-color: color-mix(in srgb, var(--c-brand) 40%, var(--c-border));
}
.sf-label {
  font-size: .9rem;
  font-weight: 600;
  color: var(--c-text-2);
}
.sf-check {
  display: flex;
  align-items: center;
  gap: .4rem;
  cursor: pointer;
  font-size: .9rem;
  color: var(--c-text-2);
  transition: color var(--dur);
}
.sf-check:hover {
  color: var(--c-text);
}
.sf-check input[type="checkbox"] {
  accent-color: var(--c-brand);
  width: 16px;
  height: 16px;
  cursor: pointer;
}
.sf-check input[type="checkbox"]:checked + span {
  color: var(--c-text);
  font-weight: 600;
}
.prof-row { display: flex; flex-wrap: wrap; gap: .4rem; justify-content: center; margin-bottom: 1.5rem; }
.center-block { display: flex; justify-content: center; padding: 3rem; }

.skills-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 1.25rem; flex-wrap: wrap; gap: .5rem; }
.skills-head h2 { font-size: 1.3rem; margin: 0; }
.muted { color: var(--c-text-4); font-size: .88rem; }

.chart { display: flex; flex-direction: column; gap: .45rem; margin-bottom: 1.5rem; }
.skill-row {
  display: grid; grid-template-columns: 180px 1fr 90px;
  align-items: center; gap: .75rem; padding: .4rem 0;
  animation: fadeUp .4s var(--ease) backwards;
}
.sk-info { display: flex; align-items: center; gap: .4rem; }
.sk-rank { font-weight: 800; color: var(--c-text-4); font-size: .88rem; min-width: 26px; }
.sk-name { font-weight: 600; font-size: .96rem; color: var(--c-text); }
.sk-bar-wrap {
  display: flex;
  align-items: center;
  gap: .6rem;
  height: 28px;
  background: color-mix(in srgb, var(--c-bg-2) 88%, transparent);
  border: 1px solid var(--c-border);
  border-radius: 6px;
  padding: 2px 8px 2px 2px;
}
.sk-bar {
  height: 100%;
  border-radius: 4px;
  transition: width .6s cubic-bezier(.4,0,.2,1);
  min-width: 4px;
  box-shadow: inset 0 -1px 0 rgba(255,255,255,.18);
}
.sk-pct { font-weight: 800; color: var(--c-text); font-size: .92rem; min-width: 36px; text-align: right; }
.sk-count { color: var(--c-text-4); font-size: .84rem; text-align: right; }

.pg { display: flex; justify-content: center; align-items: center; gap: .75rem; margin-bottom: 1.5rem; color: var(--c-text-2); font-size: .88rem; }

.summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: .75rem; }
.sum-card { background: var(--c-surface); border: 1px solid var(--c-border); border-radius: var(--r-md); padding: 1.15rem; }
.sum-card h4 { font-size: .94rem; font-weight: 600; margin-bottom: .6rem; }
.must h4 { color: var(--c-err); }
.nice h4 { color: var(--c-warn); }
.bonus h4 { color: var(--c-ok); }
.sum-tags { display: flex; flex-wrap: wrap; gap: .25rem; }
.sum-tags .badge {
  text-transform: none;
  letter-spacing: 0;
}
.method-note {
  margin-top: .85rem;
  color: var(--c-text-4);
  font-size: .82rem;
}
.empty-state { text-align: center; padding: 4rem; color: var(--c-text-4); }

@media (max-width: 640px) {
  .source-filters { justify-content: flex-start; }
  .skill-row { grid-template-columns: 1fr; gap: .2rem; }
  .sk-count { text-align: left; }
}
</style>
