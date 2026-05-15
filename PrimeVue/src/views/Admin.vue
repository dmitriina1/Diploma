<template>
  <div class="page admin-page">
    <NavBar />
    <main class="screen admin">
      <section class="complete glass neon-border">
        <div class="check"><i class="pi pi-check"></i></div>
        <div>
          <h1>Обработка видео завершена</h1>
          <p>Все вопросы успешно извлечены и готовы к использованию</p>
          <button><i class="pi pi-chart-line"></i>Показать детали обработки <i class="pi pi-angle-down"></i></button>
        </div>
        <div class="summary"><span>Источник</span><b><em>▶</em>YouTube</b></div>
        <div class="summary"><span>Длительность</span><b>19:04</b></div>
        <div class="summary"><span>Обработано</span><b>19.04.2024, 10:37</b></div>
        <div class="complete-actions">
          <button class="btn"><i class="pi pi-play-circle"></i>Открыть в плеере</button>
          <button class="btn">Ещё действия <i class="pi pi-angle-down"></i></button>
        </div>
      </section>

      <nav class="tabs">
        <a class="active">Вопросы</a><a>Предложения</a><a>Обратная связь</a><a>Видео</a><a>Тестовые задания</a><a>Аналитика</a>
      </nav>

      <section class="admin-tools">
        <button class="btn primary"><i class="pi pi-sparkles"></i>Массовая генерация ответов</button>
        <div class="toolbar">
          <input class="field" placeholder="Поиск по вопросам..." />
          <select class="field"><option>Все темы</option></select>
          <select class="field"><option>Все статусы</option></select>
          <button class="btn"><i class="pi pi-filter"></i>Фильтры</button>
        </div>
      </section>

      <section class="glass admin-table">
        <div class="table-row table-head">
          <span><input type="checkbox" /></span><span>Вопрос</span><span>Тема</span><span>Сложность</span><span>Уверенность</span><span>Статус</span><span>Ответ</span><span>Действия</span>
        </div>
        <div v-for="(row, index) in rows" :key="row.title" class="table-row">
          <span><input type="checkbox" /></span>
          <span>{{ row.title }}</span>
          <span><b :class="row.topic === 'General' ? 'tag purple' : 'tag'">{{ row.topic }}</b></span>
          <span><b :class="`tag ${row.level}`">{{ row.level }}</b></span>
          <span class="confidence">{{ row.conf }}% <i class="progress-line"><span :style="{ width: row.conf + '%' }"></span></i></span>
          <span><b :class="`tag ${row.status ? 'ok' : 'middle'}`">{{ row.status ? 'Да' : 'Нет' }}</b></span>
          <span>{{ row.answer ? 'Есть' : '—' }}</span>
          <span class="row-actions"><button>{{ index < 2 ? 'Снять' : 'Одобрить' }}</button><button class="danger"><i class="pi pi-trash"></i></button></span>
        </div>
      </section>
      <footer class="admin-footer"><span>Показано 1–7 из 7 вопросов</span><span>Показывать по <b>25</b></span></footer>
    </main>
  </div>
</template>

<script setup>
import NavBar from '../components/NavBar.vue'

const rows = [
  { title: 'Почему вы выбрали именно нашу компанию?', topic: 'Общие вопросы', level: 'junior', conf: 100, status: true, answer: true },
  { title: 'Чем вы занимаетесь на текущем месте работы?', topic: 'Общие вопросы', level: 'junior', conf: 100, status: true, answer: true },
  { title: 'Как вы считаете, почему мы должны выбрать именно вас?', topic: 'General', level: 'junior', conf: 50, status: false, answer: false },
  { title: 'Расскажите о ваших хобби.', topic: 'General', level: 'junior', conf: 50, status: false, answer: false },
  { title: 'Сколько тоненьных магий поместится в автобусе?', topic: 'General', level: 'middle', conf: 50, status: false, answer: false },
  { title: 'Вы допускаете, что на рассматриваемой вакансии придётся...', topic: 'General', level: 'junior', conf: 50, status: false, answer: false },
  { title: 'Кем вы видите себя через пять лет?', topic: 'General', level: 'junior', conf: 50, status: false, answer: false }
]
</script>

<style scoped>
.admin { padding-top: 26px; }
.complete {
  min-height: 198px;
  display: grid;
  grid-template-columns: 120px 1fr 160px 170px 250px 230px;
  gap: 28px;
  align-items: center;
  padding: 34px 40px;
}
.check { width: 88px; height: 88px; border: 4px solid var(--cyan); border-radius: 50%; display: grid; place-items: center; color: var(--cyan); font-size: 42px; box-shadow: 0 0 28px rgba(18, 230, 209, .25); }
.complete h1 { margin: 0 0 10px; font-size: 26px; }
.complete p, .summary span { color: var(--muted); margin: 0; }
.complete button:not(.btn) { margin-top: 24px; background: transparent; border: 0; color: var(--cyan); font-weight: 700; }
.summary b { display: block; margin-top: 10px; font-size: 17px; }
.summary em { color: red; font-style: normal; margin-right: 8px; }
.complete-actions { display: grid; gap: 26px; }
.tabs { display: flex; gap: 44px; height: 82px; align-items: end; border-bottom: 1px solid rgba(83, 121, 148, .14); margin-bottom: 24px; }
.tabs a { height: 52px; color: var(--muted); font-weight: 700; }
.tabs .active { color: var(--cyan); border-bottom: 3px solid var(--cyan); }
.admin-tools { display: flex; justify-content: space-between; align-items: center; gap: 36px; margin-bottom: 22px; }
.admin-tools .toolbar { flex: 1; grid-template-columns: 1.1fr .5fr .5fr auto; margin: 0; }
.admin-tools .field { height: 52px; }
.admin-table .table-row { grid-template-columns: 52px 1.7fr .55fr .52fr .65fr .42fr .42fr .78fr; min-height: 68px; padding: 0 24px; }
.confidence { display: flex; align-items: center; gap: 14px; }
.row-actions { display: flex; gap: 14px; justify-content: flex-end; }
.row-actions button { height: 42px; min-width: 92px; border-radius: 8px; background: rgba(3, 39, 56, .66); color: var(--cyan); border: 1px solid rgba(18, 230, 209, .35); font-weight: 700; }
.row-actions .danger { min-width: 42px; color: var(--red); border-color: rgba(255, 93, 108, .6); }
.admin-footer { display: flex; justify-content: space-between; color: var(--muted); padding-top: 14px; }
.admin-footer b { color: var(--text); border: 1px solid rgba(83, 121, 148, .16); padding: 12px 28px; border-radius: 10px; margin-left: 16px; }

@media (max-width: 1300px) {
  .complete { grid-template-columns: 90px 1fr 1fr; }
  .admin-table { overflow-x: auto; }
  .admin-table .table-row { min-width: 1300px; }
}
</style>
