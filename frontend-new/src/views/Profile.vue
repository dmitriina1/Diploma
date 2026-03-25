<template>
  <div class="page">
    <NavBar />
    <div class="container" style="padding-top:2rem;padding-bottom:3rem">
      <button class="btn btn-ghost btn-sm" @click="$router.push('/')" style="margin-bottom:1.25rem">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        На главную
      </button>
      <h1 class="sec-title h-page" style="margin-bottom:1.5rem;display:flex;align-items:center;gap:.5rem">
        <BrandIcon name="profile" :size="28" />
        Профиль
      </h1>

      <div v-if="loading" class="profile-card card">
        <div style="display:grid;grid-template-columns:100px 1fr;gap:1.5rem;width:100%">
          <div class="skeleton" style="width:100px;height:100px;border-radius:50%"></div>
          <div style="display:grid;gap:.6rem">
            <div class="skeleton-line lg"></div>
            <div class="skeleton-line" style="width:60%"></div>
            <div class="skeleton-line"></div>
          </div>
        </div>
      </div>

      <StatePanel
        v-else-if="loadError"
        icon="warning"
        type="error"
        title="Не удалось загрузить профиль"
        :description="loadError"
      >
        <button class="btn btn-secondary btn-sm" @click="reloadProfile">Повторить</button>
      </StatePanel>

      <template v-else>
        <!-- User Card -->
        <div class="profile-card card">
          <div class="avatar-col">
            <div class="avatar">
              <img v-if="profile.avatar_url" :src="profile.avatar_url" alt="" />
              <span v-else class="av-letter">{{ (profile.display_name || profile.username || '?')[0].toUpperCase() }}</span>
            </div>
            <span class="role-badge" :class="profile.role">{{ profile.role === 'admin' ? 'Админ' : 'Пользователь' }}</span>
          </div>
          <div class="info-col">
            <div class="field-row"><label>Имя</label><input v-model="form.display_name" class="input" placeholder="Ваше имя" /></div>
            <div class="field-row"><label>Логин</label><span class="static">{{ profile.username }}</span></div>
            <div class="field-row"><label>GitHub</label><input v-model="form.github_url" class="input" placeholder="https://github.com/you" /></div>
            <div class="field-row"><label>Аватар (URL)</label><input v-model="form.avatar_url" class="input" placeholder="https://..." /></div>
            <div class="field-row"><label>Регистрация</label><span class="static">{{ fmtDate(profile.created_at) }}</span></div>
            <div class="actions-row">
              <button class="btn btn-primary" @click="save" :disabled="saving">{{ saving ? 'Сохранение...' : 'Сохранить' }}</button>
              <span v-if="msg" class="save-msg" :class="msgType">{{ msg }}</span>
            </div>
          </div>
        </div>

        <!-- Stats -->
        <div v-if="profile.trainer_stats" class="stats-grid">
          <div class="stat-card card"><div class="sv">{{ profile.trainer_stats.total_cards || 0 }}</div><div class="sl">Карточек</div></div>
          <div class="stat-card card"><div class="sv">{{ profile.trainer_stats.reviewed || 0 }}</div><div class="sl">Повторено</div></div>
          <div class="stat-card card"><div class="sv">{{ profile.trainer_stats.avg_easiness || '—' }}</div><div class="sl">Лёгкость</div></div>
          <div class="stat-card card"><div class="sv">{{ (profile.bookmarks || []).length }}</div><div class="sl">Закладок</div></div>
        </div>

        <!-- GitHub -->
        <div v-if="profile.github_url" class="section card" style="margin-bottom:1.5rem">
          <h3 class="sec-title" style="font-size:1rem">GitHub</h3>
          <a :href="profile.github_url" target="_blank" rel="noopener" class="gh-link">{{ profile.github_url }}</a>
        </div>

        <!-- Bookmarks -->
        <div class="section">
          <h3 class="sec-title" style="font-size:1rem;margin-bottom:1rem">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg>
            Сохранённые вопросы
          </h3>
          <div v-if="!profile.bookmarks || profile.bookmarks.length === 0" class="empty">
            <p>Нет сохранённых вопросов</p>
            <router-link to="/interview-questions" class="link">Перейти к вопросам</router-link>
          </div>
          <div v-else class="bm-list">
            <router-link v-for="bm in profile.bookmarks" :key="bm.id" :to="'/question/' + bm.question_id" class="bm-card card card-hover">
              <div class="bm-tags">
                <span class="badge badge-info">{{ bm.topic }}</span>
                <span v-if="bm.difficulty" class="badge" :class="diffBadge(bm.difficulty)">{{ bm.difficulty }}</span>
              </div>
              <div class="bm-q">{{ bm.question }}</div>
               <div v-if="bm.note" class="bm-note">{{ bm.note }}</div>
              <div class="bm-date">{{ fmtDate(bm.created_at) }}</div>
            </router-link>
          </div>
        </div>
      </template>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../store/auth'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import BrandIcon from '../components/BrandIcon.vue'
