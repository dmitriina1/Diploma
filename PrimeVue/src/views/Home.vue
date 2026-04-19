<template>
  <div class="page-shell">
    <NavBar />

    <main class="openai-home">
      <section class="section section-hero">
        <div class="openai-container max-w-container @container grid w-full">
          <div class="hero-wrap reveal-pop">
            <h1>Готовьтесь к IT-собеседованиям структурно и без хаоса</h1>
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
          <div class="ticker-shell" role="presentation" aria-hidden="true">
            <div class="ticker-track">
              <span v-for="(item, idx) in professionsTicker" :key="`${item}-${idx}`">{{ item }}</span>
            </div>
          </div>
        </div>
      </section>

      <section class="section section-proof">
        <div class="openai-container max-w-container @container grid w-full">
          <div class="t396__filter">
            <div class="section-head centered">
              <h2>Почему InterviewHub ускоряет подготовку</h2>
              <p>Не просто список вопросов, а система, которая доводит до уверенного ответа на собеседовании.</p>
            </div>
            <div class="proof-grid">
              <article
                v-for="(item, idx) in platformProof"
                :key="item.title"
                class="proof-card"
                :class="{ 'proof-card-main': idx === 0 }"
              >
                <h3>{{ item.title }}</h3>
                <p>{{ item.description }}</p>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section class="section section-video">
        <div class="openai-container max-w-container @container grid w-full">
          <div class="video-shell t396__filter">
            <div class="video-split">
              <div class="video-visual">
                <img src="../assets/media/hybrid/questions-banner.svg" alt="Пайплайн извлечения вопросов из видео" />
              </div>
              <article class="video-story">
                <h2>Видеоконтент, который превращается в базу знаний</h2>
                <p>Пайплайн сохраняет только полезные вопросы и превращает разрозненные интервью в структурируемую практику.</p>
                <ul class="video-points">
                  <li v-for="step in videoPipeline" :key="step.title">
                    <strong>{{ step.title }}</strong>
                    <span>{{ step.description }}</span>
                  </li>
                </ul>
                <div class="hero-actions">
                  <Button label="Открыть записи" @click="router.push('/recordings')" />
                  <Button label="Перейти к вопросам" outlined @click="router.push('/interview-questions')" />
                </div>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section class="section section-chat-shot">
        <div class="openai-container max-w-container @container grid w-full">
          <div class="chat-shell">
            <div class="chat-shot">
              <img src="../assets/media/hybrid/hero-interview.svg" alt="Прохождение интервью в InterviewHub" />
            </div>
            <article class="chat-copy">
              <p class="mini-kicker">Практика с обратной связью</p>
              <h2>Скрин прохождения собеседования в платформе</h2>
              <p>
                Пользователь проходит mock/AI-интервью, получает разбор и тут же уходит в повторение слабых мест по SM-2.
                Такой цикл сокращает время между «прочитал вопрос» и «уверенно ответил».
              </p>
              <div class="hero-actions">
                <Button label="Попробовать AI Interview" @click="router.push('/ai-interview')" />
                <Button label="Открыть mock-интервью" outlined @click="router.push('/mock-interview')" />
              </div>
            </article>
          </div>
        </div>
      </section>

      <section class="section section-usecases">
        <div class="openai-container max-w-container @container grid w-full">
          <div class="section-head centered">
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

      <section class="section section-enterprise">
        <div class="openai-container max-w-container @container grid w-full">
          <div class="section-head centered">
            <h2>Функции платформы для масштабной подготовки</h2>
            <p>Подходит как для индивидуальной подготовки, так и для внутренних учебных треков команды.</p>
          </div>
          <div class="enterprise-grid">
            <article v-for="item in enterpriseHighlights" :key="item.title" class="enterprise-card">
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </article>
          </div>
        </div>
      </section>

      <section class="section section-faq">
        <div class="openai-container max-w-container @container grid w-full">
          <div class="section-head centered">
            <h2>Часто задаваемые вопросы</h2>
          </div>
          <div class="faq-grid">
            <details v-for="item in faqItems" :key="item.q" class="faq-item">
              <summary>{{ item.q }}</summary>
              <p>{{ item.a }}</p>
            </details>
          </div>
        </div>
      </section>

      <section class="section section-cta">
        <div class="openai-container cta-inner max-w-container @container grid w-full">
          <h2>Попробовать InterviewHub сейчас</h2>
          <p>Стартуйте с вопросов, закрепляйте ответы в тренажёре и проверяйте себя в mock/AI-сессиях.</p>
          <div class="hero-actions">
            <Button label="Начать с вопросов" @click="router.push('/interview-questions')" />
            <Button label="Перейти к mock" outlined @click="router.push('/mock-interview')" />
          </div>
          <p class="cta-note">Загрузка видео остаётся админ-функцией. Для пользователей доступна полная учебная траектория.</p>
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

