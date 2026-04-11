<template>
  <div class="page-shell">
    <NavBar />

    <main class="container-lg home-page">
      <section class="hero-grid">
        <Card class="hero-card reveal-pop">
          <template #content>
            <div class="hero-layout">
              <div class="hero-copy">
                <div class="hero-badges">
                  <Tag value="AI-powered подготовка" severity="success" rounded class="hero-tag" />
                  <Tag value="PrimeVue Edition" severity="contrast" rounded />
                </div>

                <h1 class="h-page hero-title">
                  Готовься к <span>IT-собеседованиям</span>
                  системно и быстрее
                </h1>

                <p class="hero-sub">
                  Вопросы, тренажер SM-2, mock-интервью, анализ вакансий и обработка видео в едином
                  рабочем пространстве без переключения между разными сервисами.
                </p>

                <ul class="hero-points">
                  <li>Приоритизация тем по вероятности и рыночному спросу</li>
                  <li>Практика в формате интервью, а не просто чтение конспектов</li>
                  <li>Реальный цикл подготовки: изучил → закрепил → проверил</li>
                </ul>

                <div class="hero-actions">
                  <Button label="Начать подготовку" icon="pi pi-play" @click="router.push('/interview-questions')" />
                  <Button label="Тренажер SM-2" icon="pi pi-bolt" severity="secondary" outlined @click="router.push('/trainer')" />
                </div>

                <div class="hero-stats">
                  <div v-for="item in stats" :key="item.label" class="hero-stat-item">
                    <div class="hero-stat-value">{{ item.value }}</div>
                    <div class="hero-stat-label">{{ item.label }}</div>
                  </div>
                </div>
              </div>

              <div class="hero-visual media-glow">
                <img :src="heroVisual" alt="Схема подготовки к интервью" class="hero-art float-soft" />
                <div class="hero-visual-badge">AI pipeline • Q&A • SM-2</div>
              </div>
            </div>
          </template>
        </Card>

        <Card class="stats-card reveal-pop" style="--delay:120ms">
          <template #title>Динамика и пайплайн</template>
          <template #content>
            <p class="stats-sub">Топ-6 тем по количеству собранных вопросов</p>
            <Divider />
            <Chart type="bar" :data="chartData" :options="chartOptions" class="home-chart" />

            <div class="pipeline-mini">
              <div v-for="step in steps" :key="step.title" class="pipeline-item">
                <Tag :value="step.index" severity="secondary" rounded />
                <span>{{ step.title }}</span>
              </div>
            </div>

            <div class="proof-mini">
              <div class="proof-item">
                <span class="proof-k">SM-2</span>
                <span class="proof-v">алгоритм интервальных повторений</span>
              </div>
              <div class="proof-item">
                <span class="proof-k">AI</span>
                <span class="proof-v">извлечение вопросов и генерация ответов</span>
              </div>
            </div>
          </template>
        </Card>
      </section>

      <section class="tools-section">
        <div class="tools-head">
          <h2 class="section-title">Инструменты платформы</h2>
          <p class="p-muted">Ежедневная практика, контроль прогресса и приоритизация тем в одном интерфейсе.</p>
        </div>

        <div class="tools-grid">
          <Card v-for="item in features" :key="item.route" class="tool-card" @click="openFeature(item.route)">
            <template #title>
              <div class="tool-title">
                <i :class="item.icon" />
                <span>{{ item.title }}</span>
              </div>
            </template>
            <template #content>
              <p class="tool-desc">{{ item.description }}</p>
            </template>
            <template #footer>
              <Button label="Открыть" text icon="pi pi-arrow-right" iconPos="right" @click.stop="openFeature(item.route)" />
            </template>
          </Card>
        </div>
      </section>

      <section class="value-strip">
        <Card class="value-card">
          <template #content>
            <div class="value-grid">
              <div v-for="pillar in valuePillars" :key="pillar.title" class="value-item">
                <h3>{{ pillar.title }}</h3>
                <p>{{ pillar.text }}</p>
              </div>
            </div>
          </template>
        </Card>
      </section>

      <section class="flow-section">
        <Card class="flow-card">
          <template #title>Как это работает</template>
          <template #content>
            <div class="flow-grid">
              <div v-for="step in steps" :key="step.title" class="flow-step">
                <Tag :value="step.index" rounded />
                <h3>{{ step.title }}</h3>
                <p>{{ step.description }}</p>
              </div>
            </div>
          </template>
        </Card>
      </section>

      <section class="cta-section">
        <Card class="cta-card">
          <template #content>
            <div class="cta-content">
              <div>
                <h2>Готов начать подготовку?</h2>
                <p>Собери персональный ритм: вопросы, карточки и аналитика навыков в одном цикле.</p>
              </div>
              <div class="cta-actions">
                <Button label="К вопросам" icon="pi pi-compass" @click="router.push('/interview-questions')" />
                <Button label="Открыть записи" icon="pi pi-video" severity="secondary" outlined @click="router.push('/recordings')" />
              </div>
            </div>
          </template>
        </Card>
      </section>
    </main>

    <AppFooter />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Divider from 'primevue/divider'
