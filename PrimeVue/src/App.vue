<script setup>
import AppFooter from './components/AppFooter.vue'
</script>

<template>
  <div class="app-shell">
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
    <AppFooter />
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-shell :deep(.page) {
  flex: 1 0 auto;
  min-height: auto;
}
</style>
