<template>
  <div class="page-shell">
    <NavBar />

    <main class="container-lg home-page">
      <section class="hero-grid">
        <Card class="hero-card reveal-pop">
          <template #content>
            <div class="hero-copy">
              <div class="hero-badges">
                <Tag value="Что дает платформа" severity="success" rounded class="hero-tag" />
                <Tag value="Практика + аналитика" severity="contrast" rounded />
              </div>

              <h1 class="h-page hero-title">
                Подготовка к <span>IT-собеседованиям</span>
                с понятным планом и приоритетами
              </h1>

              <p class="hero-sub">
                InterviewHub собирает вопросы из реальных интервью, показывает что спрашивают чаще,
                и превращает подготовку в управляемый цикл: изучил, закрепил, проверил результат.
              </p>

              <div class="hero-benefits">
                <article v-for="benefit in heroBenefits" :key="benefit.title" class="hero-benefit">
                  <h3>{{ benefit.title }}</h3>
                  <p>{{ benefit.text }}</p>
                </article>
              </div>

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

      <section class="value-strip">
        <Card class="value-card">
          <template #content>
            <div class="section-header centered">
              <h2 class="section-heading">Что ты получаешь от платформы</h2>
              <p class="section-lead">Сначала ценность и результат, затем детали реализации.</p>
            </div>
            <div class="value-grid">
              <div v-for="pillar in valuePillars" :key="pillar.title" class="value-item">
                <h3>{{ pillar.title }}</h3>
                <p>{{ pillar.text }}</p>
              </div>
            </div>
          </template>
        </Card>
      </section>

      <section class="tools-section">
        <div class="section-header centered">
          <h2 class="section-heading">Инструменты платформы</h2>
          <p class="section-lead">Ежедневная практика, контроль прогресса и приоритизация тем в одном интерфейсе.</p>
        </div>

        <div class="tools-grid">
          <div
            v-for="(item, i) in features"
            :key="item.route"
            class="blob-card"
            :class="`blob-card-${(i % 6) + 1}`"
            @click="openFeature(item.route)"
          >
            <i :class="item.icon" class="blob-icon" />
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </div>
        </div>
      </section>

      <section class="flow-section">
        <Card class="flow-card">
          <template #title>Как это работает</template>
          <template #content>
            <div class="flow-grid">
              <div v-for="step in steps" :key="step.title" class="flow-step">
                <div class="flow-top">
                  <Tag :value="step.index" rounded />
                  <div class="flow-visual">
                    <BrandIcon :name="step.icon" :size="22" />
                  </div>
                </div>
                <h3>{{ step.title }}</h3>
                <p>{{ step.description }}</p>
                <ul class="flow-details">
                  <li v-for="detail in step.details" :key="detail">{{ detail }}</li>
                </ul>
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
import BrandIcon from '../components/BrandIcon.vue'
import { useQuestionsStore } from '../store'

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

const heroBenefits = [
  {
    title: 'Фокус на приоритетах',
    text: 'Сначала вопросы с высокой частотой и рыночной значимостью, а не случайный список тем.'
  },
  {
    title: 'Тренировка в контексте интервью',
    text: 'SM-2, mock и AI-диалог помогают не просто читать ответы, а формулировать их уверенно.'
  },
  {
    title: 'Понимание реального спроса',
    text: 'HH-аналитика и тестовые задания показывают, какие навыки дают максимальный эффект при подготовке.'
  }
]

const steps = [
  {
    index: '01',
    icon: 'recordings',
    title: 'Загрузка и транскрибация',
    description: 'Whisper обрабатывает видео и формирует структурированный текст интервью.',
    details: ['Поддержка нескольких платформ и локальных файлов', 'Отслеживание прогресса обработки в реальном времени']
  },
  {
    index: '02',
    icon: 'questions',
    title: 'Извлечение и нормализация вопросов',
    description: 'LLM выделяет релевантные вопросы, а система дедупликации убирает повторы.',
    details: ['Семантическая очистка схожих формулировок', 'Сортировка по частоте и вероятности появления']
  },
  {
    index: '03',
    icon: 'trainer',
    title: 'Подготовка и проверка результата',
    description: 'База вопросов, тренажер и mock-сценарии превращают материал в навык ответа.',
    details: ['Интервальные повторения для долгого запоминания', 'Проверка понимания через практические сценарии']
  }
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
  gap: 5rem;
  padding-top: 3.5rem;
  padding-bottom: 5rem;
}

