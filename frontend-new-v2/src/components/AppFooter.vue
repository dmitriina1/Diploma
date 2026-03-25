<template>
  <footer class="footer gradient-line">
    <div class="footer-inner">
      <div>
        <span class="footer-copy">InterviewHub © {{ year }}</span>
        <p class="footer-note">AI-driven prep platform for engineering interviews</p>
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
  border-top: 1px solid var(--c-border);
  padding: 2rem 0;
}
.footer-inner {
  max-width: var(--max-w-lg);
  margin: 0 auto;
  padding: 0 1.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.footer-copy { color: var(--c-text-4); font-size: .9rem; }
.footer-note { color: var(--c-text-4); font-size: .74rem; margin-top: .2rem; letter-spacing: .04em; text-transform: uppercase; }
.footer-links { display: flex; gap: 1.5rem; }
.footer-links a { color: var(--c-text-3); font-size: .9rem; transition: color var(--dur) var(--ease); }
.footer-links a:hover { color: var(--c-text); }

@media (max-width: 480px) {
  .footer-inner { flex-direction: column; gap: .5rem; text-align: center; }
}
</style>