import StatePanel from '../components/StatePanel.vue'
import api from '../api/client'

const auth = useAuthStore()
const loading = ref(true)
const saving = ref(false)
const msg = ref('')
const msgType = ref('ok')
const loadError = ref('')
const profile = reactive({ username: '', display_name: '', role: 'user', avatar_url: null, github_url: null, created_at: null, bookmarks: [], trainer_stats: null })
const form = reactive({ display_name: '', github_url: '', avatar_url: '' })

const diffBadge = (d) => ({ junior: 'badge-ok', middle: 'badge-warn', senior: 'badge-err' }[d] || 'badge-muted')
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }) : '—'

const reloadProfile = async () => {
  loadError.value = ''
  loading.value = true
  try {
    const r = await api.getProfile()
    Object.assign(profile, r.data)
    form.display_name = profile.display_name || ''
    form.github_url = profile.github_url || ''
    form.avatar_url = profile.avatar_url || ''
  } catch (e) { console.error(e); loadError.value = 'Сервис профиля недоступен, попробуй позже.' }
  loading.value = false
}

onMounted(reloadProfile)

async function save() {
  saving.value = true; msg.value = ''
  try {
    const r = await api.updateProfile({ display_name: form.display_name || null, github_url: form.github_url || null, avatar_url: form.avatar_url || null })
    Object.assign(profile, r.data)
    if (auth.user) { auth.user.display_name = r.data.display_name; auth.user.avatar_url = r.data.avatar_url; auth.user.github_url = r.data.github_url; localStorage.setItem('auth_user', JSON.stringify(auth.user)) }
    msg.value = 'Сохранено!'; msgType.value = 'ok'
  } catch { msg.value = 'Ошибка сохранения'; msgType.value = 'err' }
  saving.value = false; setTimeout(() => msg.value = '', 3000)
}
</script>

<style scoped>
.center-block { display: flex; justify-content: center; padding: 4rem; }
.profile-card { display: flex; gap: 2rem; padding: 2rem; margin-bottom: 1.5rem; }
.avatar-col { display: flex; flex-direction: column; align-items: center; gap: .6rem; }
.avatar {
  width: 100px; height: 100px; border-radius: 50%;
  background: linear-gradient(135deg, var(--c-brand), var(--c-brand-h));
  display: flex; align-items: center; justify-content: center;
  border: 3px solid var(--c-border); overflow: hidden;
}
.avatar img { width: 100%; height: 100%; object-fit: cover; }
.av-letter { font-size: 2.5rem; font-weight: 700; color: #fff; }
.role-badge { padding: .2rem .75rem; border-radius: var(--r-full); font-size: .76rem; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; }
.role-badge.admin { background: var(--c-warn-bg); color: var(--c-warn); }
.role-badge.user { background: var(--c-brand-bg); color: var(--c-brand-h); }
.info-col { flex: 1; display: flex; flex-direction: column; gap: .9rem; }
.field-row { display: flex; align-items: center; gap: 1rem; }
.field-row label { min-width: 120px; font-size: .85rem; color: var(--c-text-3); font-weight: 600; }
.static { color: var(--c-text-2); font-size: .92rem; }
.actions-row { display: flex; align-items: center; gap: .75rem; margin-top: .25rem; }
.save-msg { font-size: .82rem; font-weight: 600; }
.save-msg.ok { color: var(--c-ok); }
.save-msg.err { color: var(--c-err); }

.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: .75rem; margin-bottom: 1.5rem; }
.stat-card { text-align: center; padding: 1.1rem; }
.sv { font-size: 1.75rem; font-weight: 800; color: var(--c-text); }
.sl { font-size: .78rem; color: var(--c-text-4); text-transform: uppercase; letter-spacing: .5px; margin-top: .15rem; }
.section { margin-bottom: 1.5rem; }
.gh-link { color: var(--c-brand); text-decoration: none; word-break: break-all; }
.gh-link:hover { text-decoration: underline; }
.empty { text-align: center; padding: 2.5rem; color: var(--c-text-4); border: 1px dashed var(--c-border); border-radius: var(--r-md); }
.link { color: var(--c-brand); text-decoration: none; font-weight: 600; }
.bm-list { display: flex; flex-direction: column; gap: .5rem; }
.bm-card { display: block; padding: 1rem 1.15rem; text-decoration: none; }
.bm-tags { display: flex; gap: .35rem; margin-bottom: .4rem; }
.bm-q { color: var(--c-text); font-size: .96rem; line-height: 1.4; margin-bottom: .35rem; }
.bm-note { color: var(--c-text-3); font-size: .84rem; font-style: italic; margin-bottom: .2rem; }
.bm-date { color: var(--c-text-4); font-size: .78rem; }

@media (max-width: 640px) {
  .profile-card { flex-direction: column; align-items: center; text-align: center; }
  .field-row { flex-direction: column; align-items: stretch; gap: .2rem; }
  .field-row label { min-width: unset; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
