<template>
  <nav class="nav">
    <div class="nav-inner">
      <router-link to="/" class="nav-logo">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
        <span class="logo-title">InterviewHub</span>
        <span class="logo-sub">IT interview readiness</span>
      </router-link>

      <div class="nav-links" :class="{ open: menuOpen }">
        <router-link to="/interview-questions" class="nav-link" @click="menuOpen = false">Вопросы</router-link>
        <router-link to="/trainer" class="nav-link" @click="menuOpen = false">Тренажёр</router-link>
        <router-link to="/ai-interview" class="nav-link" @click="menuOpen = false">AI Interview</router-link>
        <router-link to="/test-assignments" class="nav-link" @click="menuOpen = false">Задания</router-link>
        <router-link to="/hh-requirements" class="nav-link" @click="menuOpen = false">Навыки</router-link>
        <router-link to="/recordings" class="nav-link" @click="menuOpen = false">Записи</router-link>
        <router-link v-if="auth.isAdmin" to="/admin" class="nav-link" @click="menuOpen = false">Админка</router-link>
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
  z-index: 120;
  background: color-mix(in srgb, var(--c-bg) 74%, transparent);
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
  border-bottom: 1px solid color-mix(in srgb, var(--c-border-h) 78%, transparent);
  height: var(--nav-h);
}
.nav-inner {
  max-width: var(--max-w-lg);
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 1.75rem;
  gap: .9rem;
}

/* Logo */
.nav-logo {
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto auto;
  align-items: center;
  column-gap: .6rem;
  color: var(--c-text);
  flex-shrink: 0;
}
.nav-logo svg {
  grid-row: 1 / span 2;
  color: var(--c-brand);
  width: 28px;
  height: 28px;
  padding: .2rem;
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-brand-bg) 70%, transparent);
}
.logo-title {
  font-family: var(--app-font-heading);
  font-size: 1.02rem;
  line-height: 1;
  font-weight: 700;
  background: linear-gradient(132deg, var(--c-text), color-mix(in srgb, var(--c-text) 66%, var(--c-brand-h)));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.logo-sub {
  font-size: .65rem;
  line-height: 1;
  color: var(--c-text-4);
  text-transform: uppercase;
  letter-spacing: .09em;
}

/* Links */
.nav-links {
  display: flex;
  align-items: center;
  gap: .22rem;
  margin-left: auto;
}
.nav-link {
  padding: .53rem .86rem;
  border-radius: var(--r-full);
  font-size: .92rem;
  font-weight: 500;
  color: var(--c-text-2);
  transition: all var(--dur) var(--ease);
  position: relative;
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
.nav-link::after {
  content: '';
  position: absolute;
  inset: 0;
  border: 1px solid transparent;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--c-brand), var(--c-accent));
  opacity: 0;
  transform: scale(.96);
  transition: opacity var(--dur), transform var(--dur);
  -webkit-mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}
.nav-link:hover,
.nav-link.router-link-active {
  color: var(--c-text);
  background: color-mix(in srgb, var(--c-surface) 58%, var(--c-brand-bg));
}
.nav-link:hover::after,
.nav-link.router-link-active::after { opacity: 1; transform: scaleX(1); }

/* Right */
.nav-right {
  display: flex;
  align-items: center;
  gap: .42rem;
  margin-left: .5rem;
  flex-shrink: 0;
}
.theme-toggle {
  width: 36px;
  height: 36px;
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
  width: 34px; height: 34px;
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
  font-size: .9rem;
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
    display: flex;
    gap: .45rem;
    font-size: 1rem;
  }

  .logo-sub {
    display: none;
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
  .logo-title { display: none; }
}
</style>
