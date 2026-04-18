<template>
  <footer class="footer">
    <div class="footer-inner">
      <div class="footer-brand">
        <span class="footer-copy">InterviewHub © {{ year }}</span>
        <span class="footer-note">Платформа подготовки к IT-собеседованиям</span>
      </div>
      <div class="footer-links">
        <router-link to="/suggest">Предложить видео</router-link>
        <router-link to="/interview-questions">Каталог вопросов</router-link>
        <a href="https://github.com" target="_blank" rel="noopener">GitHub</a>
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
  border-top: 1px solid var(--surface-border);
  background: color-mix(in srgb, var(--surface-bg) 92%, transparent);
  padding: 1.4rem 0;
}
.footer-inner {
  max-width: var(--max-w);
  margin: 0 auto;
  padding: 0 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: .9rem;
}
.footer-brand {
  display: grid;
  gap: .2rem;
}
.footer-copy {
  color: var(--text-secondary);
  font-size: .84rem;
  font-weight: 600;
}
.footer-note {
  color: var(--c-text-4);
  font-size: .78rem;
}

.footer-links {
  display: flex;
  gap: .5rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.footer-links a {
  color: var(--text-secondary);
  font-size: .84rem;
  padding: .35rem .62rem;
  border-radius: 999px;
  border: 1px solid var(--surface-border);
  background: color-mix(in srgb, var(--surface-bg) 86%, transparent);
  transition: color .2s ease, background .2s ease;
}

.footer-links a:hover {
  color: var(--text-primary);
  background: var(--surface-soft);
}

@media (max-width: 480px) {
  .footer-inner {
    flex-direction: column;
    gap: .5rem;
    text-align: center;
    padding: 0 1rem;
  }

  .footer-links {
    justify-content: center;
  }
}
</style>
