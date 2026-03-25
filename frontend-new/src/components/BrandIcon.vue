<template>
  <span class="brand-icon" :class="`brand-icon-${name}`" :style="{ width: `${size}px`, height: `${size}px` }">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <template v-if="name === 'questions'">
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
        <circle cx="12" cy="12" r="9" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </template>
      <template v-else-if="name === 'trainer'">
        <path d="M4 6.5A2.5 2.5 0 0 1 6.5 4H20v16H6.5A2.5 2.5 0 0 1 4 17.5z" />
        <path d="M9 8h7" />
        <path d="M9 12h7" />
        <path d="M9 16h4" />
      </template>
      <template v-else-if="name === 'mock'">
        <path d="M7 8a5 5 0 0 1 10 0v3a5 5 0 0 1-10 0z" />
        <path d="M4 11v1a8 8 0 0 0 16 0v-1" />
        <path d="M12 20v2" />
      </template>
      <template v-else-if="name === 'recordings'">
        <rect x="3" y="5" width="18" height="14" rx="3" />
        <path d="m11 9 4 3-4 3z" />
      </template>
      <template v-else-if="name === 'assignments'">
        <rect x="5" y="3" width="14" height="18" rx="2" />
        <path d="M9 8h6" />
        <path d="M9 12h6" />
        <path d="M9 16h3" />
      </template>
      <template v-else-if="name === 'skills'">
        <circle cx="7" cy="9" r="3" />
        <circle cx="17" cy="15" r="3" />
        <path d="M9.5 10.5 14.5 13.5" />
        <path d="M4 18h6" />
      </template>
      <template v-else-if="name === 'suggest'">
        <path d="M12 3v18" />
        <path d="M3 12h18" />
        <circle cx="12" cy="12" r="9" />
      </template>
      <template v-else-if="name === 'flashcards'">
        <rect x="4" y="6" width="13" height="10" rx="2" />
        <path d="M8 10h5" />
        <path d="M8 13h3" />
        <path d="M17 8h3a2 2 0 0 1 2 2v6" />
      </template>
      <template v-else-if="name === 'interview'">
        <path d="M12 2a4 4 0 0 0-4 4v4a4 4 0 0 0 8 0V6a4 4 0 0 0-4-4Z" />
        <path d="M5 11v1a7 7 0 0 0 14 0v-1" />
        <path d="M12 19v3" />
      </template>
      <template v-else-if="name === 'admin'">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v10" />
        <path d="M7 12h10" />
      </template>
      <template v-else-if="name === 'profile'">
        <circle cx="12" cy="8" r="4" />
        <path d="M4 20a8 8 0 0 1 16 0" />
      </template>
      <template v-else-if="name === 'warning'">
        <path d="M12 3 2.8 19h18.4z" />
        <path d="M12 9v4" />
        <path d="M12 16h.01" />
      </template>
      <template v-else-if="name === 'success'">
        <circle cx="12" cy="12" r="9" />
        <path d="m8 12 2.8 2.8L16 9.6" />
      </template>
      <template v-else-if="name === 'empty'">
        <rect x="5" y="5" width="14" height="14" rx="3" />
        <path d="M9 10h6" />
        <path d="M9 14h6" />
      </template>
      <template v-else>
        <circle cx="12" cy="12" r="9" />
      </template>
    </svg>
  </span>
</template>

<script setup>
defineProps({
  name: { type: String, required: true },
  size: { type: Number, default: 20 }
})
</script>

<style scoped>
.brand-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: color-mix(in srgb, var(--c-brand-bg) 70%, transparent);
  color: var(--c-brand-h);
}
.brand-icon svg {
  width: 62%;
  height: 62%;
}
.brand-icon-mock,
.brand-icon-skills {
  color: var(--c-accent);
  background: color-mix(in srgb, var(--c-accent-bg) 70%, transparent);
}
.brand-icon-recordings,
.brand-icon-assignments {
  color: var(--c-violet);
  background: color-mix(in srgb, var(--c-violet-bg) 70%, transparent);
}
</style>
