<template>
  <div class="page">
    <NavBar />

    <!-- Hero -->
    <section class="hero">
      <div class="hero-bg"></div>
      <div class="hero-content container">
        <span class="hero-badge badge badge-brand">Бесплатно и открыто</span>
        <h1 class="hero-title">Подготовься к <span class="highlight">IT-собеседованию</span></h1>
        <p class="hero-sub">Вопросы из реальных собеседований, тренажёр с интервальным повторением,<br>тестовые задания и аналитика рынка труда — всё в одном месте.</p>
        <div class="hero-actions">
          <router-link to="/interview-questions" class="btn btn-primary btn-lg">Перейти к вопросам →</router-link>
          <router-link to="/trainer" class="btn btn-secondary btn-lg">Тренажёр SM-2</router-link>
        </div>
        <div class="hero-stats">
          <div class="hs" v-for="s in stats" :key="s.label">
            <span class="hs-val">{{ s.value }}</span>
            <span class="hs-label">{{ s.label }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="features container-lg">
      <h2 class="section-title">Возможности</h2>
      <div class="features-grid">
        <router-link v-for="f in features" :key="f.to" :to="f.to" class="f-card card card-hover">
          <div class="f-icon" :style="{ background: f.color }">{{ f.emoji }}</div>
          <div class="f-body">
            <h3>{{ f.title }}</h3>
            <p>{{ f.desc }}</p>
          </div>
          <svg class="f-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </router-link>
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

const store = useQuestionsStore()

onMounted(() => store.fetchQuestions())

const stats = computed(() => [
  { value: store.questions.length || '—', label: 'Вопросов' },
  { value: store.topics.length || '—', label: 'Технологий' },
  { value: new Set(store.questions.map(q => q.video_url)).size || '—', label: 'Видео' },
])

const features = [
  { emoji: '📝', title: 'Вопросы с собеседований', desc: 'Полная база с фильтрацией по технологии, сложности и вероятности', to: '/interview-questions', color: 'rgba(96,165,250,.12)' },
  { emoji: '⚡', title: 'Тренажёр SM-2', desc: 'Запоминай вопросы с алгоритмом интервального повторения', to: '/trainer', color: 'rgba(124,92,252,.12)' },
  { emoji: '🎯', title: 'Mock Interview', desc: 'Симуляция интервью с итоговым скором и историей попыток', to: '/mock-interview', color: 'rgba(31,138,112,.12)' },
  { emoji: '🎬', title: 'Записи собеседований', desc: 'Реальные видео с извлечёнными вопросами и таймкодами', to: '/recordings', color: 'rgba(248,113,113,.12)' },
  { emoji: '📋', title: 'Тестовые задания', desc: 'Практические задания от IT-компаний с описанием и ссылками', to: '/test-assignments', color: 'rgba(251,191,36,.12)' },
  { emoji: '📊', title: 'Навыки из вакансий', desc: 'Что требуют работодатели — аналитика на основе HeadHunter', to: '/hh-requirements', color: 'rgba(52,211,153,.12)' },
  { emoji: '💡', title: 'Предложить видео', desc: 'Знаешь хорошее видео с собеседования? Отправь ссылку!', to: '/suggest', color: 'rgba(168,85,247,.12)' },
]
</script>

<style scoped>
.page { min-height: 100vh; }

/* ── Hero ── */
.hero {
  position: relative;
  padding: 4.5rem 0 3.5rem;
  overflow: hidden;
}
.hero-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 50% -10%, rgba(124,92,252,.18) 0%, transparent 70%),
    radial-gradient(circle at 80% 80%, rgba(96,165,250,.08) 0%, transparent 50%);
  pointer-events: none;
}
.hero-content { position: relative; text-align: center; }
.hero-badge { margin-bottom: 1.25rem; display: inline-flex; }
.hero-title {
  font-size: clamp(2.2rem, 5vw, 3.5rem);
  font-weight: 800;
  line-height: 1.15;
  margin-bottom: 1rem;
  letter-spacing: -.02em;
}
.highlight {
  background: linear-gradient(135deg, var(--c-brand), #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-sub {
  color: var(--c-text-2);
  font-size: 1.2rem;
  max-width: 660px;
  margin: 0 auto 2.25rem;
  line-height: 1.7;
}
.hero-actions {
  display: flex;
  justify-content: center;
  gap: .75rem;
  margin-bottom: 2.5rem;
  flex-wrap: wrap;
}
.hero-stats {
  display: inline-flex;
  gap: 3rem;
  border: 1px solid var(--c-border);
  border-radius: var(--r-xl);
  padding: 1.15rem 2.5rem;
  background: var(--c-surface);
}
.hs { text-align: center; }
.hs-val { display: block; font-size: 1.85rem; font-weight: 800; color: var(--c-text); }
.hs-label { font-size: .85rem; color: var(--c-text-3); text-transform: uppercase; letter-spacing: .5px; font-weight: 600; }

/* ── Features ── */
.features { padding: 3.5rem 0 4rem; }
.section-title {
  font-size: 1.85rem;
  font-weight: 700;
  margin-bottom: 2rem;
  text-align: center;
  color: var(--c-text);
}
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
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
  width: 56px; height: 56px;
  border-radius: var(--r-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}
.f-body { flex: 1; min-width: 0; }
.f-body h3 { font-size: 1.1rem; font-weight: 600; color: var(--c-text); margin-bottom: .2rem; }
.f-body p { font-size: .97rem; color: var(--c-text-3); line-height: 1.5; }
.f-arrow {
  color: var(--c-text-4);
  opacity: 0;
  transform: translateX(-4px);
  transition: all var(--dur) var(--ease);
  flex-shrink: 0;
}
.f-card:hover .f-arrow { opacity: 1; transform: translateX(0); }

@media (max-width: 640px) {
  .hero { padding: 3rem 0 2.5rem; }
  .hero-stats { gap: 1.5rem; padding: .75rem 1.25rem; }
  .features-grid { grid-template-columns: 1fr; }
  .hero-sub br { display: none; }
}
</style>
