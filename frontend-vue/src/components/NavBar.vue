<template>
  <nav class="navbar">
    <div class="navbar-container">
      <router-link to="/" class="navbar-brand">
        <i class="pi pi-bookmark"></i>
        <span>Interview Prep</span>
      </router-link>
      
      <div class="navbar-menu">
        <router-link to="/" class="navbar-link">
          <i class="pi pi-home"></i>
          <span>Главная</span>
        </router-link>
        
        <router-link to="/admin" class="navbar-link">
          <i class="pi pi-cog"></i>
          <span>Админка</span>
        </router-link>
      </div>
      
      <div class="navbar-stats">
        <Chip :label="`${questionsCount} вопросов`" icon="pi pi-question-circle" />
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useQuestionsStore } from '../store'

const questionsStore = useQuestionsStore()

const questionsCount = computed(() => questionsStore.questions.length)
</script>

<style scoped>
.navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-size: 200% 200%;
  padding: 1.2rem 2rem;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
  position: sticky;
  top: 0;
  z-index: 1000;
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  animation: gradient-shift 15s ease infinite;
}

.navbar-container {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  text-decoration: none;
  color: white;
  font-size: 1.6rem;
  font-weight: 800;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.navbar-brand i {
  transition: transform 0.4s ease;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.navbar-brand:hover {
  transform: scale(1.05);
  text-shadow: 0 4px 20px rgba(255, 255, 255, 0.3);
}

.navbar-brand:hover i {
  transform: rotate(10deg) scale(1.1);
}

.navbar-menu {
  display: flex;
  gap: 1rem;
  flex: 1;
  margin-left: 3rem;
}

.navbar-link {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 600;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.navbar-link::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.1);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s ease;
  border-radius: 8px;
}

.navbar-link:hover::before,
.navbar-link.router-link-active::before {
  transform: scaleX(1);
}

.navbar-link:hover,
.navbar-link.router-link-active {
  color: white;
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.navbar-link i {
  transition: transform 0.3s ease;
}

.navbar-link:hover i {
  transform: scale(1.2);
}

.navbar-stats {
  display: flex;
  gap: 1rem;
}
</style>
