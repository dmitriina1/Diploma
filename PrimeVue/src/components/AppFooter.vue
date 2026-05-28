<template>
  <footer class="footer">
    <div class="footer-inner">
      <div class="footer-brand">
        <span class="footer-copy">InterviewHub © {{ year }}</span>
        <span class="footer-note">Платформа подготовки к IT-собеседованиям</span>
        <span class="footer-legal">Для пользователей: обучение и практика. Загрузка видео доступна только администраторам.</span>
      </div>

      <div class="footer-nav">
        <div class="footer-col">
          <div class="footer-col-title">Подготовка</div>
          <router-link to="/interview-questions">Вопросы</router-link>
          <router-link to="/trainer">Тренажёр</router-link>
          <router-link to="/ai-interview">AI Interview</router-link>
          <router-link to="/mock-interview">Mock Interview</router-link>
        </div>

        <div class="footer-col">
          <div class="footer-col-title">Контент</div>
          <router-link to="/recordings">Записи</router-link>
          <router-link to="/test-assignments">Задания</router-link>
          <router-link to="/hh-requirements">Навыки HH</router-link>
          <router-link to="/suggest">Предложить видео</router-link>
        </div>

        <div class="footer-col">
          <div class="footer-col-title">Платформа</div>
          <router-link to="/">Главная</router-link>
          <router-link to="/profile">Профиль</router-link>
          <a href="https://github.com" target="_blank" rel="noopener">GitHub</a>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
const year = new Date().getFullYear()
</script>

<style scoped>
.footer {
  margin-top: auto;
  border-top: 1px solid var(--line);
  background: transparent;
  padding: 34px 0 28px;
}
.footer-inner {
  width: min(1720px, calc(100% - 72px));
  margin: 0 auto;
  padding: 24px 28px;
  display: grid;
  grid-template-columns: minmax(230px, .9fr) minmax(0, 1.6fr);
  justify-content: space-between;
  gap: 1.2rem;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: linear-gradient(180deg, rgba(8, 35, 60, .58), rgba(4, 22, 40, .52));
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
}
.footer-brand {
  display: grid;
  gap: .25rem;
}
.footer-copy {
  color: var(--muted);
  font-size: 17px;
  font-weight: 600;
}
.footer-note {
  color: var(--c-text-4);
  font-size: 16px;
}

.footer-legal {
  color: var(--c-text-4);
  font-size: 15px;
  line-height: 1.45;
  max-width: 38ch;
}

.footer-nav {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: .9rem;
}

.footer-col {
  display: grid;
  align-content: start;
  gap: .32rem;
}

.footer-col-title {
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--c-text-4);
  margin-bottom: .2rem;
}

.footer-nav a {
  color: var(--muted);
  font-size: 16px;
  transition: color .2s ease;
  width: fit-content;
}

.footer-nav a:hover {
  color: var(--text);
}

@media (max-width: 860px) {
  .footer-inner {
    width: min(100% - 32px, 980px);
  }

  .footer-inner {
    grid-template-columns: 1fr;
  }

  .footer-nav {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .footer-inner {
    gap: .7rem;
    text-align: left;
    padding: 20px;
  }

  .footer-nav {
    grid-template-columns: 1fr;
    gap: .5rem;
  }
}
</style>
