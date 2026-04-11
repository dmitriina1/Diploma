<template>
  <footer class="footer">
    <div class="footer-inner">
      <div class="footer-brand">
        <span class="footer-copy">InterviewHub © {{ year }}</span>
        <span class="footer-note">Платформа подготовки к IT-собеседованиям</span>
      </div>
      <div class="footer-links">
        <router-link to="/suggest">Предложить видео</router-link>
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
  border-top: 1px solid color-mix(in srgb, var(--c-border-h) 82%, transparent);
  background: color-mix(in srgb, var(--c-surface) 78%, transparent);
  padding: 1.2rem 0;
}
.footer-inner {
  max-width: var(--max-w-lg);
  margin: 0 auto;
  padding: 0 1.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: .8rem;
}
.footer-brand {
  display: grid;
  gap: .15rem;
}
.footer-copy {
  color: var(--c-text-3);
  font-size: .86rem;
  font-weight: 600;
}
.footer-note {
  color: var(--c-text-4);
  font-size: .76rem;
  letter-spacing: .04em;
  text-transform: uppercase;
}
.footer-links { display: flex; gap: 1.5rem; }
.footer-links a {
  color: var(--c-text-3);
  font-size: .84rem;
  padding: .25rem .45rem;
  border-radius: var(--r-sm);
  transition: color var(--dur) var(--ease), background var(--dur) var(--ease);
}
.footer-links a:hover { color: var(--c-text); }
.footer-links a:hover { background: color-mix(in srgb, var(--c-surface-h) 66%, transparent); }

@media (max-width: 480px) {
  .footer-inner {
    flex-direction: column;
    gap: .5rem;
    text-align: center;
    padding: 0 1rem;
  }
}
</style>