.hero-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.25rem;
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
  font-size: clamp(2rem, calc(2rem + 2 * ((100vw - 375px) / 1065)), 4rem);
  line-height: 1.05;
  letter-spacing: -0.03em;
  font-weight: 500;
  text-wrap: balance;
}

.hero-title span {
  color: var(--p-primary-color, #10b981);
}

.hero-sub {
  margin: 0;
  color: var(--p-text-muted-color);
  max-width: 72ch;
  font-size: 1.1rem;
  line-height: 1.65;
}

.hero-benefits {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: .55rem;
}

.hero-benefit {
  border: 1px solid color-mix(in srgb, var(--c-border) 82%, transparent);
  border-radius: var(--r-md);
  padding: .75rem .8rem;
  background: color-mix(in srgb, var(--c-surface) 72%, transparent);
}

.hero-benefit h3 {
  margin: 0 0 .25rem;
  font-size: .9rem;
}

.hero-benefit p {
  margin: 0;
  color: var(--c-text-3);
  font-size: .83rem;
  line-height: 1.54;
}

.hero-actions {
  display: flex;
  gap: 0.7rem;
  flex-wrap: wrap;
}

.hero-stats {
  display: flex;
  gap: 2.5rem;
  flex-wrap: wrap;
  padding-top: 1.5rem;
  border-top: 1px solid var(--c-border);
}

.hero-stat-item {
  display: flex;
  flex-direction: column;
  gap: .2rem;
}

.hero-stat-value {
  font-family: var(--app-font-heading);
  font-size: 2rem;
  font-weight: 600;
  letter-spacing: -0.03em;
  color: var(--c-text);
  line-height: 1;
}

.hero-stat-label {
  font-size: 0.82rem;
  color: var(--c-text-3);
  margin-top: .2rem;
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
  gap: 2.5rem;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.flow-card {
  overflow: hidden;
}

.flow-section :deep(.p-card-title) {
  font-size: clamp(1.3rem, 2.5vw, 1.9rem);
  letter-spacing: -.025em;
  font-weight: 500;
}

.value-strip {
  margin-top: 0;
}

.value-card :deep(.p-card-content) {
  padding-top: .2rem;
}

.value-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin-top: 2rem;
}

.value-item {
  border: 1px solid color-mix(in srgb, var(--c-border) 86%, transparent);
  border-radius: var(--r-lg);
  padding: 1.5rem;
  background: color-mix(in srgb, var(--c-surface) 74%, transparent);
}

.value-item h3 {
  margin: 0 0 .5rem;
  font-size: 1.05rem;
}

.value-item p {
  margin: 0;
  color: var(--c-text-3);
  font-size: .9rem;
  line-height: 1.6;
}

.flow-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin-top: .5rem;
}

.flow-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.flow-visual {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--c-border-h) 75%, transparent);
  background: color-mix(in srgb, var(--c-brand-bg) 58%, transparent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.flow-step {
  border: 1px solid color-mix(in srgb, var(--c-border) 80%, transparent);
  border-radius: var(--r-lg);
  padding: 1.4rem;
  display: grid;
  gap: 0.5rem;
  background: color-mix(in srgb, var(--c-surface) 70%, transparent);
}

.flow-step h3 {
  margin: 0;
  font-size: 1.05rem;
  letter-spacing: -.01em;
}

.flow-step p {
  margin: 0;
  color: var(--c-text-3);
  font-size: 0.9rem;
  line-height: 1.6;
}

.flow-details {
  margin: .1rem 0 0;
  padding-left: 1.05rem;
  display: grid;
  gap: .28rem;
  color: var(--c-text-3);
  font-size: .84rem;
  line-height: 1.5;
}

.cta-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.cta-content h2 {
  margin: 0;
  font-size: clamp(1.4rem, 2.5vw, 2rem);
  letter-spacing: -.025em;
  font-weight: 500;
}

.cta-content p {
  margin: 0.4rem 0 0;
  color: var(--c-text-3);
  line-height: 1.6;
}

.cta-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  flex-shrink: 0;
}

@media (max-width: 980px) {
  .hero-benefits {
    grid-template-columns: 1fr;
  }

  .tools-grid,
  .flow-grid,
  .value-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 700px) {
  .home-page {
    gap: 3rem;
    padding-top: 2rem;
    padding-bottom: 3rem;
  }

  .tools-grid,
  .flow-grid,
  .value-grid {
    grid-template-columns: 1fr;
  }

  .hero-stats {
    gap: 1.5rem;
  }

  .hero-title {
    font-size: clamp(1.75rem, 8vw, 2.25rem);
  }
}
</style>
