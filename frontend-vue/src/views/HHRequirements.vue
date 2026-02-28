<template>
  <div class="hh-page">
    <NavBar />
    
    <div class="hh-container">
      <h1 class="page-title">
        <i class="pi pi-chart-bar"></i> Навыки из вакансий
      </h1>
      <p class="page-subtitle">Какие навыки требуют работодатели и как часто они встречаются в вакансиях</p>

      <!-- Profession selector -->
      <div class="profession-tabs">
        <Button v-for="prof in professions" :key="prof.profession"
                :label="prof.profession" size="small"
                :severity="selectedProfession === prof.profession ? undefined : 'secondary'"
                :outlined="selectedProfession !== prof.profession"
                @click="selectProfession(prof.profession)" />
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading">
        <ProgressSpinner />
      </div>

      <!-- Skills Chart -->
      <div v-else-if="currentSkills.length > 0" class="skills-container">
        <div class="skills-header">
          <h2>{{ selectedProfession || 'Все профессии' }}</h2>
          <span class="total-vacancies" v-if="currentSkills[0]?.total_vacancies">
            Проанализировано ~{{ currentSkills[0].total_vacancies }} вакансий
          </span>
        </div>

        <div class="skills-chart">
          <div v-for="(skill, index) in currentSkills" :key="skill.skill" class="skill-row"
               :style="{ animationDelay: `${index * 0.05}s` }">
            <div class="skill-info">
              <span class="skill-rank">#{{ index + 1 }}</span>
              <span class="skill-name">{{ skill.skill }}</span>
            </div>
            <div class="skill-bar-container">
              <div class="skill-bar" :style="{ width: skill.percentage + '%', background: getBarColor(skill.percentage) }">
              </div>
              <span class="skill-percentage">{{ skill.percentage.toFixed(0) }}%</span>
            </div>
            <div class="skill-count">
              {{ skill.vacancy_count }} вакансий
            </div>
          </div>
        </div>

        <!-- Summary cards -->
        <div class="summary-cards">
          <div class="summary-card must-have">
            <h4><i class="pi pi-exclamation-triangle"></i> Must-have (>50%)</h4>
            <div class="summary-tags">
              <Tag v-for="s in mustHaveSkills" :key="s.skill" :value="`${s.skill} (${s.percentage.toFixed(0)}%)`" 
                   severity="danger" class="summary-tag" />
            </div>
          </div>
          <div class="summary-card nice-have">
            <h4><i class="pi pi-star"></i> Nice-to-have (20-50%)</h4>
            <div class="summary-tags">
              <Tag v-for="s in niceToHaveSkills" :key="s.skill" :value="`${s.skill} (${s.percentage.toFixed(0)}%)`" 
                   severity="warning" class="summary-tag" />
            </div>
          </div>
          <div class="summary-card bonus">
            <h4><i class="pi pi-plus"></i> Бонус (<20%)</h4>
            <div class="summary-tags">
              <Tag v-for="s in bonusSkills" :key="s.skill" :value="`${s.skill} (${s.percentage.toFixed(0)}%)`" 
                   severity="info" class="summary-tag" />
            </div>
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div v-else-if="!loading" class="empty-state">
        <i class="pi pi-chart-bar"></i>
        <h3>Выберите профессию для просмотра навыков</h3>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import api from '../api/client'

const loading = ref(false)
const professions = ref([])
const allSkills = ref([])
const selectedProfession = ref(null)

const currentSkills = computed(() => {
  if (!selectedProfession.value) return []
  return allSkills.value
    .filter(s => s.profession === selectedProfession.value)
    .sort((a, b) => b.percentage - a.percentage)
})

const mustHaveSkills = computed(() => currentSkills.value.filter(s => s.percentage > 50))
const niceToHaveSkills = computed(() => currentSkills.value.filter(s => s.percentage >= 20 && s.percentage <= 50))
const bonusSkills = computed(() => currentSkills.value.filter(s => s.percentage < 20))

const getBarColor = (pct) => {
  if (pct >= 70) return 'linear-gradient(90deg, #ef4444, #dc2626)'
  if (pct >= 50) return 'linear-gradient(90deg, #f59e0b, #ea580c)'
  if (pct >= 30) return 'linear-gradient(90deg, #667eea, #764ba2)'
  return 'linear-gradient(90deg, #22c55e, #14b8a6)'
}

const selectProfession = async (prof) => {
  selectedProfession.value = prof
  loading.value = true
  try {
    const r = await api.getHHSkills(prof)
    allSkills.value = r.data.skills || []
  } catch (e) {
    console.error('Failed to load HH skills:', e)
  }
  loading.value = false
}

onMounted(async () => {
  try {
    const r = await api.getHHProfessions()
    professions.value = r.data.professions || []
    // Auto-select first profession
    if (professions.value.length > 0) {
      await selectProfession(professions.value[0].profession)
    }
  } catch (e) {
    console.error('Failed to load HH professions:', e)
  }
})
</script>

<style scoped>
.hh-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
}
.hh-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
}
.page-title {
  font-size: 2.2rem;
  text-align: center;
  color: white;
  margin-bottom: 0.5rem;
}
.page-title i { color: #4facfe; }
.page-subtitle {
  text-align: center;
  color: rgba(255,255,255,0.6);
  margin-bottom: 2rem;
}

.profession-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-bottom: 2rem;
}

.skills-container { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

.skills-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1.5rem;
}
.skills-header h2 { color: white; margin: 0; font-size: 1.5rem; }
.total-vacancies { color: rgba(255,255,255,0.4); font-size: 0.85rem; }

.skills-chart {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-bottom: 2rem;
}
.skill-row {
  display: grid;
  grid-template-columns: 200px 1fr 120px;
  align-items: center;
  gap: 1rem;
  padding: 0.6rem 0;
  animation: slideIn 0.5s ease backwards;
}
@keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } }

.skill-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.skill-rank {
  font-weight: 800;
  color: rgba(255,255,255,0.3);
  min-width: 28px;
  font-size: 0.85rem;
}
.skill-name {
  color: rgba(255,255,255,0.9);
  font-weight: 600;
  font-size: 0.95rem;
}

.skill-bar-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  height: 28px;
}
.skill-bar {
  height: 100%;
  border-radius: 6px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 4px;
}
.skill-percentage {
  font-weight: 800;
  color: rgba(255,255,255,0.9);
  min-width: 40px;
  text-align: right;
  font-size: 0.9rem;
}
.skill-count {
  color: rgba(255,255,255,0.4);
  font-size: 0.8rem;
  text-align: right;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}
.summary-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 1.25rem;
}
.summary-card h4 {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0 0 0.75rem;
  font-size: 0.9rem;
}
.must-have h4 { color: #ef4444; }
.nice-have h4 { color: #f59e0b; }
.bonus h4 { color: #22c55e; }
.summary-tags { display: flex; flex-wrap: wrap; gap: 0.3rem; }
.summary-tag { font-size: 0.75rem !important; }

.loading { display: flex; justify-content: center; padding: 4rem; }
.empty-state {
  text-align: center; padding: 4rem; color: rgba(255,255,255,0.4);
}
.empty-state i { font-size: 4rem; display: block; margin-bottom: 1rem; }

@media (max-width: 768px) {
  .skill-row { grid-template-columns: 1fr; gap: 0.3rem; }
  .skill-count { text-align: left; }
}
</style>
