<template>
  <nav class="nav">
    <div class="nav-inner">
      <router-link to="/" class="nav-logo" @click="menuOpen = false">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
        <span>InterviewHub</span>
      </router-link>

      <div class="nav-links" :class="{ open: menuOpen }">
        <router-link to="/interview-questions" class="nav-link" @click="menuOpen = false">Вопросы</router-link>
        <router-link to="/trainer" class="nav-link" @click="menuOpen = false">Тренажер</router-link>
        <router-link to="/ai-interview" class="nav-link" @click="menuOpen = false">AI Interview</router-link>
        <router-link to="/test-assignments" class="nav-link" @click="menuOpen = false">Задания</router-link>
        <router-link to="/hh-requirements" class="nav-link" @click="menuOpen = false">Навыки</router-link>
        <router-link to="/recordings" class="nav-link" @click="menuOpen = false">Записи</router-link>
        <router-link v-if="auth.isAdmin" to="/admin" class="nav-link" @click="menuOpen = false">Админ</router-link>
        <router-link v-if="auth.isAuthenticated" to="/profile" class="nav-link nav-mobile-only" @click="menuOpen = false">Профиль</router-link>
        <button v-if="auth.isAuthenticated" class="nav-link nav-link-btn nav-mobile-only" @click="logoutAndClose">Выйти</button>
        <router-link v-else to="/login" class="nav-link nav-mobile-only" @click="menuOpen = false">Войти</router-link>
      </div>

      <div class="nav-right">
        <button class="theme-toggle" @click="theme.toggle()" :title="theme.isDark ? 'Светлая тема' : 'Темная тема'">
          <BrandIcon :name="theme.isDark ? 'theme-light' : 'theme-dark'" :size="18" />
        </button>
        <template v-if="auth.isAuthenticated">
          <router-link to="/profile" class="nav-user" @click="menuOpen = false">
            <div class="nav-avatar">{{ initials }}</div>
            <span class="nav-username">{{ auth.displayName }}</span>
          </router-link>
          <button class="nav-action" @click="logout">Выйти</button>
        </template>
        <router-link v-else to="/login" class="nav-action nav-action-primary">Начать</router-link>
      </div>

      <button class="nav-burger" @click="menuOpen = !menuOpen" :class="{ active: menuOpen }" aria-label="Открыть меню">
        <span></span><span></span><span></span>
      </button>
    </div>

    <transition name="overlay">
      <div v-if="menuOpen" class="nav-overlay" @click="menuOpen = false"></div>
    </transition>
  </nav>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { useThemeStore } from '../stores/theme'
import BrandIcon from './BrandIcon.vue'

const auth = useAuthStore()
const theme = useThemeStore()
const route = useRoute()
const router = useRouter()
const menuOpen = ref(false)

const initials = computed(() => {
  const name = auth.user?.display_name || auth.user?.username || '?'
  return name.charAt(0).toUpperCase()
})

watch(() => route.path, () => { menuOpen.value = false })

function logout() {
  auth.logout()
  router.push('/')
}

function logoutAndClose() {
  menuOpen.value = false
  logout()
}
</script>

<style scoped>
.nav {
  position: sticky;
  top: 0;
  z-index: 120;
  background: color-mix(in srgb, var(--surface-bg) 82%, transparent);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--surface-border);
  height: var(--nav-h);
}

.nav-inner {
  max-width: var(--max-w);
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 1.5rem;
  gap: .8rem;
}

.nav-logo {
  display: inline-flex;
  align-items: center;
  gap: .45rem;
  color: var(--text-primary);
  font-family: var(--app-font-heading);
  font-size: .96rem;
  font-weight: 600;
  letter-spacing: -.01em;
  flex-shrink: 0;
}

.nav-logo svg {
  color: var(--text-primary);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: .1rem;
  margin-left: auto;
}