const store = useQuestionsStore()
const router = useRouter()

onMounted(() => {
  store.fetchQuestions()
})

const fallbackDirections = [
  'Backend', 'Frontend', 'Fullstack', 'DevOps', 'QA', 'Data Scientist', 'Data Analyst',
  'ML Engineer', 'Android', 'iOS', 'System Design', 'SRE', 'Security', 'Product', 'Team Lead', 'Cloud'
]

const professionsLine = computed(() => {
  const source = store.professions?.map((item) => item.title).filter(Boolean) || []
  const merged = [...new Set([...fallbackDirections, ...source])]
  return merged
})

const professionsTicker = computed(() => [...professionsLine.value, ...professionsLine.value])

const platformProof = [
  {
    title: 'Единая база без ручного хаоса',
    description: 'Вопросы из интервью автоматически структурируются по теме, сложности и вероятности. Вы тратите время на подготовку, а не на сортировку заметок.',
  },
  {
    title: 'Практика, а не пассивное чтение',
    description: 'SM-2, mock и AI-сессии строят регулярный цикл тренировок, где каждый ответ проверяется и закрепляется в нужный момент.',
  },
  {
    title: 'Фокус на рынке и приоритетах',
    description: 'Навыки из вакансий помогают выбирать, что учить в первую очередь, чтобы быстрее закрывать реальные требования работодателей.',
  },
]

