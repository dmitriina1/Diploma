<template>
  <div class="page detail-page">
    <NavBar />
    <main class="screen narrow detail">
      <router-link to="/interview-questions" class="back"><i class="pi pi-arrow-left"></i>Назад к списку вопросов</router-link>
      <h1>Почему вы выбрали именно нашу компанию?</h1>
      <div class="detail-tags">
        <span class="tag">Общие вопросы</span>
        <span class="tag junior">Junior</span>
        <span class="tag ok"><i class="pi pi-bullseye"></i>100% вероятность</span>
      </div>

      <section class="glass block answer">
        <h2><i class="pi pi-comment"></i>Ответ</h2>
        <div class="answer-box">
          <p>Меня привлекает ваша компания тем, что вы создаёте продукты, которые решают реальные задачи пользователей и приносят ощутимую ценность.</p>
          <p>Я разделяю ваши ценности: ориентацию на качество, постоянное развитие и открытость к новым идеям.</p>
          <p>Вижу здесь возможности для профессионального роста, интересные задачи и сильную команду, у которой можно учиться и вместе достигать большего.</p>
          <p>Я хочу внести свой вклад в развитие продуктов компании и помогать достигать амбициозных целей.</p>
        </div>
      </section>

      <section class="glass block">
        <h2><i class="pi pi-youtube"></i>Видео с этим вопросом</h2>
        <div class="video-row" v-for="video in videos" :key="video.title">
          <span><i class="pi pi-play"></i>{{ video.title }}</span>
          <b :class="video.source === 'YouTube' ? 'youtube' : 'rutube'">{{ video.source === 'YouTube' ? '▶' : 'R' }}</b>
          <span>{{ video.source }}</span>
          <time>{{ video.time }}</time>
          <a>Перейти к фрагменту <i class="pi pi-external-link"></i></a>
        </div>
      </section>

      <section class="glass block note">
        <h2><i class="pi pi-pencil"></i>Моя заметка</h2>
        <textarea placeholder="Добавьте личную заметку или важные тезисы по этому вопросу..."></textarea>
        <span>0 / 1000</span>
      </section>

      <section class="glass block community">
        <h2><i class="pi pi-users"></i>Ответы сообщества</h2>
        <div>
          <input placeholder="Поделитесь своим ответом или советом для сообщества..." />
          <button class="btn small">Опубликовать</button>
        </div>
      </section>

      <section class="glass block feedback">
        <h2><i class="pi pi-link"></i>Обратная связь</h2>
        <div>
          <button class="btn small"><i class="pi pi-thumbs-up"></i>Полезно <i class="pi pi-angle-down"></i></button>
          <input placeholder="Что понравилось?" />
          <span>0 / 500</span>
          <button class="btn small">Отправить</button>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import NavBar from '../components/NavBar.vue'

const videos = [
  { title: 'Собеседование на Backend Developer', source: 'YouTube', time: '12:34' },
  { title: 'Mock interview. Java Developer', source: 'Rutube', time: '08:52' },
  { title: 'Интервью на Frontend Developer', source: 'YouTube', time: '16:41' }
]
</script>

<style scoped>
.detail { padding-top: 16px; max-width: 1570px; }
.back { display: inline-flex; gap: 10px; color: var(--muted); font-weight: 700; margin: 0 0 10px; }
h1 { margin: 0; font-size: 32px; letter-spacing: -.03em; }
.detail-tags { display: flex; gap: 12px; margin: 18px 0 24px; }
.block { padding: 16px 18px 20px; margin-bottom: 12px; }
.block h2 { margin: 0 0 14px; display: flex; gap: 12px; align-items: center; font-size: 21px; }
.block h2 i { color: var(--cyan); }
.answer-box {
  border: 1px solid rgba(91, 132, 159, .13);
  border-left: 3px solid var(--cyan);
  border-radius: 8px;
  padding: 16px 22px;
  background: rgba(3, 20, 36, .42);
}
.answer-box p { margin: 0 0 18px; color: #d7dee8; line-height: 1.6; }
.answer-box p:last-child { margin-bottom: 0; }
.video-row {
  min-height: 48px;
  display: grid;
  grid-template-columns: 1fr 24px 140px 100px 220px;
  align-items: center;
  border-bottom: 1px solid rgba(91, 132, 159, .1);
  color: #d7dee8;
}
.video-row:last-child { border-bottom: 0; }
.video-row span:first-child { display: flex; gap: 12px; align-items: center; }
.video-row span:first-child i { color: var(--muted); }
.youtube { color: red; }
.rutube { color: #d1b377; }
.video-row a { color: var(--cyan); font-weight: 700; }
textarea, input {
  width: 100%;
  border: 1px solid rgba(91, 132, 159, .15);
  border-radius: 8px;
  background: rgba(4, 20, 37, .62);
  color: var(--text);
  outline: none;
}
textarea { height: 62px; padding: 16px; resize: none; }
.note { position: relative; }
.note span { position: absolute; right: 26px; bottom: 25px; color: var(--muted); }
.community div, .feedback div { display: grid; gap: 12px; align-items: center; }
.community div { grid-template-columns: 1fr 160px; }
.feedback div { grid-template-columns: 280px 1fr 80px 160px; }
input { height: 48px; padding: 0 16px; }
.feedback span { color: var(--muted); }

@media (max-width: 900px) {
  .video-row, .community div, .feedback div { grid-template-columns: 1fr; gap: 10px; padding: 12px 0; }
}
</style>
