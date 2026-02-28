<template>
  <div class="tech-selector">
    <h2>{{ mode === 'tech' ? 'Выберите технологию' : 'Выберите профессию' }}</h2>

    <div class="mode-toggle">
      <SelectButton v-model="mode" :options="modeOptions" optionLabel="label" optionValue="value"
                    :allowEmpty="false" />
    </div>

    <!-- Режим технологий -->
    <div v-if="mode === 'tech'" class="tech-grid">
      <Card v-for="tech in technologies" 
            :key="tech.name" 
            class="tech-card"
            @click="selectTech(tech.name)">
        <template #header>
          <div class="tech-icon" :style="{ background: tech.color }">
            <i :class="tech.icon"></i>
          </div>
        </template>
        <template #title>
          {{ tech.name }}
        </template>
        <template #content>
          <div class="tech-stats">
            <Badge :value="tech.count" severity="info" />
            <span>вопросов</span>
          </div>
        </template>
      </Card>
    </div>

    <!-- Режим профессий -->
    <div v-else class="tech-grid">
      <Card v-for="prof in professions" 
            :key="prof.slug" 
            class="tech-card"
            @click="selectProfession(prof)">
        <template #header>
          <div class="tech-icon" :style="{ background: prof.gradient }">
            <i :class="prof.icon"></i>
          </div>
        </template>
        <template #title>
          {{ prof.title }}
        </template>
        <template #content>
          <div class="tech-stats">
            <Badge :value="prof.question_count || 0" severity="info" />
            <span>вопросов</span>
          </div>
          <div class="prof-topics" v-if="prof.topics && prof.topics.length">
            <Tag v-for="t in prof.topics.slice(0, 4)" :key="t" :value="t" severity="secondary" rounded class="prof-tag" />
            <Tag v-if="prof.topics.length > 4" :value="'+' + (prof.topics.length - 4)" severity="secondary" rounded class="prof-tag" />
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuestionsStore } from '../store'
import api from '../api/client'

const router = useRouter()
const questionsStore = useQuestionsStore()

const mode = ref('tech')
const modeOptions = [
  { label: 'По технологиям', value: 'tech' },
  { label: 'По профессиям', value: 'prof' }
]

const professionsList = ref([])

const profGradients = {
  'frontend-developer': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'backend-developer': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'python-developer': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'java-developer': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'fullstack-developer': 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'devops': 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
  'qa-engineer': 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
  'data-scientist': 'linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%)',
  'mobile-developer': 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
  'golang-developer': 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)'
}

const technologies = computed(() => {
  const techConfig = {
    'Backend': { icon: 'pi pi-server', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
    'Frontend': { icon: 'pi pi-palette', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
    'Java': { icon: 'pi pi-code', color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' },
    'Python': { icon: 'pi pi-code', color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
    'JavaScript': { icon: 'pi pi-code', color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' },
    'Go': { icon: 'pi pi-code', color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' },
    'C#': { icon: 'pi pi-microsoft', color: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)' },
    'DevOps': { icon: 'pi pi-cloud', color: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)' },
    'Database': { icon: 'pi pi-database', color: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)' },
    'Algorithms': { icon: 'pi pi-chart-line', color: 'linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%)' },
    'System Design': { icon: 'pi pi-sitemap', color: 'linear-gradient(135deg, #fdcbf1 0%, #e6dee9 100%)' }
  }
  
  const topics = questionsStore.topics
  
  return topics.map(topic => {
    const config = techConfig[topic] || { 
      icon: 'pi pi-question-circle', 
      color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
    }
    
    const count = questionsStore.questions.filter(q => q.topic === topic).length
    
    return {
      name: topic,
      ...config,
      count
    }
  }).sort((a, b) => b.count - a.count)
})

const professions = computed(() => {
  return professionsList.value.map(p => ({
    ...p,
    gradient: profGradients[p.slug] || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  }))
})

const selectTech = (techName) => {
  router.push({ path: '/interview-questions', query: { topic: techName } })
}

const selectProfession = (prof) => {
  router.push({ path: '/interview-questions', query: { profession: prof.slug, profTitle: prof.title } })
}

const loadProfessions = async () => {
  try {
    const res = await api.getProfessions()
    professionsList.value = res.data.professions || []
  } catch (e) {
    console.error('Failed to load professions:', e)
  }
}

onMounted(() => {
  loadProfessions()
})
</script>

<style scoped>
.tech-selector {
  padding: 2rem 0;
  animation: slide-up 0.6s ease-out;
}

.tech-selector h2 {
  text-align: center;
  margin-bottom: 1.5rem;
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  position: relative;
  display: inline-block;
  width: 100%;
}

.tech-selector h2::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 100px;
  height: 4px;
  background: linear-gradient(90deg, transparent, #667eea, transparent);
  border-radius: 2px;
}

.mode-toggle {
  display: flex;
  justify-content: center;
  margin-bottom: 2.5rem;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem;
}

.tech-card {
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  animation: slide-up 0.6s ease-out backwards;
}

.tech-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.tech-card:hover::before {
  left: 100%;
}

.tech-card:nth-child(1) { animation-delay: 0.05s; }
.tech-card:nth-child(2) { animation-delay: 0.1s; }
.tech-card:nth-child(3) { animation-delay: 0.15s; }
.tech-card:nth-child(4) { animation-delay: 0.2s; }
.tech-card:nth-child(5) { animation-delay: 0.25s; }
.tech-card:nth-child(6) { animation-delay: 0.3s; }
.tech-card:nth-child(7) { animation-delay: 0.35s; }
.tech-card:nth-child(8) { animation-delay: 0.4s; }

.tech-card:hover {
  transform: translateY(-12px) scale(1.03);
  box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.1);
  z-index: 10;
}

.tech-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 140px;
  font-size: 3.5rem;
  color: white;
  border-radius: 16px 16px 0 0;
  position: relative;
  overflow: hidden;
  transition: all 0.4s ease;
}

.tech-card:hover .tech-icon {
  transform: scale(1.1);
}

.tech-icon i {
  position: relative;
  z-index: 1;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
  transition: transform 0.4s ease;
}

.tech-card:hover .tech-icon i {
  transform: scale(1.2) rotate(5deg);
}

.tech-stats {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  justify-content: center;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-color-secondary);
  padding: 0.5rem 0;
}

.prof-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  justify-content: center;
  margin-top: 0.5rem;
}

.prof-tag {
  font-size: 0.7rem !important;
  padding: 0.15rem 0.4rem !important;
}
</style>
