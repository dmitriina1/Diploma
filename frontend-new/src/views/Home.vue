<template>
  <div class="page">
    <NavBar />

    <!-- Hero -->
    <section class="hero">
      <div class="hero-bg"></div>
      <div class="hero-content container">
        <span class="hero-badge badge badge-brand">AI-powered подготовка</span>
        <h1 class="hero-title">Готовься к <span class="highlight">IT-собеседованиям</span><br>умнее и быстрее</h1>
        <p class="hero-sub">Автоматическое извлечение вопросов из видео, интеллектуальный тренажёр с SM-2,<br>аналитика рынка труда и тестовые задания от топовых компаний.</p>
        <div class="hero-actions">
          <router-link to="/interview-questions" class="btn btn-primary btn-lg">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 8px;">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
            </svg>
            Начать подготовку
          </router-link>
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

    <!-- How it works -->
    <section class="how-it-works container-lg">
      <h2 class="section-title">Как это работает</h2>
      <div class="steps-grid">
        <div class="step-card card" v-for="(step, i) in steps" :key="i">
          <div class="step-number">{{ i + 1 }}</div>
          <div class="step-icon">{{ step.emoji }}</div>
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
          <div class="f-icon" :style="{ background: f.color }">{{ f.emoji }}</div>
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

const store = useQuestionsStore()

onMounted(() => store.fetchQuestions())

const stats = computed(() => [
  { value: store.questions.length || '—', label: 'Вопросов' },
  { value: store.topics.length || '—', label: 'Технологий' },
  { value: new Set(store.questions.map(q => q.video_url)).size || '—', label: 'Видео' },
])

const steps = [
  { emoji: '🎬', title: 'Загрузка видео', desc: 'Система автоматически обрабатывает видео с YouTube, VK, Rutube и других платформ' },
  { emoji: '🤖', title: 'AI-анализ', desc: 'Whisper транскрибирует речь, LLM извлекает вопросы, FAISS удаляет дубликаты' },
  { emoji: '📚', title: 'База знаний', desc: 'Вопросы структурируются по темам, сложности и вероятности встречи' },
  { emoji: '🎯', title: 'Подготовка', desc: 'Используй тренажёр SM-2, mock-интервью и аналитику для эффективной подготовки' },
]

const features = [
  { emoji: '📝', title: 'Вопросы с собеседований', desc: 'База вопросов с фильтрацией по технологии, сложности и вероятности', to: '/interview-questions', color: 'rgba(96,165,250,.12)' },
  { emoji: '⚡', title: 'Тренажёр SM-2', desc: 'Интервальное повторение для эффективного запоминания', to: '/trainer', color: 'rgba(124,92,252,.12)' },
  { emoji: '🤖', title: 'AI Interview', desc: 'Чат с AI-интервьюером для реалистичной симуляции собеседования', to: '/ai-interview', color: 'rgba(31,138,112,.12)' },
  { emoji: '🎬', title: 'Записи собеседований', desc: 'Видео с извлечёнными вопросами и таймкодами', to: '/recordings', color: 'rgba(248,113,113,.12)' },
  { emoji: '📋', title: 'Тестовые задания', desc: 'Задания от Яндекс, СБЕР, VK, Т-Банк и других компаний', to: '/test-assignments', color: 'rgba(251,191,36,.12)' },
  { emoji: '📊', title: 'Навыки из вакансий', desc: 'Аналитика требований работодателей на основе HH.ru', to: '/hh-requirements', color: 'rgba(52,211,153,.12)' },
  { emoji: '💡', title: 'Предложить видео', desc: 'Знаешь полезное видео? Отправь ссылку для обработки', to: '/suggest', color: 'rgba(168,85,247,.12)' },
]
</script>

<style scoped>
.page { min-height: 100vh; }

/* ── Hero ── */
.hero {
  position: relative;
  padding: 5rem 0 4rem;
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
.hero-badge { margin-bottom: 1.5rem; display: inline-flex; }
.hero-title {
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 800;
  line-height: 1.15;
  margin-bottom: 1.25rem;
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
  font-size: 1.15rem;
  max-width: 720px;
  margin: 0 auto 2.5rem;
  line-height: 1.7;
}
.hero-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 3rem;
  flex-wrap: wrap;
}
.hero-stats {
  display: inline-flex;
  gap: 3rem;
  border: 1px solid var(--c-border);
  border-radius: var(--r-xl);
  padding: 1.25rem 2.75rem;
  background: var(--c-surface);
  backdrop-filter: blur(12px);
}
.hs { text-align: center; }
.hs-val { display: block; font-size: 2rem; font-weight: 800; color: var(--c-text); }
.hs-label { font-size: .85rem; color: var(--c-text-3); text-transform: uppercase; letter-spacing: .5px; font-weight: 600; }

/* ── How it works ── */
.how-it-works { padding: 4rem 0; }
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
  font-size: 3rem;
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
.features { padding: 4rem 0; background: rgba(255,255,255,.01); }
.section-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 2.5rem;
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
  padding: 3.5rem 2rem;
  background: linear-gradient(135deg, rgba(31,138,112,.08), rgba(124,92,252,.08));
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
  .hero { padding: 3.5rem 0 3rem; }
  .hero-stats { gap: 1.5rem; padding: 1rem 1.5rem; }
  .features-grid { grid-template-columns: 1fr; }
  .steps-grid { grid-template-columns: 1fr; }
  .hero-sub br { display: none; }
  .cta-card { padding: 2.5rem 1.5rem; }
}
</style>
