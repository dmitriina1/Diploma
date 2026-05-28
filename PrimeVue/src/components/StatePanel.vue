<template>
  <div class="state-panel state-theme" :class="`state-${type}`">
    <BrandIcon :name="icon" :size="60" />
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
    <slot />
  </div>
</template>

<script setup>
import BrandIcon from './BrandIcon.vue'

defineProps({
  icon: { type: String, default: 'suggest' },
  title: { type: String, required: true },
  description: { type: String, required: true },
  type: { type: String, default: 'empty' }
})
</script>

<style scoped>
.state-theme {
  display: grid;
  justify-items: center;
  gap: .65rem;
}
.state-theme h3 { margin-top: .35rem; }
.state-theme p { max-width: 54ch; }
.state-error { border-style: solid; }
</style>
