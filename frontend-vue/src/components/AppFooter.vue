<template>
  <footer class="app-footer">
    <div class="footer-container">
      <div class="footer-section brand">
        <div class="footer-logo">
          <i class="pi pi-bookmark"></i>
          <span>Interview Prep</span>
        </div>
        <p class="footer-desc">Платформа подготовки к IT-собеседованиям на основе анализа реальных интервью</p>
      </div>

      <div class="footer-section">
        <h4>Навигация</h4>
        <router-link to="/">Главная</router-link>
        <router-link to="/trainer">Тренажёр</router-link>
        <router-link to="/recordings">Записи собеседований</router-link>
        <router-link to="/interview-questions">Вопросы с собеседований</router-link>
      </div>

      <div class="footer-section">
        <h4>Сообщество</h4>
        <router-link to="/suggest">Предложить видео</router-link>
        <a href="https://github.com" target="_blank" rel="noopener">GitHub</a>
      </div>

      <div class="footer-section">
        <h4>О проекте</h4>
        <p class="footer-text">Дипломный проект — автоматизированная система анализа видео-собеседований с использованием Whisper и LLM.</p>
      </div>
    </div>

    <div class="footer-bottom">
      <span>&copy; {{ new Date().getFullYear() }} Interview Prep. Проект разработан в образовательных целях.</span>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  background: rgba(10, 10, 30, 0.95);
  border-top: 1px solid rgba(255,255,255,0.06);
  padding: 3rem 2rem 1.5rem;
  margin-top: 4rem;
}
.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr 1.2fr;
  gap: 2rem;
}
.footer-logo {
  display: flex; align-items: center; gap: 0.6rem;
  font-size: 1.3rem; font-weight: 700; color: white; margin-bottom: 0.75rem;
}
.footer-logo i { color: #667eea; font-size: 1.4rem; }
.footer-desc { color: rgba(255,255,255,0.4); font-size: 0.85rem; line-height: 1.5; }
.footer-section h4 { color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
.footer-section a {
  display: block; color: rgba(255,255,255,0.45); text-decoration: none;
  font-size: 0.88rem; padding: 0.25rem 0; transition: color 0.2s;
}
.footer-section a:hover { color: #667eea; }
.footer-text { color: rgba(255,255,255,0.4); font-size: 0.83rem; line-height: 1.5; }
.footer-bottom {
  max-width: 1200px; margin: 2rem auto 0;
  padding-top: 1.25rem; border-top: 1px solid rgba(255,255,255,0.06);
  text-align: center; color: rgba(255,255,255,0.3); font-size: 0.8rem;
}

@media (max-width: 768px) {
  .footer-container { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 480px) {
  .footer-container { grid-template-columns: 1fr; }
}
</style>