import Chart from 'primevue/chart'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import { useQuestionsStore } from '../store'
import heroVisual from '../assets/media/hybrid/hero-interview.svg'

const store = useQuestionsStore()
const router = useRouter()

onMounted(() => {
  store.fetchQuestions()
})

const stats = computed(() => {
  const videos = new Set(
    store.questions
      .map((q) => q.video_url || q.youtube_url || q.source_url || q.video_id || q.processed_video_id)
      .filter(Boolean)
  ).size
  return [
    { label: 'Вопросов', value: store.questions.length || '0' },
    { label: 'Технологий', value: store.topics.length || '0' },
    { label: 'Видео', value: videos || '0' }
  ]
})

const chartData = computed(() => {
  const byTopic = {}
  for (const q of store.questions) {
    if (!q.topic) continue
    byTopic[q.topic] = (byTopic[q.topic] || 0) + 1
  }

  const top = Object.entries(byTopic)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)

  return {
    labels: top.map((entry) => entry[0]),
    datasets: [
      {
        label: 'Вопросы',
        data: top.map((entry) => entry[1]),
        borderRadius: 10,
        maxBarThickness: 30,
        backgroundColor: ['#20b28a', '#1aa4c0', '#5b8ef2', '#20b28a', '#1aa4c0', '#5b8ef2'],
        borderColor: 'rgba(255,255,255,.1)',
        borderWidth: 1
      }
    ]
  }
})

const chartOptions = {
  animation: {
    duration: 950,
    easing: 'easeOutQuart'
  },
  plugins: {
    legend: { display: false }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        precision: 0,
        color: '#8da8bc'
      },
      grid: {
        color: 'rgba(134, 171, 194, .2)'
      }
    },
    x: {
      ticks: {
        color: '#a5bdd0'
      },
      grid: {
        display: false
      }
    }
  },
  maintainAspectRatio: false
}

const features = [
  { route: '/interview-questions', icon: 'pi pi-question-circle', title: 'База вопросов', description: 'Фильтры по темам, сложности и вероятности вопроса.' },
  { route: '/trainer', icon: 'pi pi-bolt', title: 'Тренажер SM-2', description: 'Интервальные повторения и закрепление ответа.' },
  { route: '/ai-interview', icon: 'pi pi-comments', title: 'AI Interview', description: 'Практика формулировок в диалоге с AI-интервьюером.' },
  { route: '/test-assignments', icon: 'pi pi-briefcase', title: 'Тестовые задания', description: 'Коллекция задач от компаний для портфолио-практики.' },
  { route: '/recordings', icon: 'pi pi-video', title: 'Записи', description: 'Архив обработанных интервью с таймкодами и вопросами.' },
  { route: '/hh-requirements', icon: 'pi pi-chart-bar', title: 'Навыки вакансий', description: 'Аналитика востребованных навыков по рынку.' }
]

