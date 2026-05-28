<template>
  <nav class="nav">
    <div class="nav-inner">
      <router-link to="/" class="nav-logo">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
        <span>InterviewHub V2</span>
      </router-link>

      <div class="nav-links" :class="{ open: menuOpen }">
        <router-link to="/interview-questions" class="nav-link" @click="menuOpen = false">Вопросы</router-link>
        <router-link to="/trainer" class="nav-link" @click="menuOpen = false">Тренажёр</router-link>
        <router-link to="/ai-interview" class="nav-link" @click="menuOpen = false">AI Interview</router-link>
        <router-link to="/test-assignments" class="nav-link" @click="menuOpen = false">Задания</router-link>
        <router-link to="/hh-requirements" class="nav-link" @click="menuOpen = false">Навыки</router-link>
        <router-link to="/recordings" class="nav-link" @click="menuOpen = false">Записи</router-link>
        <router-link v-if="auth.isAdmin" to="/admin" class="nav-link" @click="menuOpen = false">Админ</router-link>
        <router-link
          v-if="auth.isAuthenticated"
          to="/profile"
          class="nav-link nav-mobile-only"
          @click="menuOpen = false"
        >
          Профиль
        </router-link>
        <button
          v-if="auth.isAuthenticated"
          class="nav-link nav-link-btn nav-mobile-only"
          @click="logoutAndClose"
        >
          Выйти
        </button>
        <router-link
          v-else
          to="/login"
          class="nav-link nav-mobile-only"
          @click="menuOpen = false"
        >
          Войти
        </router-link>
      </div>

      <div class="nav-right">
        <button class="btn btn-ghost btn-sm theme-toggle" @click="theme.toggle()" :title="theme.isDark ? 'Светлая тема' : 'Тёмная тема'">
          <BrandIcon :name="theme.isDark ? 'theme-light' : 'theme-dark'" :size="24" />
        </button>
        <template v-if="auth.isAuthenticated">
          <router-link to="/profile" class="nav-user">
            <div class="nav-avatar">{{ initials }}</div>
            <span class="nav-username">{{ auth.displayName }}</span>
          </router-link>
          <button class="btn btn-ghost btn-sm" @click="logout">Выйти</button>
        </template>
        <router-link v-else to="/login" class="btn btn-primary btn-sm">Войти</router-link>
      </div>

      <button class="nav-burger" @click="menuOpen = !menuOpen" :class="{ active: menuOpen }">
        <span></span><span></span><span></span>
      </button>
    </div>

    <!-- Mobile overlay -->
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
  z-index: 100;
  background: var(--c-bg);
  background: color-mix(in srgb, var(--c-bg) 82%, transparent);
  backdrop-filter: blur(16px) saturate(1.4);
  -webkit-backdrop-filter: blur(16px) saturate(1.4);
  border-bottom: 1px solid var(--c-border);
  height: var(--nav-h);
}
.nav-inner {
  max-width: var(--max-w-lg);
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 1.75rem;
  gap: 1.25rem;
}

/* Logo */
.nav-logo {
  display: flex;
  align-items: center;
  gap: .6rem;
  color: var(--c-text);
  font-weight: 700;
  font-size: 1.22rem;
  flex-shrink: 0;
}
.nav-logo svg { color: var(--c-brand); width: 26px; height: 26px; }
.nav-logo span {
  background: linear-gradient(130deg, var(--c-text), color-mix(in srgb, var(--c-text) 65%, var(--c-brand-h)));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* Links */
.nav-links {
  display: flex;
  align-items: center;
  gap: .15rem;
  margin-left: auto;
}
.nav-link {
  padding: .55rem 1rem;
  border-radius: var(--r-sm);
  font-size: 1rem;
  font-weight: 500;
  color: var(--c-text-2);
  transition: all var(--dur) var(--ease);
  position: relative;
}
.nav-link-btn {
  width: 100%;
  text-align: left;
  border: 0;
  background: transparent;
  font: inherit;
}
.nav-mobile-only { display: none; }
.nav-link::after {
  content: '';
  position: absolute;
  left: .85rem;
  right: .85rem;
  bottom: .32rem;
  height: 2px;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--c-brand), var(--c-accent));
  opacity: 0;
  transform: scaleX(.6);
  transition: opacity var(--dur), transform var(--dur);
}
.nav-link:hover,
.nav-link.router-link-active {
  color: var(--c-text);
  background: color-mix(in srgb, var(--c-surface) 70%, var(--c-brand-bg));
}
.nav-link:hover::after,
.nav-link.router-link-active::after { opacity: 1; transform: scaleX(1); }

/* Right */
.nav-right {
  display: flex;
  align-items: center;
  gap: .5rem;
  margin-left: .5rem;
  flex-shrink: 0;
}
.theme-toggle {
  width: 38px;
  height: 38px;
  padding: 0;
}
.nav-user {
  display: flex;
  align-items: center;
  gap: .45rem;
  padding: .25rem .5rem;
  border-radius: var(--r-md);
  transition: background var(--dur) var(--ease);
}
.nav-user:hover { background: var(--c-surface); }
.nav-avatar {
  width: 38px; height: 38px;
  border-radius: 50%;
  background: var(--c-brand-bg);
  color: var(--c-brand-h);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: .9rem;
  font-weight: 700;
}
.nav-username {
  font-size: .95rem;
  color: var(--c-text-2);
  font-weight: 500;
}

/* Burger */
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
  width: 18px; height: 2px;
  background: var(--c-text-2);
  border-radius: 1px;
  transition: all .2s var(--ease);
}
.nav-burger.active span:nth-child(1) { transform: translateY(6px) rotate(45deg); }
.nav-burger.active span:nth-child(2) { opacity: 0; }
.nav-burger.active span:nth-child(3) { transform: translateY(-6px) rotate(-45deg); }

/* Overlay */
.nav-overlay {
  position: fixed;
  inset: var(--nav-h) 0 0 0;
  background: rgba(0,0,0,.5);
  z-index: 90;
}
.overlay-enter-active, .overlay-leave-active { transition: opacity .2s; }
.overlay-enter-from, .overlay-leave-to { opacity: 0; }

/* Mobile */
@media (max-width: 768px) {
  .nav-inner {
    padding: 0 .9rem;
    gap: .45rem;
  }

  .nav-logo {
    gap: .4rem;
    font-size: 1rem;
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
    background: var(--c-bg-1);
    border-left: 1px solid var(--c-border);
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

@media (max-width: 460px) {
  .nav-logo span { display: none; }
}
</style>
