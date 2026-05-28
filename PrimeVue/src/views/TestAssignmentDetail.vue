<template>
  <div class="page">
    <NavBar />
    <div class="screen narrow assignment-detail">
      <router-link to="/test-assignments" class="back-link"><i class="pi pi-arrow-left"></i>К заданиям</router-link>

      <div v-if="loading" class="center-block"><div class="spinner"></div></div>
      <div v-else-if="!a" class="empty-state">
        <p>Задание не найдено</p>
        <router-link to="/test-assignments" class="link">Все задания</router-link>
      </div>

      <template v-else>
        <section class="detail-hero glass" :class="a.difficulty">
          <div>
            <span class="tag" :class="a.difficulty">{{ levelLabel(a.difficulty) }}</span>
            <h1 class="title">{{ a.title }}</h1>
            <p>{{ a.summary }}</p>
          </div>
          <div class="company-badge" :style="companyStyle(a.company)">
            <span>{{ a.company }}</span>
            <b>{{ logoText(a) }}</b>
          </div>
        </section>

        <div class="meta">
          <span class="tag" :class="a.difficulty">{{ levelLabel(a.difficulty) }}</span>
          <span v-if="a.company" class="meta-item"><i class="pi pi-building"></i>{{ a.company }}</span>
          <span v-if="a.profession" class="meta-item"><i class="pi pi-user"></i>{{ a.profession }}</span>
          <span v-if="a.source" class="meta-item"><i class="pi pi-link"></i>{{ a.source }}</span>
        </div>

        <div v-if="a.skills_list?.length" class="section">
          <h3 class="sec-title">Навыки</h3>
          <div class="skills-wrap"><span v-for="s in a.skills_list" :key="s" class="tag">{{ s }}</span></div>
        </div>

        <div class="section">
          <h3 class="sec-title">Описание</h3>
          <div class="desc glass" v-html="fmtDesc"></div>
        </div>

        <div v-if="a.link" class="section">
          <a :href="a.link" target="_blank" class="btn btn-primary">Открыть задание ↗</a>
        </div>

        <div class="date">Добавлено: {{ fmtDate(a.created_at) }}</div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from '../components/NavBar.vue'
import api from '../api/client'
import { assignments as fallbackAssignments } from '../data/mock'

