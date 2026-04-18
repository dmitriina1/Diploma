<template>
  <div class="page-shell">
    <NavBar />

    <main class="openai-home">
      <section class="section section-hero">
        <div class="openai-container max-w-container @container grid w-full">
          <div class="hero-wrap reveal-pop">
            <p class="hero-kicker">InterviewHub API Platform</p>
            <h1>Создавайте сильную подготовку к IT-собеседованиям на платформе InterviewHub</h1>
            <p class="hero-sub">
              Платформа извлекает вопросы из видео интервью, структурирует их в единую базу,
              а затем помогает закреплять ответы через SM-2, mock и AI-практику.
            </p>
            <div class="hero-actions">
              <Button label="Начать подготовку" @click="router.push('/interview-questions')" />
              <Button label="Открыть тренажер" outlined @click="router.push('/trainer')" />
            </div>
          </div>
        </div>
      </section>

      <section class="section section-logos">
        <div class="openai-container max-w-container @container grid w-full">
          <p class="logos-label">Используется для подготовки по направлениям</p>
          <div class="logos-grid">
            <span v-for="item in professionsLine" :key="item">{{ item }}</span>
          </div>
        </div>
      </section>

      <section class="section section-models">
        <div class="openai-container max-w-container @container grid w-full">
          <div class="section-head">
            <h2>Работает на практических модулях платформы</h2>
          </div>

          <div class="cards-shell" role="list">
            <article
              v-for="card in modelCards"
              :key="card.title"
              class="model-card"
              role="listitem"
              tabindex="0"
              @click="openFeature(card.route)"
              @keydown.enter.prevent="openFeature(card.route)"
            >
              <img :src="card.image" :alt="card.title" class="model-image" />
              <div class="model-overlay">
                <h3>{{ card.title }}</h3>
                <ul>
                  <li v-for="point in card.points" :key="point">{{ point }}</li>
                </ul>
                <button class="model-link" type="button" @click.stop="openFeature(card.route)">Подробнее</button>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section class="section section-grid">
        <div class="openai-container grid-wrap max-w-container @container grid w-full">
          <div class="grid-copy">
            <h2>Универсальная платформа для подготовки</h2>
            <p>
              Выстраивайте цикл обучения: сначала сбор и фильтрация вопросов,
              затем практика ответов, после этого проверка навыков через mock и аналитику рынка.
            </p>
          </div>

          <div class="media-grid col-span-12 grid w-full grid-cols-1 items-stretch gap-lg @md:gap-xl">
            <article class="media-card">
              <img src="../assets/media/hybrid/questions-banner.svg" alt="Каталог вопросов" />
              <h3>Собирайте</h3>
              <p>Автосбор вопросов из интервью с дедупликацией и тегами.</p>
            </article>
            <article class="media-card">
              <img src="../assets/media/hybrid/trainer-grid.svg" alt="Тренажер" />
              <h3>Тренируйте</h3>
              <p>SM-2 интервальные повторения и практика формулировки ответов.</p>
            </article>
            <article class="media-card">
              <img src="../assets/media/hybrid/skills-orbit.svg" alt="Навыки" />
              <h3>Оптимизируйте</h3>
              <p>Приоритизируйте подготовку по статистике навыков HH.ru.</p>
            </article>
          </div>
        </div>
      </section>

      <section class="section section-video">
        <div class="openai-container max-w-container @container grid w-full">
          <div class="section-head">
            <h2>Видеоконтент, который превращается в структуру</h2>
            <p>Загрузка видео, транскрибация и извлечение вопросов в одном пайплайне</p>
          </div>

          <div class="video-grid col-span-12 grid w-full grid-cols-1 items-stretch gap-lg @md:gap-xl">
            <article class="video-card big">
              <img src="../assets/media/hybrid/hero-interview.svg" alt="Видео интервью" />
              <div>
                <h3>Pipeline обработки видео</h3>
                <p>Поддержка YouTube, VK, Rutube и локальных файлов, прогресс в real-time.</p>
              </div>
            </article>

            <article class="video-card">
              <h3>Whisper + LLM</h3>
              <p>Транскрибация речи и извлечение релевантных вопросов с нормализацией.</p>
              <Button label="Открыть записи" outlined @click="router.push('/recordings')" />
            </article>

            <article class="video-card">
              <h3>Семантический поиск</h3>
              <p>FAISS и эмбеддинги помогают находить похожие вопросы по смыслу.</p>
              <Button label="Перейти к вопросам" outlined @click="router.push('/interview-questions')" />
            </article>
          </div>
        </div>
      </section>

      <section class="section section-usecases">
        <div class="openai-container max-w-container @container grid w-full">
          <div class="section-head">
            <h2>Сценарии использования платформы</h2>
          </div>
          <div class="usecases-grid">
            <article v-for="item in features" :key="item.title" class="usecase-card" @click="openFeature(item.route)">
              <i :class="item.icon" />
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </article>
          </div>
        </div>
      </section>

      <section class="section section-cta">
        <div class="openai-container cta-inner max-w-container @container grid w-full">
          <h2>Начать подготовку</h2>
          <p>Соберите собственный план: вопросы, тренажер, mock, навыки и тестовые задания.</p>
          <div class="hero-actions">
            <Button label="К вопросам" @click="router.push('/interview-questions')" />
            <Button label="Навыки вакансий" outlined @click="router.push('/hh-requirements')" />
          </div>
        </div>
      </section>
    </main>

    <AppFooter />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import { useQuestionsStore } from '../store'

