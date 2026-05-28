<template>
  <div class="login-page">
    <router-link to="/" class="brand">
      <span class="brand-mark"></span>
      <span>Upskill</span>
    </router-link>

    <main class="login-shell">
      <section class="login-story">
        <p class="kicker">Personal workspace</p>
        <h1>{{ isRegister ? 'Создайте профиль подготовки' : 'Войдите в Upskill' }}</h1>
        <p>
          Сохраняйте заметки, закладки, ответы сообщества, прогресс SM-2 и историю mock-интервью в одном рабочем пространстве.
        </p>
        <div class="story-grid">
          <article v-for="item in benefits" :key="item.title" class="glass">
            <i :class="item.icon"></i>
            <b>{{ item.title }}</b>
            <span>{{ item.text }}</span>
          </article>
        </div>
      </section>

      <section class="login-card glass neon-border">
        <router-link to="/" class="back-link"><i class="pi pi-arrow-left"></i>На главную</router-link>
        <div class="card-head">
          <span class="login-icon"><i class="pi pi-shield"></i></span>
          <div>
            <h2>{{ isRegister ? 'Регистрация' : 'Вход' }}</h2>
            <p>{{ isRegister ? 'Новый аккаунт для учебного трека' : 'Продолжите подготовку с того места, где остановились' }}</p>
          </div>
        </div>

        <div class="tabs">
          <button type="button" :class="{ active: !isRegister }" @click="switchMode(false)">Вход</button>
          <button type="button" :class="{ active: isRegister }" @click="switchMode(true)">Регистрация</button>
        </div>

        <form class="form" @submit.prevent="handleSubmit">
          <label>
            <span>Логин</span>
            <input v-model="username" placeholder="Введите логин" autocomplete="username" />
          </label>
          <label v-if="isRegister">
            <span>Имя</span>
            <input v-model="displayName" placeholder="Как вас называть?" autocomplete="name" />
          </label>
          <label>
            <span>Пароль</span>
            <input v-model="password" type="password" placeholder="Введите пароль" :autocomplete="isRegister ? 'new-password' : 'current-password'" />
          </label>

          <div v-if="error" class="err"><i class="pi pi-exclamation-triangle"></i>{{ error }}</div>
          <button type="submit" class="btn primary submit" :disabled="loading">
            <i :class="loading ? 'pi pi-spin pi-spinner' : 'pi pi-arrow-right'"></i>
            {{ loading ? 'Проверяем...' : isRegister ? 'Создать аккаунт' : 'Войти' }}
          </button>
        </form>

        <p class="switch-text">
          <template v-if="!isRegister">Нет аккаунта? <a href="#" @click.prevent="switchMode(true)">Зарегистрируйтесь</a></template>
          <template v-else>Уже есть аккаунт? <a href="#" @click.prevent="switchMode(false)">Войдите</a></template>
        </p>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
const benefits = [
  { title: 'Закладки', text: 'Сохраняйте важные вопросы и возвращайтесь к ним перед интервью.', icon: 'pi pi-bookmark' },
  { title: 'SM-2 прогресс', text: 'Повторы и оценки остаются привязаны к вашему профилю.', icon: 'pi pi-refresh' },
  { title: 'Личные заметки', text: 'Формулируйте ответы под свой опыт и стиль речи.', icon: 'pi pi-pencil' }
]

function switchMode(register) {
  isRegister.value = register
  auth.clearError()
}

async function handleSubmit() {
  if (!username.value || !password.value) {
    auth.error = 'Заполните логин и пароль'
    return
  }
  const ok = isRegister.value
    ? await auth.register(username.value, password.value, displayName.value || null)
    : await auth.login(username.value, password.value)
  if (ok) router.push(route.query.redirect || '/')
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  padding: 26px 38px 42px;
  background:
    radial-gradient(circle at 72% 18%, rgba(18, 230, 209, .13), transparent 28%),
    radial-gradient(circle at 12% 72%, rgba(77, 163, 255, .1), transparent 34%),
    var(--bg);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 14px;
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

.login-shell {
  width: min(1500px, 100%);
  min-height: calc(100vh - 110px);
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 520px;
  gap: 56px;
  align-items: center;
}

.login-story .kicker {
  color: var(--cyan);
  text-transform: uppercase;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: .08em;
}

.login-story h1 {
  max-width: 760px;
  margin: 14px 0 20px;
  font-size: 66px;
  line-height: 1.05;
  letter-spacing: -.055em;
}

.login-story > p:not(.kicker) {
  max-width: 660px;
  margin: 0 0 34px;
  color: var(--muted);
  font-size: 22px;
  line-height: 1.55;
}

.story-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  max-width: 900px;
}

.story-grid article {
  padding: 20px;
  min-height: 165px;
}

.story-grid i {
  color: var(--cyan);
  font-size: 27px;
}

.story-grid b {
  display: block;
  margin: 20px 0 8px;
  font-size: 18px;
}

.story-grid span {
  color: var(--muted);
  line-height: 1.45;
}

.login-card {
  padding: 30px;
  border-radius: 16px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: var(--muted);
  font-weight: 700;
  margin-bottom: 28px;
}

.card-head {
  display: flex;
  gap: 18px;
  align-items: center;
  margin-bottom: 24px;
}

.login-icon {
  width: 62px;
  height: 62px;
  display: grid;
  place-items: center;
  color: var(--cyan);
  border: 1px solid rgba(18, 230, 209, .28);
  background: rgba(18, 230, 209, .07);
  border-radius: 14px;
  font-size: 28px;
}

.card-head h2 {
  margin: 0;
  font-size: 30px;
}

.card-head p {
  margin: 5px 0 0;
  color: var(--muted);
  line-height: 1.35;
}

.tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 6px;
  border: 1px solid rgba(83, 137, 174, .18);
  border-radius: 10px;
  background: rgba(3, 17, 31, .58);
  margin-bottom: 22px;
}

.tabs button {
  height: 44px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--muted);
  font-weight: 800;
}

.tabs button.active {
  color: #062e31;
  background: linear-gradient(135deg, #13e0cf, #12bba5);
}

.form {
  display: grid;
  gap: 16px;
}

label span {
  display: block;
  margin-bottom: 8px;
  color: #d7e1ee;
  font-weight: 700;
}

input {
  width: 100%;
  height: 56px;
  padding: 0 16px;
  border-radius: 10px;
  border: 1px solid rgba(83, 137, 174, .22);
  background: rgba(3, 17, 31, .72);
  color: var(--text);
  outline: none;
}

input:focus {
  border-color: rgba(18, 230, 209, .62);
  box-shadow: 0 0 0 4px rgba(18, 230, 209, .08);
}

.err {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  color: #ffd6dc;
  border: 1px solid rgba(255, 93, 108, .35);
  background: rgba(255, 93, 108, .1);
  border-radius: 10px;
}

.submit {
  width: 100%;
  margin-top: 8px;
}

.switch-text {
  margin: 22px 0 0;
  color: var(--muted);
  text-align: center;
}

.switch-text a {
  color: var(--cyan);
  font-weight: 800;
}

@media (max-width: 1100px) {
  .login-shell {
    grid-template-columns: 1fr;
  }

  .login-story h1 {
    font-size: 46px;
  }
}

@media (max-width: 720px) {
  .login-page {
    padding: 18px;
  }

  .story-grid {
    grid-template-columns: 1fr;
  }
}
</style>