const videoPipeline = [
  {
    title: '1. Загрузка и транскрибация',
    description: 'Видео проходит через пайплайн, где речь преобразуется в текст с таймкодами.',
  },
  {
    title: '2. Извлечение вопросов',
    description: 'LLM выделяет именно вопросы интервью, отбрасывая шум и нецелевой контент.',
  },
  {
    title: '3. Нормализация и дедупликация',
    description: 'Схожие вопросы объединяются, чтобы база оставалась чистой и полезной для практики.',
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

const enterpriseHighlights = [
  {
    title: 'Контроль качества контента',
    description: 'Модерация, похожие вопросы и объединение дублей поддерживают стабильное качество базы.',
  },
  {
    title: 'Сквозная аналитика прогресса',
    description: 'От первого вопроса до mock-сессии: видно, где пользователь теряет темп и что усиливать дальше.',
  },
  {
    title: 'Готовность к масштабированию',
    description: 'Платформа рассчитана на рост контента и пользователей без деградации пользовательского опыта.',
  },
]

const faqItems = [
  {
    q: 'С чего начать подготовку в InterviewHub?',
    a: 'Начните с базы вопросов по вашей роли, отметьте слабые темы и сразу закрепите их через тренажер.',
  },
  {
    q: 'Зачем нужен режим mock и AI Interview?',
    a: 'Он переводит знания в навык устного ответа: вы тренируете структуру, скорость и уверенность формулировок.',
  },
  {
    q: 'Кому доступна загрузка видео?',
    a: 'Загрузка видео доступна администраторам. Пользователь работает с готовой базой и инструментами практики.',
  },
  {
    q: 'Как часто обновляются навыки из вакансий?',
    a: 'Данные синхронизируются регулярно, чтобы вы видели актуальные приоритеты рынка в своей профессии.',
  },
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
  justify-items: center;
  text-align: center;
}

.hero-wrap h1 {
  margin: 0;
  max-width: 18ch;
  font-family: var(--app-font-heading);
  font-size: clamp(2rem, 4.25vw, 3.45rem);
  line-height: 1.01;
  letter-spacing: -0.034em;
}

.hero-sub {
  margin: 0;
  max-width: 70ch;
  color: var(--text-secondary);
  font-size: 1.03rem;
  line-height: 1.66;
}

.hero-actions {
  display: flex;
  gap: 0.7rem;
  flex-wrap: wrap;
  justify-content: center;
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

.ticker-shell {
  position: relative;
  overflow: hidden;
  border-radius: 999px;
  border: 1px solid var(--surface-border);
  background: color-mix(in srgb, var(--surface-bg) 88%, transparent);
  mask-image: linear-gradient(to right, transparent 0%, black 8%, black 92%, transparent 100%);
}

.ticker-track {
  display: flex;
  align-items: center;
  width: max-content;
  gap: .45rem;
  padding: .5rem .6rem;
  animation: tickerMove 28s linear infinite;
}

.ticker-track span {
  padding: 0.28rem 0.58rem;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--surface-border) 92%, transparent);
  background: color-mix(in srgb, var(--surface-soft) 70%, transparent);
  font-size: 0.79rem;
  color: var(--text-secondary);
  white-space: nowrap;
}

@keyframes tickerMove {
  from { transform: translateX(0); }
  to { transform: translateX(-50%); }
}

.section-head {
  margin-bottom: 1.15rem;
}

.section-head.centered {
  text-align: center;
  justify-items: center;
}

.section-head.centered h2,
.section-head.centered p {
  max-width: 62ch;
  margin-inline: auto;
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

.t396__filter {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  border: 1px solid color-mix(in srgb, var(--surface-border) 88%, transparent);
  padding: 1.25rem;
  background:
    radial-gradient(92% 120% at 12% 0%, color-mix(in srgb, var(--c-brand) 18%, transparent) 0%, transparent 58%),
    radial-gradient(90% 120% at 100% 100%, color-mix(in srgb, var(--c-accent) 14%, transparent) 0%, transparent 62%),
    color-mix(in srgb, var(--surface-bg) 92%, transparent);
}

.proof-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.22fr) minmax(0, 1fr);
  grid-template-rows: repeat(2, minmax(0, 1fr));
  gap: .85rem;
}

.proof-card,
.video-card {
  border: 1px solid var(--surface-border);
  border-radius: 12px;
  padding: 1rem;
  background: color-mix(in srgb, var(--surface-bg) 94%, transparent);
  transition: transform var(--dur-250) var(--ease-curve-a), background var(--dur-250) ease, border-color var(--dur-250) ease;
}

.proof-card:hover,
.video-card:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--c-border-h) 85%, transparent);
  background: color-mix(in srgb, var(--surface-soft) 82%, transparent);
}

.proof-card h3,
.video-card h3 {
  margin: 0 0 0.35rem;
  font-size: 1rem;
}

.proof-card p,
.video-card p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.55;
}

.proof-card-main {
  grid-row: 1 / span 2;
  padding: 1.15rem;
}

.proof-card-main h3 {
  font-size: 1.16rem;
}

.proof-card-main p {
  font-size: .95rem;
}

.video-shell {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--surface-border) 92%, transparent);
  padding: 1.2rem;
  background: color-mix(in srgb, var(--surface-bg) 90%, transparent);
}

.video-split {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr);
  gap: 1rem;
  align-items: center;
}

.video-visual {
  border: 1px solid var(--surface-border);
  border-radius: 14px;
  overflow: hidden;
  background: color-mix(in srgb, var(--surface-bg) 94%, transparent);
}