import modelA from '../assets/media/hybrid/questions-banner.svg'
import modelB from '../assets/media/hybrid/trainer-grid.svg'
import modelC from '../assets/media/hybrid/skills-orbit.svg'

const store = useQuestionsStore()
const router = useRouter()

onMounted(() => {
  store.fetchQuestions()
})

const professionsLine = computed(() => {
  const source = store.professions?.map((item) => item.title).filter(Boolean) || []
  if (source.length) return source.slice(0, 14)
  return ['Backend', 'Frontend', 'DevOps', 'Data Scientist', 'QA', 'Android', 'iOS', 'System Design']
})

const modelCards = [
  {
    title: 'Каталог вопросов',
    route: '/interview-questions',
    image: modelA,
    points: ['Фильтры по теме и уровню', 'Вероятность и частота', 'Похожие вопросы'],
  },
  {
    title: 'SM-2 тренажер',
    route: '/trainer',
    image: modelB,
    points: ['Интервальные повторения', 'Карточки вопрос/ответ', 'Прогресс по сессии'],
  },
  {
    title: 'Навыки вакансий',
    route: '/hh-requirements',
    image: modelC,
    points: ['Статистика HH.ru', 'Must-have навыки', 'Фокус на рынке'],
  },
]

const features = [
  { route: '/interview-questions', icon: 'pi pi-question-circle', title: 'База вопросов', description: 'Быстрый доступ к частым вопросам по профессиям и темам.' },
  { route: '/trainer', icon: 'pi pi-bolt', title: 'Тренажер', description: 'Закрепление знаний по алгоритму интервальных повторений.' },
  { route: '/ai-interview', icon: 'pi pi-comments', title: 'AI Interview', description: 'Диалоговый режим для тренировки уверенных формулировок.' },
  { route: '/mock-interview', icon: 'pi pi-stopwatch', title: 'Mock интервью', description: 'Проверка навыка ответа в формате реального собеседования.' },
  { route: '/test-assignments', icon: 'pi pi-briefcase', title: 'Тестовые задания', description: 'Практические задания от технологических компаний.' },
  { route: '/recordings', icon: 'pi pi-video', title: 'Записи интервью', description: 'Видео-источники, таймкоды и извлеченные вопросы.' },
]

function openFeature(route) {
  router.push(route)
}
</script>

<style scoped>
.openai-home {
  display: grid;
  gap: 0;
}

.openai-container {
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
  padding: 0 1.5rem;
}

.section {
  padding: 2.35rem 0;
}

.section-hero {
  padding-top: 2.9rem;
  padding-bottom: 1.8rem;
}

.hero-wrap {
  display: grid;
  gap: 1.05rem;
}

.hero-kicker {
  font-family: var(--app-font-mono);
  font-size: 0.8rem;
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}

.hero-wrap h1 {
  margin: 0;
  max-width: 16ch;
  font-family: var(--app-font-heading);
  font-size: clamp(2.4rem, 5vw, 4.2rem);
  line-height: 1.01;
  letter-spacing: -0.034em;
}

.hero-sub {
  margin: 0;
  max-width: 64ch;
  color: var(--text-secondary);
  font-size: 1.03rem;
  line-height: 1.66;
}

.hero-actions {
  display: flex;
  gap: 0.7rem;
  flex-wrap: wrap;
}

.section-logos {
  padding-top: 1rem;
  padding-bottom: 2.2rem;
}

