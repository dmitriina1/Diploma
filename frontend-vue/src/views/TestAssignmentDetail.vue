<template>
  <div class="ta-detail-page">
    <NavBar />
    <div class="ta-detail-container">
      <!-- Header -->
      <div class="ta-detail-header">
        <router-link to="/test-assignments" class="back-link">
          <i class="pi pi-arrow-left"></i>
          К заданиям
        </router-link>
      </div>

      <div v-if="loading" class="loading-state">
        <ProgressSpinner style="width: 50px; height: 50px" />
        <p>Загрузка задания...</p>
      </div>

      <div v-else-if="!assignment" class="empty-state">
        <i class="pi pi-exclamation-triangle"></i>
        <h3>Задание не найдено</h3>
        <router-link to="/test-assignments">Все задания</router-link>
      </div>

      <div v-else class="ta-content">
        <!-- Title & Meta -->
        <div class="ta-title-block">
          <h1>{{ assignment.title }}</h1>
          <div class="ta-meta">
            <Tag :value="assignment.difficulty" :severity="diffSeverity(assignment.difficulty)" class="meta-tag" />
            <span v-if="assignment.company" class="meta-company">
              <i class="pi pi-building"></i> {{ assignment.company }}
            </span>
            <span v-if="assignment.profession" class="meta-profession">
              <i class="pi pi-user"></i> {{ assignment.profession }}
            </span>
            <span v-if="assignment.source" class="meta-source">
              <i class="pi pi-link"></i> {{ assignment.source }}
            </span>
          </div>
        </div>

        <!-- Skills -->
        <div v-if="assignment.skills_list && assignment.skills_list.length" class="ta-skills">
          <h3><i class="pi pi-tags"></i> Навыки</h3>
          <div class="skills-list">
            <Tag v-for="skill in assignment.skills_list" :key="skill" :value="skill" 
                 severity="info" rounded class="skill-tag" />
          </div>
        </div>

        <!-- Description -->
        <div class="ta-description">
          <h3><i class="pi pi-align-left"></i> Описание</h3>
          <div class="desc-text" v-html="formattedDescription"></div>
        </div>

        <!-- Link -->
        <div v-if="assignment.link" class="ta-link-section">
          <Button label="Открыть задание" icon="pi pi-external-link" severity="info"
                  @click="openLink(assignment.link)" />
        </div>

        <!-- Date -->
        <div class="ta-date">
          Добавлено: {{ formatDate(assignment.created_at) }}
        </div>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import api from '../api/client'

const route = useRoute()
const assignment = ref(null)
const loading = ref(true)

const diffSeverity = (d) => ({ junior: 'success', middle: 'warning', senior: 'danger' }[d] || 'info')

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('ru-RU', { year: 'numeric', month: 'long', day: 'numeric' })
}

const formattedDescription = computed(() => {
  if (!assignment.value?.description) return ''
  return assignment.value.description
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
})

const openLink = (link) => window.open(link, '_blank')

onMounted(async () => {
  try {
    const r = await api.getTestAssignmentDetail(route.params.id)
    assignment.value = r.data
  } catch (e) {
    console.error('Failed to load assignment:', e)
  }
  loading.value = false
})
</script>

<style scoped>
.ta-detail-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
}
.ta-detail-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
  padding-top: 2rem;
}
.ta-detail-header {
  margin-bottom: 1.5rem;
}
.back-link {
  color: rgba(255,255,255,0.6);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
  transition: color 0.2s;
}
.back-link:hover { color: #60a5fa; }

.loading-state {
  text-align: center;
  padding: 4rem;
  color: rgba(255,255,255,0.5);
}
.empty-state {
  text-align: center;
  padding: 4rem;
  color: rgba(255,255,255,0.4);
}
.empty-state i { font-size: 3rem; display: block; margin-bottom: 1rem; color: #fa709a; }
.empty-state a { color: #60a5fa; text-decoration: none; }

.ta-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.ta-title-block h1 {
  font-size: 2rem;
  color: white;
  margin: 0 0 1rem 0;
  line-height: 1.3;
}
.ta-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
}
.meta-tag { font-size: 0.85rem; }
.meta-company, .meta-profession, .meta-source {
  color: rgba(255,255,255,0.6);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.ta-skills h3 {
  color: rgba(255,255,255,0.8);
  font-size: 1.1rem;
  margin: 0 0 0.75rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.ta-skills h3 i { color: #a78bfa; }
.skills-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.skill-tag { font-size: 0.85rem; }

.ta-description h3 {
  color: rgba(255,255,255,0.8);
  font-size: 1.1rem;
  margin: 0 0 0.75rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.ta-description h3 i { color: #60a5fa; }
.desc-text {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 1.5rem;
  color: rgba(255,255,255,0.85);
  line-height: 1.7;
  font-size: 0.95rem;
  white-space: pre-wrap;
  word-break: break-word;
}

.ta-link-section {
  display: flex;
}

.ta-date {
  color: rgba(255,255,255,0.35);
  font-size: 0.85rem;
  border-top: 1px solid rgba(255,255,255,0.06);
  padding-top: 1rem;
}

@media (max-width: 768px) {
  .ta-detail-container { padding: 1rem; }
  .ta-title-block h1 { font-size: 1.5rem; }
  .ta-meta { gap: 0.5rem; }
}
</style>
