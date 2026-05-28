<template>
  <div class="page skills-page">
    <NavBar />
    <main class="screen narrow skills">
      <section class="page-title">
        <div>
          <h1>Навыки</h1>
          <p>Аналитика востребованных навыков на рынке труда.<br />Данные обновляются автоматически из hh.ru</p>
        </div>
        <div class="sync">
          <span><i class="pi pi-info-circle"></i>Автообновление: примерно раз в 24 часа</span>
          <button class="btn primary" :disabled="syncing" @click="runSyncNow"><i class="pi pi-refresh"></i>{{ syncing ? 'Обновляем...' : 'Обновить из HH сейчас' }}</button>
        </div>
      </section>

      <section class="source glass">
        <b>Источник данных:</b>
        <label><input v-model="sources.skills" type="checkbox" @change="loadSkills" /> Навыки</label>
        <label><input v-model="sources.description" type="checkbox" @change="loadSkills" /> Описание</label>
        <label><input v-model="sources.title" type="checkbox" @change="loadSkills" /> Заголовок</label>
      </section>

      <section class="professions">
        <button v-for="name in professionNames" :key="name" :class="{ active: name === selected }" @click="selectProfession(name)">{{ name }}</button>
        <button>Ещё <i class="pi pi-angle-down"></i></button>
      </section>

      <section class="glass skill-card">
        <header>
          <h2>{{ selected }}</h2>
          <span><i class="pi pi-briefcase"></i>≈ {{ totalVacancies }} вакансий</span>
          <span><i class="pi pi-star"></i>{{ totalSkills }} навыков</span>
          <em>Режим: {{ activeSourceTitle }}</em>
        </header>
        <div class="skill-table">
          <div class="skill-head"><span>#</span><span>Навык</span><span>Упоминания в вакансиях</span><span>Вакансий</span></div>
          <div v-if="loading" class="empty-panel"><div class="loader"></div></div>
          <div v-for="skill in normalizedSkills" v-else :key="skill.name" class="skill-row">
            <span>{{ skill.rank }}</span>
            <b>{{ skill.name }}</b>
            <div class="skill-bar"><i :style="{ width: skill.percent + '%' }"></i><strong>{{ skill.percent }}%</strong></div>
            <em>{{ skill.vacancies.toLocaleString('ru-RU') }}</em>
          </div>
        </div>
      </section>

      <section class="learning-priorities glass">
        <header>
          <span class="kicker">Приоритет изучения</span>
          <h2>Что учить по направлению</h2>
          <p>Разделите навыки на обязательную базу, рекомендуемый слой и дополнительные темы. Так подготовка остаётся плотной, но не превращается в бесконечный список.</p>
        </header>
        <div class="priority-list">
          <article v-for="group in learningPriority" :key="group.title">
            <b :class="group.type">{{ group.label }}</b>
            <h3>{{ group.title }}</h3>
            <p>{{ group.text }}</p>
            <div>
              <span v-for="skill in group.skills" :key="skill">{{ skill }}</span>
            </div>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import NavBar from '../components/NavBar.vue'
import api from '../api/client'
import { professions as fallbackProfessions, skills as fallbackSkills } from '../data/mock'

const loading = ref(false)
const syncing = ref(false)
const professions = ref(fallbackProfessions.map((profession) => ({ profession })))
const skills = ref(fallbackSkills)
const selected = ref('Golang разработчик')
const totalSkills = ref(fallbackSkills.length)
const totalVacancies = ref('2 800')
const sources = ref({ skills: true, description: true, title: true })

const professionNames = computed(() => professions.value.map((p) => p.profession || p).slice(0, 16))
const activeSourceTitle = computed(() => [
  sources.value.skills && 'Навыки',
  sources.value.description && 'Описание',
  sources.value.title && 'Заголовок'
].filter(Boolean).join(' + ') || 'Навыки')
const normalizedSkills = computed(() => skills.value.map((item, index) => ({
  rank: item.rank || index + 1,
  name: item.name || item.skill,
  percent: Math.round(item.percent || item.percentage || 0),
  vacancies: item.vacancies || item.vacancy_count || 0
})))
const learningPriority = computed(() => {
  const top = normalizedSkills.value.slice(0, 12).map((skill) => skill.name)
  return [
    {
      type: 'must',
      label: 'Обязательно',
      title: 'Практический минимум',
      text: 'Эти навыки чаще всего формируют первые технические вопросы и должны быть уверенно проговорены вслух.',
      skills: top.slice(0, 4)
    },
    {
      type: 'recommended',
      label: 'Рекомендуется',
      title: 'Следующий уровень',
      text: 'Темы, которые повышают качество ответов и помогают показать практический опыт в проектах.',
      skills: top.slice(4, 8)
    },
    {
      type: 'optional',
      label: 'Можно позже',
      title: 'По ситуации',
      text: 'Имеет смысл учить после базы или если вакансия явно требует эти инструменты.',
      skills: top.slice(8, 12)
    }
  ]
})

function selectedSources() {
  const list = []
  if (sources.value.skills) list.push('skills')
  if (sources.value.description) list.push('description')
  if (sources.value.title) list.push('title')
  if (!list.length) {
    sources.value.skills = true
    list.push('skills')
  }
  return list.join(',')
}

async function selectProfession(name) {
  selected.value = name
  await loadSkills()
}

