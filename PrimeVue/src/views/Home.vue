<template>
  <div class="page home-page">
    <NavBar />
    <main class="screen home-screen">
      <section class="hero">
        <div class="hero-copy">
          <h1>Готовьтесь к IT-собеседованиям <span>структурно</span> и без хаоса</h1>
          <p>Upskill извлекает вопросы из реальных интервью и видео, структурирует их в единую базу и помогает уверенно отвечать через SM-2, mock-и AI-практику.</p>
          <div class="hero-actions">
            <router-link to="/interview-questions" class="btn primary"><i class="pi pi-arrow-right"></i>Начать подготовку</router-link>
            <router-link to="/trainer" class="btn"><i class="pi pi-play-circle"></i>Открыть тренажёр</router-link>
          </div>
        </div>

        <div class="hero-visual" aria-hidden="true">
          <div class="orb one"></div>
          <div class="orb two"></div>
          <div class="float-card chat"><i class="pi pi-comments"></i></div>
          <div class="float-card award"><i class="pi pi-star"></i></div>
          <div class="float-card code"><i class="pi pi-code"></i></div>
          <div class="float-card play"><i class="pi pi-play"></i></div>
          <div class="progress-card">
            <span>Подготовка</span>
            <strong>92%</strong>
            <div class="curve"><span></span></div>
            <small>Твой прогресс</small>
          </div>
        </div>
      </section>

      <section class="chips">
        <p>Тренируйтесь по технологиям:</p>
        <div>
          <span v-for="chip in chips" :key="chip"><i class="pi pi-circle"></i>{{ chip }}</span>
          <span>...</span>
        </div>
      </section>

      <section class="why glass">
        <header>
          <h2>Почему <span>Upskill</span> ускоряет подготовку</h2>
          <p>Не просто список вопросов, а система, которая доводит до уверенного ответа на собеседовании.</p>
        </header>
        <div class="why-grid">
          <article v-for="item in reasons" :key="item.title">
            <div class="icon-box"><i :class="item.icon"></i></div>
            <div>
              <h3>{{ item.title }}</h3>
              <p>{{ item.text }}</p>
            </div>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import NavBar from '../components/NavBar.vue'

const chips = ['System Design', 'SRE', 'Security', 'Product', 'Team Lead', 'Cloud', 'Backend', 'Frontend', 'Fullstack', 'QA', 'Data Scientist', 'Data Analyst', 'ML Engineer']
const reasons = [
  { title: 'Актуальная база', text: 'Вопросы из реальных интервью и видео обновляются ежедневно.', icon: 'pi pi-database' },
  { title: 'AI-практика', text: 'Mock-интервью с ИИ: обратная связь, подсказки и рекомендации.', icon: 'pi pi-microchip-ai' },
  { title: 'Структурная подготовка', text: 'Spaced repetition и трекер прогресса по темам и навыкам.', icon: 'pi pi-crosshairs' },
  { title: 'Фокус на навыках', text: 'Аналитика по слабым местам помогает выявлять пробелы и расти.', icon: 'pi pi-chart-bar' }
]
</script>

<style scoped>
.home-screen { padding-top: 46px; }

.hero {
  min-height: 520px;
  display: grid;
  grid-template-columns: 1.08fr .92fr;
  align-items: center;
  gap: 60px;
}

.hero-copy h1 {
  margin: 0;
  max-width: 900px;
  font-size: 58px;
  line-height: 1.2;
  letter-spacing: -.045em;
}

.hero-copy h1 span { color: var(--cyan); }
.hero-copy p { max-width: 650px; margin: 28px 0 34px; color: var(--muted); font-size: 22px; line-height: 1.55; }
.hero-actions { display: flex; gap: 26px; }

.hero-visual {
  position: relative;
  min-height: 440px;
}

.orb {
  position: absolute;
  border-radius: 50%;
  border: 5px solid rgba(18, 230, 209, .35);
  filter: drop-shadow(0 0 28px rgba(18, 230, 209, .16));
}
.orb.one { width: 250px; height: 250px; right: 130px; top: 20px; }
.orb.two { width: 195px; height: 195px; right: 60px; bottom: 20px; border-color: rgba(28, 114, 190, .25); }

.float-card, .progress-card {
  position: absolute;
  border: 1px solid rgba(39, 210, 229, .32);
  background: linear-gradient(145deg, rgba(8, 55, 78, .78), rgba(5, 21, 42, .92));
  box-shadow: 0 28px 80px rgba(0, 0, 0, .35), inset 0 1px 0 rgba(255, 255, 255, .06);
  border-radius: 18px;
}

.float-card {
  width: 88px;
  height: 88px;
  display: grid;
  place-items: center;
  color: var(--cyan);
  font-size: 34px;
  transform: rotate(4deg);
}
.chat { left: 110px; top: 90px; }
.award { left: 50px; top: 240px; color: #c8d6ef; transform: rotate(8deg); }
.code { right: 155px; top: 120px; color: #19caff; }
.play { right: 80px; bottom: 115px; color: #7aa7ff; }

.progress-card {
  left: 230px;
  top: 130px;
  width: 290px;
  height: 235px;
  padding: 34px 30px;
  transform: perspective(700px) rotateY(-15deg) rotateX(4deg);
}
.progress-card span, .progress-card small { color: var(--muted); font-size: 17px; }
.progress-card strong { display: block; margin-top: 28px; font-size: 38px; }
.curve { height: 78px; margin-top: 18px; background: linear-gradient(180deg, rgba(18, 230, 209, .48), rgba(18, 230, 209, .02)); border-radius: 60% 40% 0 0; position: relative; }
.curve span { position: absolute; right: 28px; top: -4px; width: 10px; height: 10px; border-radius: 50%; background: white; box-shadow: 0 0 20px var(--cyan); }

.chips { margin: 10px 0 30px; }
.chips p { margin: 0 0 10px; color: var(--muted); }
.chips div { display: flex; gap: 8px; flex-wrap: wrap; }
.chips span {
  height: 43px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  border: 1px solid rgba(74, 137, 178, .22);
  border-radius: var(--radius);
  background: rgba(4, 21, 38, .65);
  color: #c3cfde;
  font-size: 14px;
}
.chips i { color: #61b9ff; font-size: 13px; }

.why { padding: 34px 28px 42px; }
.why header { text-align: center; margin-bottom: 34px; }
.why h2 { margin: 0; font-size: 31px; letter-spacing: -.03em; }
.why h2 span { color: var(--cyan); }
.why header p { margin: 10px 0 0; color: var(--muted); font-size: 17px; }
.why-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 34px; }
.why article { display: grid; grid-template-columns: 96px 1fr; gap: 18px; align-items: center; }
.why h3 { margin: 0 0 10px; font-size: 20px; }
.why article p { margin: 0; color: var(--muted); line-height: 1.55; }

@media (max-width: 1200px) {
  .hero { grid-template-columns: 1fr; }
  .hero-visual { display: none; }
  .why-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 720px) {
  .home-screen { padding-top: 32px; }
  .hero-copy h1 { font-size: 38px; }
  .hero-copy p { font-size: 17px; }
  .hero-actions { flex-direction: column; }
  .why-grid { grid-template-columns: 1fr; }
}
</style>
