<template>
  <footer class="footer">
    <div class="footer-body">
      <div class="footer-brand">
        <div class="footer-logo">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
          <span>InterviewHub</span>
        </div>
        <p class="footer-desc">Платформа подготовки к IT-собеседованиям на основе анализа реальных интервью</p>
      </div>

      <div class="footer-col">
        <h4 class="footer-col-title">Подготовка</h4>
        <router-link to="/interview-questions">Вопросы</router-link>
        <router-link to="/trainer">Тренажёр SM-2</router-link>
        <router-link to="/ai-interview">AI Interview</router-link>
        <router-link to="/test-assignments">Тестовые задания</router-link>
      </div>

      <div class="footer-col">
        <h4 class="footer-col-title">Аналитика</h4>
        <router-link to="/hh-requirements">Навыки вакансий</router-link>
        <router-link to="/recordings">Записи интервью</router-link>
        <router-link to="/suggest">Предложить видео</router-link>
      </div>

      <div class="footer-col">
        <h4 class="footer-col-title">Проект</h4>
        <a href="https://github.com" target="_blank" rel="noopener">GitHub</a>
        <router-link to="/login">Войти</router-link>
      </div>
    </div>

    <div class="footer-bottom">
      <span class="footer-copy">InterviewHub © {{ year }}</span>
      <span class="footer-note">Дипломный проект — анализ видео-собеседований с AI</span>
    </div>
  </footer>
</template>

<script setup>
const year = new Date().getFullYear()
</script>

<style scoped>
.footer {
  margin-top: auto;
  border-top: 1px solid var(--c-border);
  background: var(--c-bg-2);
}

.footer-body {
  max-width: var(--max-w-lg);
  margin: 0 auto;
  padding: 3rem 1.75rem 2.5rem;
  display: grid;
  grid-template-columns: 1.6fr 1fr 1fr 1fr;
  gap: 2rem;
}

.footer-logo {
  display: flex;
  align-items: center;
  gap: .5rem;
  color: var(--c-text);
  font-family: var(--app-font-heading);
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: .75rem;
}
.footer-logo svg { color: var(--c-brand); }

.footer-desc {
  color: var(--c-text-4);
  font-size: .84rem;
  line-height: 1.6;
  max-width: 240px;
  margin: 0;
}

.footer-col-title {
  color: var(--c-text-3);
  font-size: .78rem;
  font-weight: 600;
  letter-spacing: .06em;
  text-transform: uppercase;
  margin: 0 0 .85rem;
}

.footer-col {
  display: flex;
  flex-direction: column;
  gap: .5rem;
}

.footer-col a {
  color: var(--c-text-3);
  font-size: .88rem;
  padding: .18rem 0;
  transition: color var(--dur) var(--ease);
}
.footer-col a:hover { color: var(--c-text); }

.footer-bottom {
  max-width: var(--max-w-lg);
  margin: 0 auto;
  padding: 1.25rem 1.75rem;
  border-top: 1px solid var(--c-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.footer-copy {
  color: var(--c-text-4);
  font-size: .82rem;
  font-weight: 600;
}

.footer-note {
  color: var(--c-text-4);
  font-size: .78rem;
}

@media (max-width: 900px) {
  .footer-body {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 540px) {
  .footer-body {
    grid-template-columns: 1fr;
    padding: 2rem 1rem 1.5rem;
  }
  .footer-bottom {
    flex-direction: column;
    align-items: flex-start;
    gap: .3rem;
    padding: 1rem;
  }
}
</style>
