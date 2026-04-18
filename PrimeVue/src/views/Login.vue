<template>
  <div class="login-page">
    <div class="login-box">
      <router-link to="/" class="back-link">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        На главную
      </router-link>

      <div class="logo">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--c-brand)" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
        <h1>Interview Prep</h1>
      </div>
      <p class="subtitle">{{ isRegister ? 'Создайте аккаунт' : 'Войдите в аккаунт' }}</p>

      <div class="tabs">
        <button :class="{ active: !isRegister }" @click="switchMode(false)">Вход</button>
        <button :class="{ active: isRegister }" @click="switchMode(true)">Регистрация</button>
      </div>

      <form @submit.prevent="handleSubmit" class="form">
        <div class="field">
          <label for="u">Логин</label>
          <input id="u" v-model="username" class="input" placeholder="Введите логин" autocomplete="username" />
        </div>
        <div v-if="isRegister" class="field">
          <label for="dn">Имя (необязательно)</label>
          <input id="dn" v-model="displayName" class="input" placeholder="Как вас называть?" autocomplete="name" />
        </div>
        <div class="field">
          <label for="p">Пароль</label>
          <input id="p" v-model="password" type="password" class="input" placeholder="Введите пароль" autocomplete="current-password" />
        </div>
        <div v-if="error" class="err">{{ error }}</div>
        <button type="submit" class="btn btn-primary btn-lg submit" :disabled="loading">
          {{ loading ? 'Загрузка...' : isRegister ? 'Зарегистрироваться' : 'Войти' }}
        </button>
      </form>

      <p class="switch-text">
        <template v-if="!isRegister">Нет аккаунта? <a href="#" @click.prevent="switchMode(true)">Зарегистрируйтесь</a></template>
        <template v-else>Уже есть аккаунт? <a href="#" @click.prevent="switchMode(false)">Войдите</a></template>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const isRegister = ref(false)
const username = ref('')
const password = ref('')
const displayName = ref('')
const loading = computed(() => auth.loading)
const error = computed(() => auth.error)

function switchMode(r) { isRegister.value = r; auth.clearError() }

async function handleSubmit() {
  if (!username.value || !password.value) { auth.error = 'Заполните логин и пароль'; return }
  let ok = false
  if (isRegister.value) ok = await auth.register(username.value, password.value, displayName.value || null)
  else ok = await auth.login(username.value, password.value)
  if (ok) router.push(route.query.redirect || '/')
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-bg);
  padding: 2rem;
}
.login-box {
  width: 100%;
  max-width: 420px;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-xl);
  padding: 2.75rem;
}
.back-link {
  display: inline-flex;
  align-items: center;
  gap: .4rem;
  color: var(--c-text-3);
  text-decoration: none;
  font-size: .88rem;
  margin-bottom: 1.5rem;
  transition: color var(--dur);
}
.back-link:hover { color: var(--c-brand); }
.logo {
  display: flex;
  align-items: center;
  gap: .6rem;
  margin-bottom: .35rem;
}
.logo h1 {
  font-size: 1.55rem;
  font-weight: 500;
  background: linear-gradient(135deg, var(--c-brand), var(--c-brand-h));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.subtitle {
  color: var(--c-text-3);
  font-size: .94rem;
  margin-bottom: 1.5rem;
}
.tabs {
  display: flex;
  border-radius: var(--r-md);
  border: 1px solid var(--c-border);
  overflow: hidden;
  margin-bottom: 1.5rem;
}
.tabs button {
  flex: 1;
  padding: .7rem 1rem;
  border: none;
  background: transparent;
  color: var(--c-text-3);
  font-size: .95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--dur);
}
.tabs button.active {
  background: var(--c-brand);
  color: #fff;
}
.tabs button:hover:not(.active) {
  background: var(--c-bg-2);
  color: var(--c-text);
}
.form {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: .3rem;
}
.field label {
  font-size: .85rem;
  color: var(--c-text-2);
  font-weight: 500;
}
.err {
  padding: .6rem .8rem;
  background: var(--c-err-bg);
  color: var(--c-err);
  border-radius: var(--r-sm);
  font-size: .85rem;
  font-weight: 500;
}
.submit { width: 100%; margin-top: .5rem; }
.switch-text {
  text-align: center;
  margin-top: 1.5rem;
  color: var(--c-text-3);
  font-size: .88rem;
}
.switch-text a {
  color: var(--c-brand);
  font-weight: 600;
  text-decoration: none;
}
.switch-text a:hover { text-decoration: underline; }
</style>
