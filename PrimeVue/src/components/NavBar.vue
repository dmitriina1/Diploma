<template>
  <header class="topbar">
    <router-link to="/" class="brand" aria-label="Upskill">
      <span class="brand-mark"></span>
      <span>Upskill</span>
    </router-link>

    <nav class="nav-links">
      <router-link v-for="item in visibleNavItems" :key="item.to" :to="item.to">{{ item.label }}</router-link>
    </nav>

    <div class="nav-actions">
      <button class="icon-btn" title="Переключить тему"><i class="pi pi-sun"></i></button>
      <button v-if="isAdminChrome" class="icon-btn with-dot" title="Уведомления"><i class="pi pi-bell"></i><span>3</span></button>
      <router-link to="/login" class="login-btn">Войти</router-link>
      <router-link v-if="!isAdminChrome" to="/interview-questions" class="start-btn">Начать бесплатно</router-link>
      <button v-if="isAdminChrome" class="admin-pill"><i class="pi pi-shield"></i><span>Администратор</span><b>Админ</b><i class="pi pi-angle-down"></i></button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { navItems } from '../data/mock'

const route = useRoute()
const isAdminChrome = computed(() => ['/admin', '/recordings'].includes(route.path))
const visibleNavItems = computed(() => navItems.filter((item) => item.to !== '/admin' || isAdminChrome.value))
</script>

<style scoped>
.topbar {
  height: 92px;
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 0 16px 0 42px;
  border-bottom: 1px solid rgba(63, 130, 169, .18);
  background: rgba(2, 13, 27, .78);
  backdrop-filter: blur(18px);
  position: sticky;
  top: 0;
  z-index: 20;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 250px;
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -.04em;
}

.brand-mark {
  width: 28px;
  height: 40px;
  display: inline-block;
  background: linear-gradient(145deg, #13f0e2, #0ca8ff);
  clip-path: polygon(18% 13%, 53% 0, 53% 24%, 37% 31%, 37% 69%, 68% 57%, 68% 30%, 91% 22%, 91% 72%, 38% 100%, 9% 81%, 9% 24%);
  filter: drop-shadow(0 0 18px rgba(18, 230, 209, .35));
}

.nav-links {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  flex: 1;
  height: 100%;
}

.nav-links a {
  height: 100%;
  display: inline-flex;
  align-items: center;
  color: rgba(245, 247, 251, .74);
  font-size: 17px;
  font-weight: 600;
  position: relative;
  white-space: nowrap;
}

.nav-links a.router-link-active { color: #fff; }
.nav-links a.router-link-active::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 3px;
  background: var(--cyan);
  border-radius: 999px 999px 0 0;
  box-shadow: 0 0 18px rgba(18, 230, 209, .7);
}

.nav-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 14px;
  min-width: 340px;
}

.icon-btn, .login-btn, .start-btn, .admin-pill {
  border: 1px solid rgba(83, 137, 174, .2);
  background: rgba(7, 26, 45, .78);
  color: #fff;
  border-radius: var(--radius);
  height: 54px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.icon-btn {
  width: 54px;
  color: rgba(255, 255, 255, .78);
  font-size: 22px;
  position: relative;
}

.with-dot span {
  position: absolute;
  right: 8px;
  top: 6px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--cyan);
  color: #053139;
  font-size: 12px;
  display: grid;
  place-items: center;
  font-weight: 800;
}

.login-btn { padding: 0 32px; font-weight: 700; }
.start-btn { min-width: 220px; padding: 0 34px; background: linear-gradient(135deg, #12d8c7, #0cac95); border-color: transparent; font-weight: 800; white-space: nowrap; }

.admin-pill {
  gap: 12px;
  padding: 0 18px;
  font-weight: 700;
}

.admin-pill b {
  color: var(--cyan);
  background: rgba(18, 230, 209, .12);
  padding: 5px 9px;
  border-radius: 8px;
  font-size: 13px;
}

@media (max-width: 1400px) {
  .topbar { gap: 20px; padding: 0 24px; }
  .brand { min-width: 190px; }
  .nav-links { gap: 24px; }
  .nav-actions { min-width: 0; }
  .admin-pill span, .start-btn { display: none; }
}

@media (max-width: 900px) {
  .topbar { height: auto; min-height: 80px; flex-wrap: wrap; padding: 16px; }
  .brand { min-width: 0; font-size: 26px; }
  .nav-links { order: 3; width: 100%; justify-content: flex-start; overflow-x: auto; gap: 22px; height: 44px; }
  .nav-actions { margin-left: auto; }
  .login-btn, .admin-pill { display: none; }
}
</style>