.nav-link {
  padding: .5rem .72rem;
  border-radius: 10px;
  font-size: .88rem;
  font-weight: 500;
  color: var(--text-secondary);
  transition: color .2s ease, background .2s ease;
  white-space: nowrap;
}

.nav-link-btn {
  width: 100%;
  text-align: left;
  border: 0;
  background: transparent;
  font: inherit;
}

.nav-mobile-only { display: none; }

.nav-link:hover,
.nav-link.router-link-active {
  color: var(--text-primary);
  background: var(--surface-soft);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: .4rem;
  margin-left: .5rem;
  flex-shrink: 0;
}

.theme-toggle {
  width: 34px;
  height: 34px;
  padding: 0;
  border-radius: 9px;
  border: 1px solid var(--surface-border);
  background: var(--surface-bg);
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.theme-toggle:hover {
  color: var(--text-primary);
  background: var(--surface-soft);
}

.nav-user {
  display: flex;
  align-items: center;
  gap: .45rem;
  padding: .25rem .45rem;
  border-radius: 10px;
  transition: background .2s ease;
}

.nav-user:hover {
  background: var(--surface-soft);
}

.nav-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--brand-soft);
  color: var(--brand-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: .84rem;
  font-weight: 600;
}

.nav-username {
  font-size: .85rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.nav-action {
  border: 1px solid var(--surface-border);
  border-radius: 999px;
  background: var(--surface-bg);
  color: var(--text-primary);
  padding: .46rem .86rem;
  font-size: .84rem;
  font-weight: 600;
}

.nav-action:hover {
  background: var(--surface-soft);
}

.nav-action-primary {
  background: #111111;
  color: #ffffff;
  border-color: #111111;
}

.nav-action-primary:hover {
  background: #2a2a2a;
  border-color: #2a2a2a;
}

.nav-burger {
  display: none;
  flex-direction: column;
  gap: 4px;
  padding: 6px;
  background: none;
  border: none;
  cursor: pointer;
}
.nav-burger span {
  width: 18px;
  height: 2px;
  background: var(--text-secondary);
  border-radius: 1px;
  transition: all .2s var(--ease);
}
.nav-burger.active span:nth-child(1) { transform: translateY(6px) rotate(45deg); }
.nav-burger.active span:nth-child(2) { opacity: 0; }
.nav-burger.active span:nth-child(3) { transform: translateY(-6px) rotate(-45deg); }

.nav-overlay {
  position: fixed;
  inset: var(--nav-h) 0 0 0;
  background: rgba(0,0,0,.36);
  z-index: 90;
}
.overlay-enter-active, .overlay-leave-active { transition: opacity .2s; }
.overlay-enter-from, .overlay-leave-to { opacity: 0; }

@media (max-width: 768px) {
  .nav-inner {
    padding: 0 1rem;
    gap: .4rem;
  }

  .nav-right {
    margin-left: auto;
    gap: .25rem;
  }

  .nav-user,
  .nav-right > .btn.btn-ghost.btn-sm,
  .nav-right > .btn.btn-primary.btn-sm {
    display: none;
  }

  .theme-toggle {
    width: 34px;
    height: 34px;
  }

  .nav-burger { display: flex; }
  .nav-links {
    position: fixed;
    top: var(--nav-h);
    right: 0;
    width: 260px;
    height: calc(100vh - var(--nav-h));
    background: var(--surface-bg);
    border-left: 1px solid var(--surface-border);
    flex-direction: column;
    align-items: stretch;
    padding: 1rem;
    gap: .25rem;
    transform: translateX(100%);
    transition: transform .25s var(--ease);
    z-index: 95;
    overflow-y: auto;
    display: none;
  }
  .nav-mobile-only { display: block; }
  .nav-links.open {
    display: flex;
    transform: translateX(0);
  }
  .nav-link { padding: .65rem .75rem; font-size: .9rem; }
  .nav-username { display: none; }
}
</style>