.video-visual img {
  display: block;
  width: 100%;
  height: auto;
}

.video-story {
  border: 1px solid var(--surface-border);
  border-radius: 14px;
  background: color-mix(in srgb, var(--surface-bg) 93%, transparent);
  padding: 1rem;
  display: grid;
  gap: .65rem;
}

.video-story h2 {
  margin: 0;
  font-size: clamp(1.38rem, 2.15vw, 1.9rem);
  line-height: 1.12;
}

.video-story p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.62;
}

.video-points {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: .45rem;
}

.video-points li {
  display: grid;
  gap: .15rem;
  padding: .45rem .55rem;
  border-radius: 10px;
  border: 1px solid var(--surface-border);
  background: color-mix(in srgb, var(--surface-soft) 72%, transparent);
}

.video-points strong {
  font-size: .9rem;
}

.video-points span {
  font-size: .88rem;
  color: var(--text-secondary);
}

.section-chat-shot {
  padding-top: 1rem;
}

.chat-shell {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr);
  align-items: center;
  gap: 1rem;
}

.chat-copy {
  display: grid;
  gap: 0.6rem;
}

.mini-kicker {
  margin: 0;
  color: var(--text-secondary);
  font-size: .78rem;
  letter-spacing: .04em;
  text-transform: uppercase;
  font-weight: 700;
}

.chat-copy h2 {
  margin: 0;
  font-size: clamp(1.46rem, 2.35vw, 2rem);
  line-height: 1.1;
}

.chat-copy p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.64;
}

.video-story .hero-actions,
.chat-copy .hero-actions {
  justify-content: flex-start;
}

.chat-shot {
  border: 1px solid var(--surface-border);
  border-radius: 16px;
  overflow: hidden;
  background: color-mix(in srgb, var(--surface-bg) 94%, transparent);
}

.chat-shot img {
  display: block;
  width: 100%;
  height: auto;
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

.enterprise-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: .75rem;
}

.enterprise-card {
  border: 1px solid var(--surface-border);
  border-radius: 12px;
  padding: .95rem;
  background: color-mix(in srgb, var(--surface-bg) 93%, transparent);
}

.enterprise-card h3 {
  margin: 0 0 .35rem;
  font-size: 1rem;
}

.enterprise-card p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.58;
  font-size: .9rem;
}

.faq-grid {
  display: grid;
  gap: .65rem;
}

.faq-item {
  border: 1px solid var(--surface-border);
  border-radius: 10px;
  padding: .65rem .75rem;
  background: color-mix(in srgb, var(--surface-bg) 93%, transparent);
}

.faq-item summary {
  cursor: pointer;
  font-weight: 600;
  font-size: .95rem;
}

.faq-item p {
  margin: .55rem 0 0;
  color: var(--text-secondary);
  line-height: 1.58;
}

.section-cta {
  padding-bottom: 2.9rem;
}

.cta-inner {
  border: 1px solid var(--surface-border);
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface-bg) 94%, transparent);
  padding: 1.2rem;
  text-align: center;
}

.cta-inner h2 {
  margin: 0;
}

.cta-inner p {
  margin: 0.35rem 0 0.75rem;
  color: var(--text-secondary);
}

.cta-note {
  margin-top: .5rem;
  font-size: .84rem;
  color: var(--text-secondary);
}

@media (max-width: 1080px) {
  .proof-grid,
  .enterprise-grid,
  .usecases-grid {
    grid-template-columns: 1fr 1fr;
  }

  .proof-card-main {
    grid-row: auto;
  }

  .video-split {
    grid-template-columns: 1fr;
  }

  .chat-shell {
    grid-template-columns: 1fr;
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

  .proof-grid,
  .enterprise-grid,
  .usecases-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }

  .ticker-track {
    animation-duration: 20s;
  }

  .video-shell,
  .t396__filter {
    padding: .8rem;
  }
}
</style>
