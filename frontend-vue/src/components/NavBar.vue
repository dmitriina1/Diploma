<template>
  <nav class="navbar">
    <div class="navbar-container">
      <router-link to="/" class="navbar-brand">
        <i class="pi pi-bookmark"></i>
        <span>Interview Prep</span>
      </router-link>
      
      <div class="navbar-menu">
        <router-link to="/" class="navbar-link" exact>
          <i class="pi pi-home"></i>
          <span>Главная</span>
        </router-link>

        <router-link v-if="isAuthenticated" to="/trainer" class="navbar-link">
          <i class="pi pi-bolt"></i>
          <span>Тренажёр</span>
        </router-link>

        <router-link to="/interview-questions" class="navbar-link">
          <i class="pi pi-list"></i>
          <span>Вопросы</span>
        </router-link>

        <router-link v-if="isAuthenticated" to="/recordings" class="navbar-link">
          <i class="pi pi-video"></i>
          <span>Записи</span>
        </router-link>

        <router-link v-if="isAuthenticated" to="/test-assignments" class="navbar-link">
          <i class="pi pi-file-edit"></i>
          <span>Задания</span>
        </router-link>

        <router-link to="/hh-requirements" class="navbar-link">
          <i class="pi pi-chart-bar"></i>
          <span>Навыки</span>
        </router-link>
        
        <router-link v-if="isAdmin" to="/admin" class="navbar-link admin-link">
          <i class="pi pi-cog"></i>
          <span>Админка</span>
        </router-link>
      </div>
      
      <div class="navbar-right">
        <Chip :label="`${questionsCount} вопросов`" icon="pi pi-question-circle" />
        
        <template v-if="isAuthenticated">
          <div class="user-menu">
            <router-link :to="isAdmin ? '/admin' : '/profile'" class="user-chip-link" :title="isAdmin ? 'Админ-панель' : 'Профиль'">
              <Chip :label="displayName" :icon="isAdmin ? 'pi pi-shield' : 'pi pi-user'" class="user-chip" />
            </router-link>
            <button class="logout-btn" @click="handleLogout" title="Выйти">
              <i class="pi pi-sign-out"></i>
            </button>
          </div>
        </template>
        <template v-else>
          <router-link to="/login" class="login-btn">
            <i class="pi pi-sign-in"></i>
            <span>Войти</span>
          </router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useQuestionsStore } from '../store'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const questionsStore = useQuestionsStore()
const authStore = useAuthStore()

const questionsCount = computed(() => questionsStore.questions.length)
const isAuthenticated = computed(() => authStore.isAuthenticated)
const isAdmin = computed(() => authStore.isAdmin)
const displayName = computed(() => authStore.displayName)

function handleLogout() {
  authStore.logout()
  router.push('/')
}
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

.navbar-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.user-chip-link {
  text-decoration: none;
  transition: all 0.3s;
  border-radius: 16px;
}

.user-chip-link:hover .user-chip {
  background: rgba(255, 255, 255, 0.25) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.user-chip {
  background: rgba(255, 255, 255, 0.15) !important;
  color: white !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  cursor: pointer;
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  transition: all 0.3s;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.3);
  border-color: rgba(239, 68, 68, 0.5);
  color: white;
}

.login-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: white;
  padding: 0.5rem 1.2rem;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.login-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
</style>
