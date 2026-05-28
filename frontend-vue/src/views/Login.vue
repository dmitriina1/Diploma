<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <router-link to="/" class="back-link">
          <i class="pi pi-arrow-left"></i>
          На главную
        </router-link>
        <div class="login-logo">
          <i class="pi pi-bookmark"></i>
          <h1>Interview Prep</h1>
        </div>
        <p class="login-subtitle">{{ isRegisterMode ? 'Создайте аккаунт' : 'Войдите в аккаунт' }}</p>
      </div>

      <div class="login-tabs">
        <button 
          class="tab-btn" 
          :class="{ active: !isRegisterMode }"
          @click="switchMode(false)"
        >
          Вход
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: isRegisterMode }"
          @click="switchMode(true)"
        >
          Регистрация
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="form-group">
          <label for="username">Логин</label>
          <InputText 
            id="username"
            v-model="username" 
            placeholder="Введите логин"
            :class="{ 'p-invalid': error }"
            autocomplete="username"
          />
        </div>

        <div v-if="isRegisterMode" class="form-group">
          <label for="displayName">Имя (необязательно)</label>
          <InputText 
            id="displayName"
            v-model="displayName" 
            placeholder="Как вас называть?"
            autocomplete="name"
          />
        </div>

        <div class="form-group">
          <label for="password">Пароль</label>
          <InputText 
            id="password"
            v-model="password" 
            type="password" 
            placeholder="Введите пароль"
            :class="{ 'p-invalid': error }"
            autocomplete="current-password"
          />
        </div>

        <Message v-if="error" severity="error" :closable="false" class="error-message">
          {{ error }}
        </Message>

        <Button 
          type="submit" 
          :label="isRegisterMode ? 'Зарегистрироваться' : 'Войти'"
          :icon="isRegisterMode ? 'pi pi-user-plus' : 'pi pi-sign-in'"
          class="submit-btn"
          :loading="loading"
        />
      </form>

      <div class="login-info">
        <p v-if="!isRegisterMode">
          Нет аккаунта? 
          <a href="#" @click.prevent="switchMode(true)">Зарегистрируйтесь</a>
        </p>
        <p v-else>
          Уже есть аккаунт? 
          <a href="#" @click.prevent="switchMode(false)">Войдите</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isRegisterMode = ref(false)
const username = ref('')
const password = ref('')
const displayName = ref('')

const loading = computed(() => authStore.loading)
const error = computed(() => authStore.error)

function switchMode(register) {
  isRegisterMode.value = register
  authStore.clearError()
}

async function handleSubmit() {
  if (!username.value || !password.value) {
    authStore.error = 'Заполните логин и пароль'
    return
  }

  let success = false
  if (isRegisterMode.value) {
    success = await authStore.register(username.value, password.value, displayName.value || null)
  } else {
    success = await authStore.login(username.value, password.value)
  }

  if (success) {
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f0f1e;
  padding: 2rem;
}

.login-container {
  width: 100%;
  max-width: 440px;
  background: linear-gradient(145deg, rgba(26, 26, 46, 0.95), rgba(15, 15, 30, 0.95));
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 20px;
  padding: 2.5rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: rgba(255, 255, 255, 0.5);
  text-decoration: none;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
  transition: color 0.3s;
}

.back-link:hover {
  color: #667eea;
}

.login-logo {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 0.5rem;
}

.login-logo i {
  font-size: 2rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.login-logo h1 {
  font-size: 1.8rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.login-subtitle {
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 1.5rem;
}

.login-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 1.5rem;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.tab-btn {
  flex: 1;
  padding: 0.75rem 1rem;
  border: none;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.tab-btn.active {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.tab-btn:hover:not(.active) {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.form-group label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  font-weight: 500;
}

.form-group :deep(.p-inputtext) {
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(102, 126, 234, 0.2);
  color: #e4e4e7;
  font-size: 1rem;
}

.form-group :deep(.p-inputtext:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.form-group :deep(.p-inputtext.p-invalid) {
  border-color: #ef4444;
}

.error-message {
  margin: 0;
}

.submit-btn {
  width: 100%;
  padding: 0.85rem;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  margin-top: 0.5rem;
}

.submit-btn:hover {
  background: linear-gradient(135deg, #7c8ef7 0%, #8a5bb5 100%);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.login-info {
  text-align: center;
  margin-top: 1.5rem;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
}

.login-info a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
}

.login-info a:hover {
  color: #7c8ef7;
  text-decoration: underline;
}
</style>
