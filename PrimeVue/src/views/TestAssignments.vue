<template>
  <div class="page assignments-page">
    <NavBar />
    <main class="screen narrow assignments">
      <div class="toolbar assignment-toolbar">
        <select class="field"><option>Все профессии</option></select>
        <select class="field"><option>Любая сложность</option></select>
        <input class="field" placeholder="Поиск заданий, компаний, технологий..." />
      </div>
      <div class="meta-row">
        <span>Найдено 126 заданий</span>
        <span><i class="pi pi-sort-alt"></i> Сначала новые <i class="pi pi-angle-down"></i></span>
      </div>

      <section class="assignment-grid">
        <article v-for="item in assignments" :key="item.id" class="assignment-card glass" :class="item.level">
          <header>
            <span :class="`tag ${item.level}`">{{ item.level }}</span>
            <div class="company"><span>{{ item.company }}</span><b>{{ item.logo }}</b></div>
          </header>
          <h2>{{ item.title }}</h2>
          <p>{{ item.text }}</p>
          <small>{{ item.role }}</small>
          <div class="tags">
            <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
          <footer><router-link :to="`/test-assignments/${item.id}`">Подробнее <i class="pi pi-arrow-right"></i></router-link><time>18 апр. 2026 г.</time></footer>
        </article>
      </section>
      <div class="pagination"><button><i class="pi pi-angle-left"></i></button><b>1</b><span>2</span><span>3</span><span>...</span><span>9</span><button><i class="pi pi-angle-right"></i></button></div>
    </main>
  </div>
</template>

<script setup>
import NavBar from '../components/NavBar.vue'
import { assignments } from '../data/mock'
</script>

<style scoped>
.assignments { padding-top: 28px; }
.assignment-toolbar { grid-template-columns: .9fr .96fr 1.2fr; margin-bottom: 28px; }
.assignment-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.assignment-card {
  min-height: 330px;
  padding: 22px 24px 0;
  display: flex;
  flex-direction: column;
  border-left: 3px solid transparent;
}
.assignment-card.junior { border-left-color: var(--cyan); }
.assignment-card.middle { border-left-color: var(--yellow); }
.assignment-card.senior { border-left-color: var(--red); }
.assignment-card header, .assignment-card footer { display: flex; justify-content: space-between; align-items: center; gap: 18px; }
.company { display: flex; align-items: center; gap: 10px; font-weight: 800; }
.company b { width: 44px; height: 44px; border-radius: 50%; display: grid; place-items: center; background: #ff3f2d; color: white; font-size: 18px; }
.assignment-card:nth-child(2) .company b { background: #111; border: 4px solid #3ad45b; }
.assignment-card:nth-child(3) .company b { background: #1687ff; }
.assignment-card:nth-child(4) .company b { background: #ffd629; color: #111; }
.assignment-card:nth-child(5) .company b { background: #b815d0; }
.assignment-card:nth-child(6) .company b { background: #ff1b2d; }
.assignment-card h2 { margin: 28px 0 12px; font-size: 25px; letter-spacing: -.03em; }
.assignment-card p { margin: 0 0 20px; color: var(--muted); font-size: 18px; line-height: 1.45; }
.assignment-card small { color: #cdd6e3; font-size: 17px; margin-bottom: 18px; }
.tags { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }
.assignment-card footer {
  margin: auto -24px 0;
  min-height: 54px;
  padding: 0 24px;
  border-top: 1px solid rgba(83, 121, 148, .14);
  color: var(--muted);
}
.assignment-card footer a { color: #dbe3ef; font-weight: 800; }
.pagination { display: flex; justify-content: center; align-items: center; gap: 18px; margin-top: 28px; color: var(--muted); }
.pagination button, .pagination b, .pagination span { width: 45px; height: 45px; display: grid; place-items: center; border-radius: 8px; border: 1px solid rgba(83, 121, 148, .16); }
.pagination b { background: linear-gradient(135deg, var(--cyan), #0aa894); color: white; }

@media (max-width: 1100px) {
  .assignment-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 720px) {
  .assignment-grid { grid-template-columns: 1fr; }
  .assignment-toolbar { grid-template-columns: 1fr; }
}
</style>