const steps = [
  { index: '01', title: 'Загрузка и транскрибация', description: 'Whisper извлекает текст и структуру разговора из видео.' },
  { index: '02', title: 'Извлечение вопросов', description: 'LLM выделяет релевантные вопросы и убирает дубликаты.' },
  { index: '03', title: 'Подготовка и тренировка', description: 'Ты учишься по базе и закрепляешь материал в тренажере.' }
]

const valuePillars = [
  { title: 'Скорость', text: 'Меньше времени на хаотичный поиск и больше времени на целенаправленную практику.' },
  { title: 'Структура', text: 'Единый рабочий процесс: база вопросов, тренировка, проверка результата.' },
  { title: 'Актуальность', text: 'Контент обновляется из свежих интервью и вакансий, а не из старых конспектов.' }
]

function openFeature(route) {
  router.push(route)
}
</script>

<style scoped>
.home-page {
  display: grid;
  gap: 1.25rem;
  padding-top: 1.15rem;
  padding-bottom: 2.4rem;
}

.hero-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

.hero-card {
  position: relative;
  overflow: hidden;
}

.hero-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 16% 4%, color-mix(in srgb, var(--p-primary-color, #10b981) 20%, transparent), transparent 38%),
    radial-gradient(circle at 96% 96%, color-mix(in srgb, #38bdf8 14%, transparent), transparent 40%);
  opacity: 0.9;
  pointer-events: none;
}

.hero-card :deep(.p-card-content) {
  position: relative;
  z-index: 1;
}

.hero-layout {
  display: grid;
  grid-template-columns: 1.1fr minmax(320px, .9fr);
  gap: 1rem;
  align-items: stretch;
}

.hero-copy {
  display: grid;
  gap: 1rem;
}

.hero-badges {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.hero-title {
  margin: 0;
  font-size: clamp(2rem, 3.4vw, 2.9rem);
  line-height: 1.12;
  letter-spacing: -0.02em;
}

.hero-title span {
  color: var(--p-primary-color, #10b981);
}

.hero-sub {
  margin: 0;
  color: var(--p-text-muted-color);
  max-width: 60ch;
  line-height: 1.68;
}

.hero-points {
  margin: 0;
  padding-left: 1.05rem;
  display: grid;
  gap: 0.3rem;
  color: var(--c-text-2);
  font-size: 0.92rem;
}

.hero-points li::marker {
  color: var(--c-brand-h);
}

.hero-actions {
  display: flex;
  gap: 0.7rem;
  flex-wrap: wrap;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.6rem;
}

.hero-visual {
  position: relative;
  min-height: 100%;
  border-radius: var(--r-lg);
  border: 1px solid color-mix(in srgb, var(--c-border-h) 80%, transparent);
  background:
    radial-gradient(circle at 20% 12%, color-mix(in srgb, var(--c-brand) 22%, transparent), transparent 36%),
    linear-gradient(145deg, color-mix(in srgb, var(--c-bg-2) 84%, transparent), color-mix(in srgb, var(--c-bg-1) 88%, transparent));
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 1rem;
}

.hero-art {
  width: min(100%, 540px);
  height: auto;
  filter: drop-shadow(0 22px 34px rgba(8, 20, 32, .5));
}

.hero-visual-badge {
  position: absolute;
  right: .8rem;
  bottom: .8rem;
  padding: .35rem .62rem;
  border-radius: var(--r-full);
  border: 1px solid color-mix(in srgb, var(--c-border-h) 72%, transparent);
  background: color-mix(in srgb, var(--c-bg-1) 70%, transparent);
  color: var(--c-text-2);
  font-size: .74rem;
  letter-spacing: .06em;
  text-transform: uppercase;
}

.hero-stat-item {
  border: 1px solid color-mix(in srgb, var(--p-content-border-color, #e2e8f0) 70%, transparent);
  border-radius: var(--app-radius-md);
  padding: 0.8rem;
  background: color-mix(in srgb, var(--p-primary-color, #10b981) 8%, transparent);
}

.hero-stat-value {
  font-family: var(--app-font-heading);
  font-size: 1.6rem;
  font-weight: 700;
}

.hero-stat-label {
  font-size: 0.82rem;
  color: var(--p-text-muted-color);
}

.stats-sub {
  margin: 0;
  color: var(--p-text-muted-color);
  font-size: 0.92rem;
}

.home-chart {
  height: 200px;
}

.pipeline-mini {
  margin-top: 0.8rem;
  display: grid;
  gap: 0.5rem;
}

.proof-mini {
  margin-top: .85rem;
  display: grid;
  gap: .45rem;
}

.proof-item {
  display: flex;
  align-items: center;
  gap: .55rem;
  padding: .45rem .6rem;
  border: 1px solid color-mix(in srgb, var(--c-border) 88%, transparent);
  border-radius: var(--r-md);
  background: color-mix(in srgb, var(--c-surface) 68%, transparent);
}

.proof-k {
  font-family: var(--app-font-heading);
  font-size: .88rem;
  color: var(--c-brand-h);
  min-width: 40px;
}

.proof-v {
  color: var(--c-text-3);
  font-size: .82rem;
}

.pipeline-item {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--p-text-color);
  font-size: 0.88rem;
}

.tools-section {
  display: grid;
  gap: 0.85rem;
}

.tools-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.8rem;
}

.tool-card {
  cursor: pointer;
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.tool-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 18px 34px -30px rgba(15, 23, 42, 0.8);
}

.tool-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
}

.tool-title i {
  color: var(--p-primary-color, #10b981);
}

.tool-desc {
  margin: 0;
  color: var(--p-text-muted-color);
  min-height: 3.4rem;
  line-height: 1.6;
}

.flow-card {
  overflow: hidden;
}

.value-strip {
  margin-top: -.2rem;
}

.value-card :deep(.p-card-content) {
  padding-top: .2rem;
}

.value-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: .75rem;
}

.value-item {
  border: 1px solid color-mix(in srgb, var(--c-border) 86%, transparent);
  border-radius: var(--r-md);
  padding: .9rem;
  background: color-mix(in srgb, var(--c-surface) 74%, transparent);
}

.value-item h3 {
  margin: 0 0 .3rem;
  font-size: .96rem;
}

.value-item p {
  margin: 0;
  color: var(--c-text-3);
  font-size: .88rem;
  line-height: 1.55;
}

.flow-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
}

.flow-step {
  border: 1px solid color-mix(in srgb, var(--p-content-border-color, #e2e8f0) 70%, transparent);
  border-radius: var(--app-radius-md);
  padding: 1rem;
  display: grid;
  gap: 0.45rem;
  background: color-mix(in srgb, var(--p-primary-color, #10b981) 5%, transparent);
}

.flow-step h3 {
  margin: 0;
  font-size: 1rem;
}

.flow-step p {
  margin: 0;
  color: var(--p-text-muted-color);
  font-size: 0.92rem;
}

.cta-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.cta-content h2 {
  margin: 0;
  font-size: clamp(1.25rem, 2.2vw, 1.8rem);
}

.cta-content p {
  margin: 0.35rem 0 0;
  color: var(--p-text-muted-color);
}

.cta-actions {
  display: flex;
  gap: 0.65rem;
  flex-wrap: wrap;
}

@media (max-width: 980px) {
  .hero-layout {
    grid-template-columns: 1fr;
  }

  .tools-grid,
  .flow-grid,
  .value-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 700px) {
  .tools-grid,
  .flow-grid,
  .value-grid {
    grid-template-columns: 1fr;
  }

  .hero-stats {
    grid-template-columns: 1fr;
  }

  .hero-title {
    font-size: clamp(1.75rem, 8vw, 2.25rem);
  }
}
</style>
