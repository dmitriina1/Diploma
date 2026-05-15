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
          <button class="btn primary"><i class="pi pi-refresh"></i>Обновить из HH сейчас</button>
        </div>
      </section>

      <section class="source glass">
        <b>Источник данных:</b>
        <label><input type="checkbox" checked /> Навыки</label>
        <label><input type="checkbox" checked /> Описание</label>
        <label><input type="checkbox" checked /> Заголовок</label>
      </section>

      <section class="professions">
        <button v-for="name in professions" :key="name" :class="{ active: name === 'Golang разработчик' }">{{ name }}</button>
        <button>Ещё <i class="pi pi-angle-down"></i></button>
      </section>

      <section class="glass skill-card">
        <header>
          <h2>Golang разработчик</h2>
          <span><i class="pi pi-briefcase"></i>≈ 2 800 вакансий</span>
          <span><i class="pi pi-star"></i>15 навыков</span>
          <em>Режим: Навыки + Описание + Заголовок</em>
        </header>
        <div class="skill-table">
          <div class="skill-head"><span>#</span><span>Навык</span><span>Упоминания в вакансиях</span><span>Вакансий</span></div>
          <div v-for="skill in skills" :key="skill.name" class="skill-row">
            <span>{{ skill.rank }}</span>
            <b>{{ skill.name }}</b>
            <div class="skill-bar"><i :style="{ width: skill.percent + '%' }"></i><strong>{{ skill.percent }}%</strong></div>
            <em>{{ skill.vacancies.toLocaleString('ru-RU') }}</em>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import NavBar from '../components/NavBar.vue'
import { professions, skills } from '../data/mock'
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

@media (max-width: 1100px) {
  .skill-card header, .skill-head, .skill-row { grid-template-columns: 42px 160px 1fr 90px; }
  .skill-card header { display: flex; flex-wrap: wrap; }
}
</style>
