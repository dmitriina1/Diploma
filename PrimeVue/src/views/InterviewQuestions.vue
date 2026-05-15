<template>
  <div class="page">
    <NavBar />
    <main class="screen narrow catalog">
      <section class="page-title">
        <div class="title-left">
          <div class="icon-box"><i class="pi pi-comments"></i></div>
          <div>
            <h1>Каталог вопросов</h1>
            <p>Фильтруйте по технологиям, уровню и сложности, чтобы найти подходящие вопросы для подготовки.</p>
          </div>
        </div>
      </section>

      <div class="toolbar">
        <input class="field search" placeholder="Поиск вопросов..." />
        <select class="field"><option>Все технологии</option></select>
        <select class="field"><option>Любая сложность</option></select>
        <select class="field"><option>По встречаемости</option></select>
      </div>

      <div class="meta-row">
        <span>12 458 вопросов найдено</span>
        <span>Обновлено сегодня <i class="dot"></i></span>
      </div>

      <section class="question-list">
        <router-link v-for="q in questions" :key="q.id" :to="`/question/${q.id}`" class="question-row glass">
          <span class="q-icon"><i :class="`pi ${q.icon}`"></i></span>
          <span class="q-main">
            <strong>{{ q.title }}</strong>
            <span><b class="tag">{{ q.topic }}</b><b :class="`tag ${q.level}`">{{ q.level }}</b></span>
          </span>
          <span class="q-score">
            <em>{{ q.frequency }}</em>
            <strong>{{ q.probability }}%</strong>
          </span>
          <i class="pi pi-angle-right chevron"></i>
        </router-link>
      </section>
    </main>
  </div>
</template>

<script setup>
import NavBar from '../components/NavBar.vue'
import { questions } from '../data/mock'
</script>

<style scoped>
.catalog { padding-top: 48px; }
.title-left { display: flex; gap: 20px; align-items: center; }
.title-left .icon-box { width: 72px; height: 72px; }
.toolbar { grid-template-columns: 2fr .96fr .9fr .78fr; margin-bottom: 24px; }
.search { padding-left: 62px; background-image: none; position: relative; }

.question-list { display: grid; gap: 8px; }
.question-row {
  min-height: 104px;
  display: grid;
  grid-template-columns: 76px 1fr 210px 34px;
  align-items: center;
  padding: 0 32px 0 24px;
  background: linear-gradient(90deg, rgba(10, 42, 67, .78), rgba(8, 31, 54, .84));
}
.q-icon {
  width: 62px;
  height: 62px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(18, 230, 209, .18);
  border-radius: var(--radius);
  color: var(--cyan);
  font-size: 28px;
  background: rgba(0, 229, 209, .035);
}
.q-main strong { display: block; font-size: 20px; margin-bottom: 12px; }
.q-main span { display: flex; gap: 10px; }
.q-score em { display: block; color: var(--cyan); font-style: normal; font-size: 16px; margin-bottom: 4px; }
.q-score strong { font-size: 30px; }
.chevron { color: var(--muted); font-size: 28px; }

@media (max-width: 900px) {
  .question-row { grid-template-columns: 62px 1fr; gap: 14px; padding: 18px; }
  .q-score, .chevron { display: none; }
}
</style>