const route = useRoute()
const a = ref(null)
const loading = ref(true)
const levelLabel = (level) => ({ junior: 'Junior', middle: 'Middle', senior: 'Senior' }[level] || level)
const logoText = (item) => {
  const logo = String(item?.logo || '').replace(/[^\p{L}\p{N}✓]/gu, '')
  const company = String(item?.company || 'IH').replace(/[^\p{L}\p{N}]/gu, '')
  return (logo || company || 'IH').slice(0, 2).toUpperCase()
}
const companyPalette = ['#ff4d3d', '#111827', '#1687ff', '#ffd629', '#7c3aed', '#ef233c', '#0ea5e9', '#12b981', '#f97316', '#2563eb']
const companyStyle = (company = '') => {
  const code = [...company].reduce((sum, char) => sum + char.charCodeAt(0), 0)
  const bg = companyPalette[code % companyPalette.length]
  return { '--logo-bg': bg, '--logo-color': bg === '#ffd629' ? '#111827' : '#fff' }
}
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU', { year: 'numeric', month: 'long', day: 'numeric' }) : ''
const fmtDesc = computed(() => a.value?.description?.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>') || '')
const demoAssignments = [
  ['demo-1', 'Интерактивная доска задач на Vue', 'Ozon', 'OZ', 'Frontend разработчик', 'junior', ['Vue', 'Pinia', 'CSS'], 'Собрать kanban-доску с drag-and-drop, фильтрами и сохранением состояния.'],
  ['demo-2', 'API бронирования переговорок', 'Авито', 'A', 'Backend разработчик', 'middle', ['Python', 'FastAPI', 'PostgreSQL'], 'Реализовать сервис бронирования с конфликтами времени и ролями пользователей.'],
  ['demo-3', 'Сервис уведомлений', 'Яндекс', 'Я', 'Backend разработчик', 'middle', ['Go', 'Kafka', 'Redis'], 'Спроектировать отправку email/push-уведомлений с очередью и повторными попытками.'],
  ['demo-4', 'Дашборд продаж', 'СБЕР', '✓', 'Data Analyst', 'junior', ['SQL', 'Python', 'BI'], 'Подготовить витрины данных и визуализацию ключевых метрик продаж.'],
  ['demo-5', 'Автотесты для формы оплаты', 'VK', 'vk', 'QA инженер', 'junior', ['Playwright', 'TypeScript', 'API'], 'Покрыть критический путь оплаты UI и API-тестами.'],
  ['demo-6', 'Инфраструктура staging', 'МТС', '●', 'DevOps инженер', 'middle', ['Docker', 'Nginx', 'CI/CD'], 'Настроить окружение staging с деплоем по веткам и health-check.'],
  ['demo-7', 'Рекомендательная модель', 'Wildberries', 'WB', 'Data Scientist', 'middle', ['Python', 'pandas', 'ML'], 'Построить baseline рекомендаций и объяснить метрики качества.'],
  ['demo-8', 'Поиск по каталогу товаров', 'Т-Банк', 'T', 'Backend разработчик', 'middle', ['Elasticsearch', 'Java', 'REST'], 'Реализовать полнотекстовый поиск с фильтрами, сортировкой и подсказками.'],
  ['demo-9', 'Личный кабинет кандидата', 'HH', 'HH', 'Frontend разработчик', 'middle', ['React', 'TypeScript', 'Forms'], 'Собрать кабинет с профилем, загрузкой файлов и валидацией форм.'],
  ['demo-10', 'План нагрузочного тестирования', 'Ростелеком', 'RT', 'QA инженер', 'middle', ['JMeter', 'SQL', 'Monitoring'], 'Подготовить профиль нагрузки, сценарии и отчёт по bottleneck в API.'],
  ['demo-11', 'Сервис коротких ссылок', '2ГИС', '2G', 'Backend разработчик', 'junior', ['Node.js', 'Redis', 'PostgreSQL'], 'Сделать генерацию коротких ссылок, статистику переходов и TTL.'],
  ['demo-12', 'Мобильный экран избранного', 'Самокат', 'S', 'Frontend разработчик', 'junior', ['Vue', 'Responsive', 'API'], 'Сверстать адаптивный экран с состояниями загрузки, пустым списком и ошибками.'],
  ['demo-13', 'ML pipeline для классификации', 'МегаФон', 'MF', 'Data Scientist', 'senior', ['Python', 'Airflow', 'MLflow'], 'Описать и реализовать pipeline обучения, валидации и версионирования модели.'],
  ['demo-14', 'Observability для микросервиса', 'Selectel', 'SL', 'DevOps инженер', 'senior', ['Prometheus', 'Grafana', 'Tracing'], 'Подключить метрики, алерты, трассировку и dashboard для production-сервиса.'],
  ['demo-15', 'Парсер вакансий и отчёт', 'Хабр', 'H', 'Data Analyst', 'junior', ['Python', 'SQL', 'Charts'], 'Собрать данные, очистить их и подготовить отчёт по востребованным навыкам.']
].map((item) => ({ id: item[0], title: item[1], company: item[2], logo: item[3], profession: item[4], difficulty: item[5], skills_list: item[6], description: item[7], summary: item[7], created_at: '2026-04-18' }))
const fallbackById = computed(() => {
  const base = fallbackAssignments.map((item) => ({ id: String(item.id), title: item.title, company: item.company, logo: item.logo || item.company?.slice(0, 2), profession: item.role, difficulty: item.level, skills_list: item.tags, description: item.text, summary: item.text, created_at: '2026-04-18' }))
  return [...base, ...demoAssignments].find((item) => String(item.id) === String(route.params.id))
})

onMounted(async () => {
  try { const r = await api.getTestAssignmentDetail(route.params.id); a.value = r.data } catch (e) { a.value = fallbackById.value || null }
  loading.value = false
})
</script>

<style scoped>
.assignment-detail { padding-top: 34px; padding-bottom: 60px; }
.back-link { display: inline-flex; align-items: center; gap: 8px; margin-bottom: 18px; color: var(--cyan); font-weight: 800; }
.center-block { display: flex; justify-content: center; padding: 4rem; }
.empty-state { text-align: center; padding: 4rem; color: var(--c-text-4); }
.link { color: var(--c-brand); text-decoration: none; font-weight: 600; }
.detail-hero { min-height: 250px; display: flex; justify-content: space-between; gap: 32px; padding: 34px 36px; border-left: 3px solid var(--cyan); overflow: hidden; }
.detail-hero.middle { border-left-color: var(--yellow); }
.detail-hero.senior { border-left-color: var(--red); }
.detail-hero > div:first-child { min-width: 0; }
.detail-hero p { max-width: 820px; color: var(--muted); font-size: 20px; line-height: 1.55; }
.title { font-size: 42px; font-weight: 800; margin: 18px 0 12px; line-height: 1.15; letter-spacing: -.03em; }
.company-badge { flex: 0 0 auto; align-self: start; display: flex; align-items: center; justify-content: flex-end; gap: 14px; font-weight: 800; }
.company-badge span { max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 18px; order: 1; }
.company-badge b { width: 70px; height: 70px; flex: 0 0 70px; border-radius: 50%; display: grid; place-items: center; background: var(--logo-bg); color: var(--logo-color); border: 1px solid rgba(255,255,255,.16); font-size: 22px; line-height: 1; letter-spacing: 0; overflow: hidden; order: 2; }
.meta { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin: 16px 0 28px; }
.meta-item { min-height: 34px; display: inline-flex; align-items: center; gap: 8px; padding: 0 12px; border: 1px solid rgba(83, 121, 148, .16); border-radius: 8px; background: rgba(4, 20, 37, .52); color: var(--muted); font-size: 15px; font-weight: 700; }
.meta-item i { color: var(--cyan); font-size: 13px; }
.section { margin-bottom: 26px; }
.sec-title { margin: 0 0 12px; font-size: 20px; }
.skills-wrap { display: flex; flex-wrap: wrap; gap: 9px; }
.desc { padding: 24px; color: #d8e2ef; line-height: 1.7; font-size: 18px; white-space: pre-wrap; word-break: break-word; }
.date { color: var(--muted); font-size: 15px; border-top: 1px solid rgba(83, 121, 148, .14); padding-top: 18px; }

@media (max-width: 760px) {
  .detail-hero { display: grid; }
  .company-badge { justify-items: start; }
  .title { font-size: 32px; }
}
</style>
