<template>
  <div class="page">
    <NavBar />

    <!-- Hero -->
    <section class="hero">
      <div class="hero-bg"></div>
      <div class="hero-content container-lg">
        <div class="hero-grid">
          <div class="hero-main">
            <span class="hero-badge badge badge-brand">Практика по реальным интервью</span>
            <h1 class="hero-title">Готовься к <span class="highlight">IT-собеседованиям</span> системно</h1>
            <p class="hero-sub">Вопросы из записей собеседований, тренажер повторений SM-2, задания от компаний и аналитика требований рынка в одном месте.</p>
            <div class="hero-actions">
              <router-link to="/interview-questions" class="btn btn-primary btn-lg">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                </svg>
                Перейти к вопросам
              </router-link>
              <router-link to="/trainer" class="btn btn-secondary btn-lg">Открыть тренажер</router-link>
            </div>
            <div class="hero-stats">
              <div class="hs" v-for="s in stats" :key="s.label">
                <span class="hs-val">{{ s.value }}</span>
                <span class="hs-label">{{ s.label }}</span>
              </div>
            </div>
          </div>

          <aside class="hero-panel card">
            <h3>Фокус на 2 недели</h3>
            <ul class="focus-list">
              <li v-for="item in focusPlan" :key="item.day">
                <span class="fp-day">{{ item.day }}</span>
                <div class="fp-body">
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.desc }}</p>
                </div>
              </li>
            </ul>
            <router-link to="/trainer" class="btn btn-secondary btn-sm hero-panel-link">Запустить план</router-link>
          </aside>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="how-it-works container-lg">
      <h2 class="section-title">Как это работает</h2>
      <div class="steps-grid">
        <div class="step-card card" v-for="(step, i) in steps" :key="i">
          <div class="step-number">{{ i + 1 }}</div>
          <div class="step-icon"><BrandIcon :name="step.icon" :size="50" /></div>
          <h3>{{ step.title }}</h3>
          <p>{{ step.desc }}</p>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="features container-lg">
      <h2 class="section-title">Все инструменты в одном месте</h2>
      <div class="features-grid">
        <router-link v-for="f in features" :key="f.to" :to="f.to" class="f-card card card-hover">
          <div class="f-icon"><BrandIcon :name="f.icon" :size="44" /></div>
          <div class="f-body">
            <h3>{{ f.title }}</h3>
            <p>{{ f.desc }}</p>
          </div>
          <svg class="f-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </router-link>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta container">
      <div class="cta-card card">
        <h2>Готов начать подготовку?</h2>
        <p>Присоединяйся к тысячам разработчиков, которые готовятся к собеседованиям с InterviewHub</p>
        <div class="cta-actions">
          <router-link to="/interview-questions" class="btn btn-primary btn-lg">Перейти к вопросам</router-link>
          <router-link to="/recordings" class="btn btn-ghost btn-lg">Обработать видео</router-link>
        </div>
      </div>
    </section>

    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuestionsStore } from '../store'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import BrandIcon from '../components/BrandIcon.vue'

const store = useQuestionsStore()

onMounted(() => store.fetchQuestions())

const stats = computed(() => [
  { value: store.questions.length || '—', label: 'Вопросов' },
  { value: store.topics.length || '—', label: 'Технологий' },
  { value: new Set(store.questions.map(q => q.video_url)).size || '—', label: 'Видео' },
])

const steps = [
  { icon: 'recordings', title: 'Загрузка видео', desc: 'Система обрабатывает записи с YouTube, VK, Rutube и других платформ' },
  { icon: 'mock', title: 'AI-анализ', desc: 'Whisper транскрибирует речь, LLM извлекает вопросы, FAISS убирает дубликаты' },
  { icon: 'questions', title: 'База вопросов', desc: 'Контент структурируется по темам, сложности и вероятности встречи' },
  { icon: 'trainer', title: 'Подготовка', desc: 'Используйте тренажер SM-2, mock-режим и HH-аналитику' },
]

const features = [
  { icon: 'questions', title: 'Вопросы с собеседований', desc: 'Каталог вопросов с фильтрами по технологии, сложности и релевантности', to: '/interview-questions' },
  { icon: 'flashcards', title: 'Тренажер SM-2', desc: 'Интервальное повторение и личная очередь на повтор', to: '/trainer' },
  { icon: 'interview', title: 'AI Interview', desc: 'Симуляция интервью с диалогом и итоговым фидбеком', to: '/ai-interview' },
  { icon: 'recordings', title: 'Записи собеседований', desc: 'Источники видео с привязкой извлеченных вопросов', to: '/recordings' },
  { icon: 'assignments', title: 'Тестовые задания', desc: 'Задания от Яндекс, СБЕР, VK, Т-Банк и других компаний', to: '/test-assignments' },
  { icon: 'skills', title: 'Навыки из вакансий', desc: 'Требования работодателей по данным HH.ru', to: '/hh-requirements' },
  { icon: 'suggest', title: 'Предложить видео', desc: 'Добавьте полезную запись для обработки и пополнения базы', to: '/suggest' },
]

const focusPlan = [
  { day: 'День 1-3', title: 'База вопросов', desc: 'Разбор тем и формирование списка слабых мест' },
  { day: 'День 4-7', title: 'Тренажер SM-2', desc: 'Ежедневные короткие сессии по 20-30 карточек' },
  { day: 'День 8-10', title: 'Тестовые задания', desc: 'Практика в условиях, похожих на отбор в компанию' },
  { day: 'День 11-14', title: 'Mock + AI Interview', desc: 'Репетиция ответов и финальная проверка прогресса' },
]
</script>