.logos-label {
  margin: 0 0 0.55rem;
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.logos-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.logos-grid span {
  padding: 0.32rem 0.62rem;
  border-radius: 999px;
  border: 1px solid var(--surface-border);
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.section-head {
  margin-bottom: 1.15rem;
}

.section-head h2 {
  margin: 0;
  max-width: 20ch;
  font-size: clamp(1.52rem, 2.25vw, 2.06rem);
  line-height: 1.12;
  letter-spacing: -0.02em;
}

.section-head p {
  margin: 0.35rem 0 0;
  color: var(--text-secondary);
}

.cards-shell {
  display: flex;
  gap: .9rem;
  overflow-x: auto;
  padding-bottom: 0.25rem;
  scroll-snap-type: x mandatory;
}

.model-card {
  transition: transform var(--dur-250) var(--ease-curve-a), box-shadow var(--dur-250) var(--ease-curve-a), border-color var(--dur-250) ease;
  color: #101010;
  position: relative;
  display: flex;
  min-width: 286px;
  flex: 1;
  cursor: pointer;
  scroll-snap-align: start;
  align-items: flex-end;
  overflow: hidden;
  border-radius: 8px;
  background: #8ad1fd;
  aspect-ratio: 4 / 5;
  border: 1px solid rgba(12, 24, 42, 0.12);
}

.model-card:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--c-brand) 48%, white);
  outline-offset: 2px;
}

.model-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 18px 36px -28px rgba(10, 22, 38, .44);
}

.model-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--dur-400) var(--ease-curve-b);
}

.model-card:hover .model-image {
  transform: scale(1.045);
}

.model-overlay {
  position: relative;
  z-index: 1;
  width: 100%;
  padding: .92rem;
  background: linear-gradient(to top, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.82) 62%, rgba(255, 255, 255, 0) 100%);
}

.model-overlay h3 {
  margin: 0 0 0.35rem;
  font-size: 1.02rem;
}

.model-overlay ul {
  margin: 0;
  padding-left: 1rem;
  display: grid;
  gap: 0.15rem;
  font-size: 0.8rem;
  line-height: 1.45;
}

.model-link {
  margin-top: 0.6rem;
  padding: 0;
  border: 0;
  background: transparent;
  font-size: 0.84rem;
  font-weight: 600;
  color: #1f8a70;
}

.grid-wrap {
  display: grid;
  gap: 1.15rem;
}

.grid-copy p {
  margin: 0.35rem 0 0;
  max-width: 72ch;
  color: var(--text-secondary);
}

.media-grid,
.video-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

.media-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.media-card,
.video-card {
  border: 1px solid var(--surface-border);
  border-radius: 10px;
  padding: .88rem;
  background: color-mix(in srgb, var(--surface-bg) 92%, transparent);
  transition: transform var(--dur-250) var(--ease-curve-a), background var(--dur-250) ease, border-color var(--dur-250) ease;
}

.media-card:hover,
.video-card:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--c-border-h) 85%, transparent);
  background: color-mix(in srgb, var(--surface-soft) 82%, transparent);
}

.media-card img,
.video-card img {
  width: 100%;
  border-radius: 9px;
  margin-bottom: 0.55rem;
  background: color-mix(in srgb, var(--surface-soft) 82%, transparent);
}

.media-card h3,
.video-card h3 {
  margin: 0 0 0.28rem;
  font-size: 1rem;
}

.media-card p,
.video-card p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.55;
}

.video-grid {
  grid-template-columns: 1.2fr .8fr .8fr;
}

.video-card.big {
  display: grid;
  gap: 0.55rem;
}

.video-card {
  display: grid;
  align-content: start;
  gap: 0.6rem;
}

.usecases-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
}

.usecase-card {
  border: 1px solid var(--surface-border);
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface-bg) 92%, transparent);
  padding: 0.88rem;
  cursor: pointer;
  transition: transform var(--dur-250) var(--ease-curve-a), background var(--dur-250) ease, border-color var(--dur-250) ease;
}

.usecase-card:hover {
  background: var(--surface-soft);
  transform: translateY(-3px);
  border-color: color-mix(in srgb, var(--c-border-h) 85%, transparent);
}

.usecase-card i {
  color: var(--brand-color);
}

.usecase-card h3 {
  margin: 0.35rem 0 0.25rem;
  font-size: 0.98rem;
}

.usecase-card p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.88rem;
  line-height: 1.55;
}

.section-cta {
  padding-bottom: 2.9rem;
}

.cta-inner {
  border: 1px solid var(--surface-border);
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface-bg) 94%, transparent);
  padding: 1.2rem;
}

.cta-inner h2 {
  margin: 0;
}

.cta-inner p {
  margin: 0.35rem 0 0.75rem;
  color: var(--text-secondary);
}

@media (max-width: 1080px) {
  .media-grid,
  .video-grid,
  .usecases-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 760px) {
  .openai-container {
    padding: 0 1rem;
  }

  .section {
    padding: 1.5rem 0;
  }

  .hero-wrap h1 {
    max-width: 100%;
    font-size: clamp(1.95rem, 9vw, 2.75rem);
  }

  .media-grid,
  .video-grid,
  .usecases-grid {
    grid-template-columns: 1fr;
  }
}
</style>