async function loadSkills() {
  loading.value = true
  try {
    const r = await api.getHHSkills(selected.value, 1, 30, selectedSources())
    const list = r.data.skills || []
    if (list.length) skills.value = list
    totalSkills.value = r.data.total || list.length || skills.value.length
    totalVacancies.value = (list[0]?.total_vacancies || 2800).toLocaleString('ru-RU')
  } catch {}
  loading.value = false
}

async function runSyncNow() {
  syncing.value = true
  try { await api.runHHSyncNow(); await loadSkills() } catch {}
  syncing.value = false
}

onMounted(async () => {
  try {
    const r = await api.getHHProfessions()
    if (r.data.professions?.length) {
      professions.value = r.data.professions
      selected.value = professions.value[0].profession
    }
  } catch {}
  await loadSkills()
})
</script>

<style scoped>
.skills { padding-top: 22px; }
.sync { display: grid; justify-items: end; gap: 20px; color: var(--muted); }
.source { min-height: 64px; display: flex; align-items: center; gap: 24px; padding: 0 24px; margin-bottom: 16px; font-size: 18px; }
.source input { accent-color: var(--cyan); width: 20px; height: 20px; vertical-align: middle; margin-right: 8px; }
.professions { display: flex; flex-wrap: wrap; gap: 12px 14px; margin-bottom: 18px; }
.professions button {
  height: 48px;
  padding: 0 24px;
  border: 1px solid rgba(83, 137, 174, .2);
  border-radius: var(--radius);
  background: rgba(8, 31, 54, .72);
  color: #e8edf5;
  font-size: 18px;
}
.professions .active { background: linear-gradient(135deg, #14d9c8, #0aa38f); border-color: transparent; }
.skill-card { padding: 26px 36px 28px; }
.skill-card header {
  display: grid;
  grid-template-columns: 1fr 230px 190px 360px;
  gap: 18px;
  align-items: center;
  border-bottom: 1px solid rgba(83, 121, 148, .12);
  padding-bottom: 18px;
}
.skill-card h2 { margin: 0; font-size: 32px; }
.skill-card header span, .skill-card header em { color: var(--muted); font-style: normal; font-size: 18px; }
.skill-table { min-height: 420px; }
.skill-head, .skill-row {
  display: grid;
  grid-template-columns: 42px 300px 1fr 120px;
  align-items: center;
  gap: 18px;
}
.skill-head { height: 56px; color: var(--muted); }
.skill-row { min-height: 39px; font-size: 18px; }
.skill-row > span, .skill-row em { color: var(--cyan); font-style: normal; }
.skill-bar { height: 22px; border-radius: 4px; background: rgba(11, 37, 58, .74); position: relative; }
.skill-bar i { display: block; height: 100%; background: linear-gradient(90deg, #18d4c0, #18c7a1); border-radius: inherit; }
.skill-bar strong { position: absolute; left: calc(var(--left, 0px) + 100%); top: 50%; transform: translate(14px, -50%); color: #e8edf5; }
.skill-row .skill-bar strong { left: auto; right: auto; margin-left: 14px; transform: translateY(-50%); }
.skill-row:nth-child(2) .skill-bar strong { left: 95%; }
.skill-row:nth-child(3) .skill-bar strong { left: 65%; }
.skill-row:nth-child(4) .skill-bar strong { left: 56%; }
.skill-row:nth-child(5) .skill-bar strong { left: 55%; }
.skill-row:nth-child(6) .skill-bar strong { left: 48%; }
.skill-row:nth-child(7) .skill-bar strong { left: 41%; }
.skill-row:nth-child(8) .skill-bar strong { left: 40%; }
.skill-row:nth-child(9) .skill-bar strong { left: 37%; }
.skill-row:nth-child(10) .skill-bar strong { left: 35%; }
.learning-priorities { margin-top: 18px; padding: 28px 32px; }
.kicker { color: var(--cyan); font-weight: 800; text-transform: uppercase; font-size: 13px; }
.learning-priorities header { display: grid; gap: 8px; margin-bottom: 22px; }
.learning-priorities h2 { margin: 0; font-size: 32px; letter-spacing: -.03em; }
.learning-priorities p { margin: 0; color: var(--muted); line-height: 1.55; }
.priority-list { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.priority-list article { padding: 22px; border: 1px solid rgba(83, 137, 174, .16); border-radius: var(--radius); background: rgba(3, 20, 37, .36); }
.priority-list b { display: inline-flex; padding: 7px 10px; border-radius: 8px; font-size: 13px; text-transform: uppercase; }
.priority-list b.must { color: var(--cyan); background: rgba(18, 230, 209, .12); }
.priority-list b.recommended { color: #62b7ff; background: rgba(0, 116, 207, .18); }
.priority-list b.optional { color: var(--yellow); background: rgba(226, 189, 0, .14); }
.priority-list h3 { margin: 18px 0 8px; font-size: 22px; }
.priority-list div { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
.priority-list span { padding: 7px 10px; border-radius: 8px; background: rgba(0, 116, 207, .18); color: #62b7ff; font-weight: 800; }

@media (max-width: 1100px) {
  .skill-card header, .skill-head, .skill-row { grid-template-columns: 42px 160px 1fr 90px; }
  .skill-card header { display: flex; flex-wrap: wrap; }
  .priority-list { grid-template-columns: 1fr; }
}
</style>