<style scoped>
.page { min-height: 100vh; }

/* ── Hero ── */
.hero {
  position: relative;
  padding: 4.4rem 0 3.4rem;
  overflow: hidden;
}
.hero-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 70% 60% at 30% -12%, rgba(31,138,112,.16) 0%, transparent 70%),
    radial-gradient(circle at 85% 82%, rgba(96,165,250,.08) 0%, transparent 46%);
  pointer-events: none;
}
.hero-content { position: relative; }
.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(280px, .85fr);
  gap: 1.2rem;
  align-items: start;
}
.hero-main { padding-top: .35rem; }
.hero-badge { margin-bottom: 1rem; display: inline-flex; }
.hero-title {
  font-size: clamp(2.15rem, 5vw, 3.4rem);
  font-weight: 800;
  line-height: 1.13;
  margin-bottom: 1rem;
  letter-spacing: -.02em;
}
.highlight {
  background: linear-gradient(135deg, var(--c-brand), var(--c-accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-sub {
  color: var(--c-text-2);
  font-size: 1.04rem;
  max-width: 760px;
  margin: 0 0 1.7rem;
  line-height: 1.62;
}
.hero-actions {
  display: flex;
  justify-content: flex-start;
  gap: 1rem;
  margin-bottom: 1.55rem;
  flex-wrap: wrap;
}
.hero-stats {
  display: flex;
  gap: 1rem;
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  padding: .95rem 1rem;
  background: var(--c-surface);
  backdrop-filter: blur(8px);
  width: fit-content;
  flex-wrap: wrap;
}
.hs { text-align: center; }
.hs-val { display: block; font-size: 1.52rem; font-weight: 800; color: var(--c-text); }
.hs-label { font-size: .74rem; color: var(--c-text-3); text-transform: uppercase; letter-spacing: .45px; font-weight: 600; }

.hero-panel {
  padding: 1rem;
  background: color-mix(in srgb, var(--c-surface) 90%, transparent);
  border: 1px solid var(--c-border-h);
}
.hero-panel h3 {
  font-size: 1.04rem;
  margin-bottom: .8rem;
}
.focus-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: .65rem;
  margin-bottom: .9rem;
}
.focus-list li {
  display: flex;
  align-items: flex-start;
  gap: .7rem;
  padding: .6rem;
  border-radius: var(--r-md);
  background: color-mix(in srgb, var(--c-bg-2) 75%, transparent);
  border: 1px solid var(--c-border);
}
.fp-day {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 74px;
  padding: .28rem .5rem;
  border-radius: var(--r-full);
  font-size: .7rem;
  font-weight: 700;
  color: var(--c-brand-h);
  background: var(--c-brand-bg);
}
.fp-body strong {
  display: block;
  font-size: .92rem;
  margin-bottom: .18rem;
}
.fp-body p {
  font-size: .83rem;
  color: var(--c-text-3);
  line-height: 1.45;
}
.hero-panel-link { width: 100%; }

/* ── How it works ── */
.how-it-works { padding: 3.4rem 0; }
.steps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.5rem;
}
.step-card {
  padding: 2rem 1.75rem;
  text-align: center;
  position: relative;
  border: 1px solid var(--c-border);
}
.step-number {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--c-brand);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: .9rem;
}
.step-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}
.step-card h3 {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--c-text);
  margin-bottom: .75rem;
}
.step-card p {
  font-size: .95rem;
  color: var(--c-text-3);
  line-height: 1.6;
}

/* ── Features ── */
.features { padding: 3.2rem 0; background: rgba(255,255,255,.01); }
.section-title {
  font-size: 1.85rem;
  font-weight: 700;
  margin-bottom: 2rem;
  text-align: center;
  color: var(--c-text);
}
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
  gap: 1.1rem;
}
.f-card {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  padding: 1.5rem 1.65rem;
  text-decoration: none;
}
.f-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--r-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.f-body { flex: 1; min-width: 0; }
.f-body h3 { font-size: 1.1rem; font-weight: 600; color: var(--c-text); margin-bottom: .3rem; }
.f-body p { font-size: .95rem; color: var(--c-text-3); line-height: 1.5; }
.f-arrow {
  color: var(--c-text-4);
  opacity: 0;
  transform: translateX(-4px);
  transition: all var(--dur) var(--ease);
  flex-shrink: 0;
}
.f-card:hover .f-arrow { opacity: 1; transform: translateX(0); }

/* ── CTA ── */
.cta { padding: 4rem 0 5rem; }
.cta-card {
  text-align: center;
  padding: 2.8rem 2rem;
  background: linear-gradient(135deg, rgba(31,138,112,.11), rgba(96,165,250,.08));
  border: 1px solid var(--c-border);
}
.cta-card h2 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--c-text);
  margin-bottom: 1rem;
}
.cta-card p {
  font-size: 1.1rem;
  color: var(--c-text-2);
  max-width: 600px;
  margin: 0 auto 2rem;
  line-height: 1.6;
}
.cta-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

@media (max-width: 640px) {
  .hero { padding: 3.2rem 0 2.8rem; }
  .hero-grid { grid-template-columns: 1fr; }
  .hero-main { text-align: center; }
  .hero-actions { justify-content: center; }
  .hero-stats { width: 100%; justify-content: center; }
  .features-grid { grid-template-columns: 1fr; }
  .steps-grid { grid-template-columns: 1fr; }
  .cta-card { padding: 2.5rem 1.5rem; }
}
</style>
