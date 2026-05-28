<template>
  <div class="profile-page">
    <NavBar />
    <div class="profile-container">
      <!-- Header -->
      <div class="profile-header">
        <router-link to="/" class="back-link">
          <i class="pi pi-arrow-left"></i>
          На главную
        </router-link>
        <h1><i class="pi pi-user"></i> Профиль</h1>
      </div>

      <div v-if="loading" class="loading-state">
        <ProgressSpinner style="width: 50px; height: 50px" />
        <p>Загрузка профиля...</p>
      </div>

      <div v-else class="profile-content">
        <!-- User Card -->
        <div class="profile-card">
          <div class="avatar-section">
            <div class="avatar" @click="showAvatarDialog = true" title="Изменить аватар">
              <img v-if="profile.avatar_url" :src="profile.avatar_url" alt="Avatar" class="avatar-img" />
              <i v-else class="pi pi-user avatar-placeholder"></i>
              <div class="avatar-overlay">
                <i class="pi pi-camera"></i>
              </div>
            </div>
            <div class="user-badge" :class="profile.role">
              {{ profile.role === 'admin' ? 'Администратор' : 'Пользователь' }}
            </div>
          </div>

          <div class="info-section">
            <div class="info-row">
              <label>Имя</label>
              <div class="editable-field">
                <InputText 
                  v-model="editForm.display_name" 
                  placeholder="Ваше имя"
                  class="profile-input"
                />
              </div>
            </div>

            <div class="info-row">
              <label>Логин</label>
              <div class="static-field">{{ profile.username }}</div>
            </div>

            <div class="info-row">
              <label><i class="pi pi-github"></i> GitHub</label>
              <div class="editable-field">
                <InputText 
                  v-model="editForm.github_url" 
                  placeholder="https://github.com/username"
                  class="profile-input"
                />
              </div>
            </div>

            <div class="info-row">
              <label>Аватар (URL)</label>
              <div class="editable-field">
                <InputText 
                  v-model="editForm.avatar_url" 
                  placeholder="https://example.com/photo.jpg"
                  class="profile-input"
                />
              </div>
            </div>

            <div class="info-row">
              <label>Дата регистрации</label>
              <div class="static-field">{{ formatDate(profile.created_at) }}</div>
            </div>

            <div class="actions-row">
              <button class="save-btn" @click="saveProfile" :disabled="saving">
                <i class="pi" :class="saving ? 'pi-spin pi-spinner' : 'pi-check'"></i>
                {{ saving ? 'Сохранение...' : 'Сохранить' }}
              </button>
              <span v-if="saveMessage" class="save-message" :class="saveMessageType">
                {{ saveMessage }}
              </span>
            </div>
          </div>
        </div>

        <!-- Stats -->
        <div class="stats-grid" v-if="profile.trainer_stats">
          <div class="stat-card">
            <i class="pi pi-bolt"></i>
            <div class="stat-value">{{ profile.trainer_stats.total_cards || 0 }}</div>
            <div class="stat-label">Карточек в тренажёре</div>
          </div>
          <div class="stat-card">
            <i class="pi pi-check-circle"></i>
            <div class="stat-value">{{ profile.trainer_stats.reviewed || 0 }}</div>
            <div class="stat-label">Повторено</div>
          </div>
          <div class="stat-card">
            <i class="pi pi-star"></i>
            <div class="stat-value">{{ profile.trainer_stats.avg_easiness || '—' }}</div>
            <div class="stat-label">Средняя лёгкость</div>
          </div>
          <div class="stat-card">
            <i class="pi pi-bookmark"></i>
            <div class="stat-value">{{ (profile.bookmarks || []).length }}</div>
            <div class="stat-label">Закладок</div>
          </div>
        </div>

        <!-- GitHub Link Preview -->
        <div v-if="profile.github_url" class="github-section">
          <h2><i class="pi pi-github"></i> GitHub</h2>
          <a :href="profile.github_url" target="_blank" rel="noopener noreferrer" class="github-link">
            <i class="pi pi-external-link"></i>
            {{ profile.github_url }}
          </a>
        </div>

        <!-- Bookmarks -->
        <div class="bookmarks-section">
          <h2><i class="pi pi-bookmark"></i> Сохранённые вопросы</h2>
          <div v-if="!profile.bookmarks || profile.bookmarks.length === 0" class="empty-state">
            <i class="pi pi-bookmark"></i>
            <p>Нет сохранённых вопросов</p>
            <router-link to="/interview-questions" class="action-link">Перейти к вопросам</router-link>
          </div>
          <div v-else class="bookmarks-list">
            <router-link 
              v-for="bm in profile.bookmarks" 
              :key="bm.id" 
              :to="`/question/${bm.question_id}`" 
              class="bookmark-card"
            >
              <div class="bookmark-topic">
                <Tag :value="bm.topic" severity="info" />
                <Tag v-if="bm.difficulty" :value="difficultyLabel(bm.difficulty)" :severity="difficultySeverity(bm.difficulty)" />
              </div>
              <div class="bookmark-question">{{ bm.question }}</div>
              <div v-if="bm.note" class="bookmark-note">
                <i class="pi pi-pencil"></i> {{ bm.note }}
              </div>
              <div class="bookmark-date">{{ formatDate(bm.created_at) }}</div>
            </router-link>
          </div>
        </div>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../store/auth'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import api from '../api/client'

const authStore = useAuthStore()

const loading = ref(true)
const saving = ref(false)
const saveMessage = ref('')
const saveMessageType = ref('success')

const profile = reactive({
  id: null,
  username: '',
  display_name: '',
  role: 'user',
  avatar_url: null,
  github_url: null,
  created_at: null,
  bookmarks: [],
  trainer_stats: null
})

