<template>
  <div class="page recordings-page">
    <NavBar />
    <main class="screen recordings">
      <section class="page-title">
        <div>
          <h1>Загруженные собеседования</h1>
          <p>Ваши записи интервью и результаты анализа</p>
        </div>
        <button class="btn primary"><i class="pi pi-cloud-upload"></i>Загрузить запись</button>
      </section>

      <div class="records-grid">
        <aside>
          <input class="field" placeholder="Поиск по собеседованиям..." />
          <div class="side-head">Название собеседования</div>
          <button v-for="rec in recordings" :key="rec.id" class="rec-item" @click="modalOpen = true">
            <span><i class="pi pi-play"></i></span>
            <b>{{ rec.title }}</b>
            <small>{{ rec.role }}</small>
          </button>
        </aside>

        <section class="glass rec-table">
          <div class="table-row table-head">
            <span></span><span>Длительность</span><span>Дата <i class="pi pi-sort-alt"></i></span><span></span>
          </div>
          <div v-for="rec in recordings" :key="rec.id" class="table-row">
            <span></span><span>{{ rec.duration }}</span><span>{{ rec.date }}</span><button>...</button>
          </div>
          <footer><button class="page-arrow"><i class="pi pi-angle-left"></i></button><b>1</b><span>2</span><span>3</span><span>...</span><span>8</span><button class="page-arrow"><i class="pi pi-angle-right"></i></button></footer>
        </section>
      </div>
    </main>

    <div v-if="modalOpen" class="modal-layer" @click.self="modalOpen = false">
      <section class="modal neon-border">
        <button class="close" @click="modalOpen = false"><i class="pi pi-times"></i></button>
        <h2>Собеседование на Backend Developer</h2>
        <p>Запись от 23 мая 2025 <span>•</span> 54:32 <span>•</span> 12 вопросов</p>
        <div class="modal-list">
          <div v-for="q in extractedQuestions" :key="q.id">
            <b>{{ q.id }}</b>
            <span>{{ q.title }}</span>
            <em :class="`tag ${q.level}`">{{ q.level }}</em>
            <i class="pi pi-angle-down"></i>
          </div>
        </div>
        <footer><span><i class="pi pi-sparkles"></i>Вопросы выделены и сгенерированы AI. Возможны неточности.</span><button class="btn small"><i class="pi pi-copy"></i>Скопировать список</button></footer>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import NavBar from '../components/NavBar.vue'
import { recordings, extractedQuestions } from '../data/mock'

const modalOpen = ref(true)
</script>

<style scoped>
.recordings { padding-top: 34px; }
.records-grid { display: grid; grid-template-columns: 470px 1fr; gap: 42px; }
aside .field { height: 56px; margin-bottom: 20px; }
.side-head { color: var(--soft); text-transform: uppercase; font-size: 14px; font-weight: 800; margin: 0 0 18px 90px; }
.rec-item {
  width: 100%;
  min-height: 82px;
  display: grid;
  grid-template-columns: 58px 1fr;
  column-gap: 18px;
  align-items: center;
  text-align: left;
  border: 0;
  border-bottom: 1px solid rgba(83, 121, 148, .12);
  background: transparent;
  color: var(--text);
  padding: 0 0 0 18px;
}
.rec-item span { grid-row: span 2; width: 48px; height: 48px; display: grid; place-items: center; border: 1px solid rgba(18, 230, 209, .22); border-radius: var(--radius); color: var(--cyan); }
.rec-item b { font-size: 18px; }
.rec-item small { color: var(--muted); font-size: 16px; }
.rec-table { margin-top: 70px; }
.rec-table .table-row { grid-template-columns: 1fr 170px 170px 80px; min-height: 80px; padding: 0 26px; color: var(--muted); }
.rec-table button { background: none; border: 0; color: var(--muted); font-size: 24px; }
.rec-table footer { height: 90px; display: flex; justify-content: center; align-items: center; gap: 26px; color: var(--muted); }
.rec-table footer b { width: 42px; height: 42px; border-radius: 10px; display: grid; place-items: center; background: rgba(18, 230, 209, .28); color: var(--cyan); }
.page-arrow { width: 42px; height: 42px; border: 1px solid rgba(83, 121, 148, .16) !important; border-radius: 10px; }

.modal-layer { position: fixed; inset: 92px 0 0; display: grid; place-items: start center; padding-top: 18px; background: rgba(2, 13, 27, .28); z-index: 30; }
.modal {
  width: 835px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(5, 24, 44, .98), rgba(4, 23, 42, .98));
  padding: 28px 34px 18px;
  position: relative;
}
.close { position: absolute; right: 28px; top: 28px; background: none; border: 0; color: var(--muted); font-size: 24px; }
.modal h2 { margin: 0 0 8px; font-size: 28px; }
.modal p { margin: 0 0 24px; color: var(--muted); font-size: 18px; }
.modal p span { margin: 0 10px; }
.modal-list { display: grid; gap: 8px; }
.modal-list div {
  min-height: 54px;
  display: grid;
  grid-template-columns: 42px 1fr 92px 28px;
  align-items: center;
  gap: 16px;
  border: 1px solid rgba(83, 121, 148, .16);
  background: rgba(11, 42, 65, .72);
  border-radius: 10px;
  padding: 0 14px;
}
.modal-list b { width: 36px; height: 36px; display: grid; place-items: center; border-radius: 9px; background: rgba(18, 230, 209, .11); color: #b9f9f4; }
.modal-list span { font-size: 17px; }
.modal-list i { color: var(--muted); }
.modal footer { display: flex; justify-content: space-between; align-items: center; color: var(--muted); margin-top: 22px; }

@media (max-width: 1100px) {
  .records-grid { grid-template-columns: 1fr; }
  .modal { width: calc(100vw - 32px); }
}
</style>
