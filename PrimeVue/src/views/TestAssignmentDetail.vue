<template>
  <div class="page">
    <NavBar />
    <div class="container" style="padding-top:2rem;padding-bottom:3rem">
      <router-link to="/test-assignments" class="btn btn-ghost btn-sm" style="margin-bottom:1.25rem">← К заданиям</router-link>

      <div v-if="loading" class="center-block"><div class="spinner"></div></div>
      <div v-else-if="!a" class="empty-state">
        <p>Задание не найдено</p>
        <router-link to="/test-assignments" class="link">Все задания</router-link>
      </div>

      <template v-else>
        <h1 class="title">{{ a.title }}</h1>
        <div class="meta">
          <span class="badge" :class="diffBadge(a.difficulty)">{{ a.difficulty }}</span>
          <span v-if="a.company" class="meta-item">{{ a.company }}</span>
          <span v-if="a.profession" class="meta-item">{{ a.profession }}</span>
          <span v-if="a.source" class="meta-item">{{ a.source }}</span>
        </div>

        <div v-if="a.skills_list?.length" class="section">
          <h3 class="sec-title" style="font-size:1rem">Навыки</h3>
          <div class="skills-wrap"><span v-for="s in a.skills_list" :key="s" class="badge badge-info">{{ s }}</span></div>
        </div>

        <div class="section">
          <h3 class="sec-title" style="font-size:1rem">Описание</h3>
          <div class="desc card" v-html="fmtDesc"></div>
        </div>

        <div v-if="a.link" class="section">
          <a :href="a.link" target="_blank" class="btn btn-primary">Открыть задание ↗</a>
        </div>

        <div class="date">Добавлено: {{ fmtDate(a.created_at) }}</div>
      </template>
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
const a = ref(null)
const loading = ref(true)
const diffBadge = (d) => ({ junior: 'badge-ok', middle: 'badge-warn', senior: 'badge-err' }[d] || 'badge-muted')
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU', { year: 'numeric', month: 'long', day: 'numeric' }) : ''
const fmtDesc = computed(() => a.value?.description?.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>') || '')

onMounted(async () => {
  try { const r = await api.getTestAssignmentDetail(route.params.id); a.value = r.data } catch (e) { console.error(e) }
  loading.value = false
})
</script>

<style scoped>
.center-block { display: flex; justify-content: center; padding: 4rem; }
.empty-state { text-align: center; padding: 4rem; color: var(--c-text-4); }
.link { color: var(--c-brand); text-decoration: none; font-weight: 600; }
.title { font-size: 1.85rem; font-weight: 500; margin-bottom: 1rem; line-height: 1.2; letter-spacing: -.025em; }
.meta { display: flex; flex-wrap: wrap; align-items: center; gap: .75rem; margin-bottom: 1.5rem; }
.meta-item { color: var(--c-text-3); font-size: .94rem; display: flex; align-items: center; gap: .3rem; }
.section { margin-bottom: 1.5rem; }
.skills-wrap { display: flex; flex-wrap: wrap; gap: .4rem; }
.desc { padding: 1.25rem; color: var(--c-text-2); line-height: 1.7; font-size: 1rem; white-space: pre-wrap; word-break: break-word; }
.date { color: var(--c-text-4); font-size: .88rem; border-top: 1px solid var(--c-border); padding-top: .75rem; }
</style>