const editForm = reactive({
  display_name: '',
  github_url: '',
  avatar_url: ''
})

onMounted(async () => {
  await loadProfile()
})

async function loadProfile() {
  loading.value = true
  try {
    const res = await api.getProfile()
    Object.assign(profile, res.data)
    editForm.display_name = profile.display_name || ''
    editForm.github_url = profile.github_url || ''
    editForm.avatar_url = profile.avatar_url || ''
  } catch (e) {
    console.error('Failed to load profile:', e)
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  saving.value = true
  saveMessage.value = ''
  try {
    const res = await api.updateProfile({
      display_name: editForm.display_name || null,
      github_url: editForm.github_url || null,
      avatar_url: editForm.avatar_url || null
    })
    Object.assign(profile, res.data)
    
    // Update auth store & localStorage with new display_name
    if (authStore.user) {
      authStore.user.display_name = res.data.display_name
      authStore.user.avatar_url = res.data.avatar_url
      authStore.user.github_url = res.data.github_url
      localStorage.setItem('auth_user', JSON.stringify(authStore.user))
    }
    
    saveMessage.value = 'Профиль сохранён!'
    saveMessageType.value = 'success'
  } catch (e) {
    saveMessage.value = 'Ошибка сохранения'
    saveMessageType.value = 'error'
  } finally {
    saving.value = false
    setTimeout(() => { saveMessage.value = '' }, 3000)
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
}

function difficultyLabel(d) {
  const map = { junior: 'Junior', middle: 'Middle', senior: 'Senior' }
  return map[d] || d
}

function difficultySeverity(d) {
  const map = { junior: 'success', middle: 'warning', senior: 'danger' }
  return map[d] || 'info'
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0c29, #1a1a3e, #24243e);
}

.profile-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
  padding-top: 2rem;
}

.profile-header {
  margin-bottom: 2rem;
}

.profile-header h1 {
  color: white;
  font-size: 2rem;
  margin-top: 1rem;
}

.profile-header h1 i {
  margin-right: 0.5rem;
  color: #a78bfa;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.3s;
}

.back-link:hover {
  color: white;
}

.loading-state {
  text-align: center;
  padding: 4rem;
  color: rgba(255, 255, 255, 0.6);
}

/* Profile Card */
.profile-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 2rem;
  display: flex;
  gap: 2rem;
  margin-bottom: 2rem;
  backdrop-filter: blur(10px);
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  border: 3px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s;
}

.avatar:hover {
  border-color: rgba(255, 255, 255, 0.5);
  transform: scale(1.05);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.avatar-placeholder {
  font-size: 3rem;
  color: rgba(255, 255, 255, 0.7);
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
  border-radius: 50%;
}

.avatar:hover .avatar-overlay {
  opacity: 1;
}

.avatar-overlay i {
  color: white;
  font-size: 1.5rem;
}

.user-badge {
  padding: 0.3rem 1rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.user-badge.admin {
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  color: white;
}

.user-badge.user {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.info-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.info-row label {
  min-width: 140px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 600;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.static-field {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.95rem;
}

.editable-field {
  flex: 1;
}

.profile-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  color: white !important;
  border-radius: 8px !important;
  padding: 0.5rem 0.75rem !important;
  font-size: 0.9rem !important;
}

.profile-input:focus {
  border-color: #667eea !important;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) !important;
}

.actions-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.5rem;
}

.save-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.5rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.save-message {
  font-size: 0.85rem;
  font-weight: 600;
}

.save-message.success {
  color: #10b981;
}

.save-message.error {
  color: #ef4444;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.25rem;
  text-align: center;
  transition: all 0.3s;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateY(-2px);
}

.stat-card i {
  font-size: 1.5rem;
  color: #a78bfa;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 800;
  color: white;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* GitHub Section */
.github-section {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.github-section h2 {
  color: white;
  font-size: 1.1rem;
  margin-bottom: 1rem;
}

.github-section h2 i {
  margin-right: 0.5rem;
}

.github-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: #a78bfa;
  text-decoration: none;
  font-size: 0.95rem;
  transition: color 0.3s;
  word-break: break-all;
}

.github-link:hover {
  color: #c4b5fd;
}

/* Bookmarks Section */
.bookmarks-section {
  margin-bottom: 2rem;
}

.bookmarks-section h2 {
  color: white;
  font-size: 1.2rem;
  margin-bottom: 1rem;
}

.bookmarks-section h2 i {
  margin-right: 0.5rem;
  color: #a78bfa;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.empty-state i {
  font-size: 2.5rem;
  color: rgba(255, 255, 255, 0.2);
  margin-bottom: 1rem;
}

.empty-state p {
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 1rem;
}

.action-link {
  color: #a78bfa;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.3s;
}

.action-link:hover {
  color: #c4b5fd;
}

.bookmarks-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.bookmark-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  text-decoration: none;
  transition: all 0.3s;
  display: block;
}

.bookmark-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(102, 126, 234, 0.3);
  transform: translateX(4px);
}

.bookmark-topic {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.bookmark-question {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.95rem;
  line-height: 1.4;
  margin-bottom: 0.5rem;
}

.bookmark-note {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.8rem;
  font-style: italic;
  margin-bottom: 0.25rem;
}

.bookmark-note i {
  font-size: 0.7rem;
  margin-right: 0.25rem;
}

.bookmark-date {
  color: rgba(255, 255, 255, 0.3);
  font-size: 0.75rem;
}

/* Responsive */
@media (max-width: 768px) {
  .profile-card {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .info-row {
    flex-direction: column;
    align-items: stretch;
    gap: 0.25rem;
  }

  .info-row label {
    min-width: unset;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
