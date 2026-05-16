<template>
  <div class="page home-page">
    <NavBar />
    <main class="screen home-screen">
      <section class="hero fade-up">
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
            <strong>{{ stats.ready }}%</strong>
            <div class="curve"><span></span></div>
            <small>Твой прогресс</small>
          </div>
        </div>
      </section>

      <section class="chips">
        <p>Тренируйтесь по технологиям:</p>
        <div>
          <router-link v-for="chip in chips" :key="chip" class="tech-chip" :to="{ path: '/interview-questions', query: { topic: chip } }"><i class="pi pi-circle"></i>{{ chip }}</router-link>
          <router-link to="/hh-requirements" class="tech-chip">...</router-link>
        </div>
      </section>

      <section class="why glass">
        <header>
          <h2>Почему <span>Upskill</span> ускоряет подготовку</h2>
          <p>Не просто список вопросов, а система, которая доводит до уверенного ответа на собеседовании.</p>
        </header>
        <div class="why-grid stagger">
          <router-link v-for="item in reasons" :key="item.title" :to="item.to" class="reason-card">
            <div class="icon-box"><i :class="item.icon"></i></div>
            <div>
              <h3>{{ item.title }}</h3>
              <p>{{ item.text }}</p>
            </div>
          </router-link>
        </div>
      </section>

      <section class="product-flow">
        <article class="flow-copy">
          <span class="kicker">Пайплайн</span>
          <h2>Видео превращается в учебную базу</h2>
          <p>Скачивание аудио, транскрибация Whisper, извлечение вопросов LLM, дедупликация и сохранение в PostgreSQL остаются рабочим сценарием проекта.</p>
          <div class="steps">
            <button v-for="(step, index) in pipeline" :key="step.title" @click="activeStep = index" :class="{ active: activeStep === index }">
              <b>{{ index + 1 }}</b>
              <span>{{ step.title }}</span>
            </button>
          </div>
        </article>
        <aside class="flow-preview">
          <div class="preview-orbit"></div>
          <div class="preview-card">
            <i :class="pipeline[activeStep].icon"></i>
            <h3>{{ pipeline[activeStep].title }}</h3>
            <p>{{ pipeline[activeStep].text }}</p>
            <router-link :to="pipeline[activeStep].to" class="btn small">Открыть раздел</router-link>
          </div>
        </aside>
      </section>

      <section class="metrics-band">
        <header>
          <div>
            <span class="kicker">Состояние платформы</span>
            <h2>Состояние платформы</h2>
          </div>
          <button class="btn small" @click="loadStats"><i class="pi pi-refresh"></i>Обновить</button>
        </header>
        <div class="stats-grid">
          <article><span>Вопросов</span><strong>{{ stats.questions }}</strong><small>в каталоге</small></article>
          <article><span>Видео</span><strong>{{ stats.videos }}</strong><small>обработано</small></article>
          <article><span>Навыков HH</span><strong>{{ stats.skills }}</strong><small>в аналитике</small></article>
          <article><span>Заданий</span><strong>{{ stats.assignments }}</strong><small>для практики</small></article>
        </div>
      </section>

      <section class="usecases">
        <div class="section-row">
          <div>
            <span class="kicker">Сценарии</span>
            <h2>Рабочие сценарии</h2>
          </div>
          <router-link to="/interview-questions" class="quiet-link">Начать с каталога <i class="pi pi-arrow-right"></i></router-link>
        </div>
        <div class="usecase-grid stagger">
          <router-link v-for="item in usecases" :key="item.title" :to="item.to" class="usecase-card">
            <i :class="item.icon"></i>
            <h3>{{ item.title }}</h3>
            <p>{{ item.text }}</p>
          </router-link>
        </div>
      </section>

      <section class="roadmap glass">
        <div class="section-row">
          <div>
            <span class="kicker">План подготовки</span>
            <h2>Маршрут подготовки на 14 дней</h2>
          </div>
          <router-link to="/trainer" class="quiet-link">Открыть тренажёр <i class="pi pi-arrow-right"></i></router-link>
        </div>
        <div class="roadmap-grid">
          <article v-for="item in roadmap" :key="item.period" class="roadmap-card">
            <span>{{ item.period }}</span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.text }}</p>
            <div>
              <b v-for="tag in item.tags" :key="tag">{{ tag }}</b>
            </div>
          </article>
        </div>
      </section>

      <section class="home-workspace">
        <article class="latest-panel">
          <div class="section-row compact">
            <div>
              <span class="kicker">Лента вопросов</span>
              <h2>Свежие вопросы</h2>
            </div>
            <router-link to="/interview-questions" class="quiet-link">Все вопросы <i class="pi pi-arrow-right"></i></router-link>
          </div>
          <div class="question-list">
            <router-link v-for="question in latestQuestions" :key="question.title" to="/interview-questions" class="question-row">
              <i :class="question.icon"></i>
              <div>
                <h3>{{ question.title }}</h3>
                <p>{{ question.topic }} · {{ question.level }}</p>
              </div>
              <strong>{{ question.score }}%</strong>
            </router-link>
          </div>
        </article>

        <article class="practice-panel">
          <div class="pulse-ring"><i class="pi pi-bolt"></i></div>
          <span class="kicker">Фокус на сегодня</span>
          <h2>Сессия на сегодня</h2>
          <p>Короткая практика: повторить слабые карточки, разобрать один вопрос вслух и закрепить ответ в заметках.</p>
          <div class="practice-plan">
            <span><b>18</b> карточек</span>
            <span><b>3</b> вопроса</span>
            <span><b>1</b> mock</span>
          </div>
          <router-link to="/trainer" class="btn primary">Начать сессию</router-link>
        </article>
      </section>

      <section class="source-cta glass">
        <div>
          <span class="kicker">Видео в базу знаний</span>
          <h2>Пополняйте базу реальными интервью</h2>
          <p>Загрузите ссылку на запись: система скачает аудио, выполнит транскрибацию, извлечёт вопросы и подготовит их для модерации.</p>
        </div>
        <div class="source-actions">
          <router-link to="/admin" class="btn primary"><i class="pi pi-cloud-upload"></i>Загрузить видео</router-link>
          <router-link to="/recordings" class="btn"><i class="pi pi-video"></i>Смотреть записи</router-link>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import NavBar from '../components/NavBar.vue'
import api from '../api/client'

const activeStep = ref(0)
const stats = ref({ questions: '12 458', videos: '384', skills: '1 260', assignments: '126', ready: 92 })

const chips = ['System Design', 'SRE', 'Security', 'Product', 'Team Lead', 'Cloud', 'Backend', 'Frontend', 'Fullstack', 'QA', 'Data Scientist', 'Data Analyst', 'ML Engineer']
const reasons = [
  { title: 'Актуальная база', text: 'Вопросы из реальных интервью и видео обновляются ежедневно.', icon: 'pi pi-database', to: '/interview-questions' },
  { title: 'AI-практика', text: 'Mock-интервью с ИИ: обратная связь, подсказки и рекомендации.', icon: 'pi pi-comments', to: '/ai-interview' },
  { title: 'Структурная подготовка', text: 'Spaced repetition и трекер прогресса по темам и навыкам.', icon: 'pi pi-sync', to: '/trainer' },
  { title: 'Фокус на навыках', text: 'Аналитика по слабым местам помогает выявлять пробелы и расти.', icon: 'pi pi-chart-bar', to: '/hh-requirements' }
]
const pipeline = [
  { title: 'Загрузка', text: 'Администратор отправляет ссылку или файл, а пайплайн запускает обработку и показывает прогресс.', icon: 'pi pi-cloud-upload', to: '/admin' },
  { title: 'Транскрибация', text: 'Whisper-service получает аудио и возвращает текст с основой для извлечения вопросов.', icon: 'pi pi-wave-pulse', to: '/recordings' },
  { title: 'Извлечение', text: 'LLM выделяет вопросы, нормализует их и сохраняет в каталог для подготовки.', icon: 'pi pi-sparkles', to: '/interview-questions' },
  { title: 'Практика', text: 'Пользователь закрепляет ответы в тренажёре, mock-интервью и AI-чате.', icon: 'pi pi-bolt', to: '/trainer' }
]
const usecases = [
  { title: 'Каталог вопросов', text: 'Фильтрация, сортировка, детальные ответы и видеофрагменты.', icon: 'pi pi-comments', to: '/interview-questions' },
  { title: 'Практические задания', text: 'Реальные тестовые задания по профессиям и уровню.', icon: 'pi pi-briefcase', to: '/test-assignments' },
  { title: 'HH-аналитика', text: 'Источники skills, description и title с переключателями.', icon: 'pi pi-chart-line', to: '/hh-requirements' },
  { title: 'Записи интервью', text: 'Просмотр обработанных видео и списка извлечённых вопросов.', icon: 'pi pi-video', to: '/recordings' }
]
const roadmap = [
  { period: '1-3 день', title: 'Собрать базу', text: 'Выберите профессию, уровень и темы, которые чаще всего спрашивают на интервью.', tags: ['Каталог', 'Фильтры'] },
  { period: '4-7 день', title: 'Закрепить ответы', text: 'Переведите важные вопросы в карточки и проходите повторения по SM-2.', tags: ['SM-2', 'Заметки'] },
  { period: '8-11 день', title: 'Проверить практикой', text: 'Возьмите тестовое задание и проговорите решения в формате mock-интервью.', tags: ['Задания', 'Mock'] },
  { period: '12-14 день', title: 'Добить пробелы', text: 'Сверьте слабые места с HH-аналитикой и повторите вопросы с низкой уверенностью.', tags: ['Навыки', 'Фокус'] }
]
const latestQuestions = [
  { title: 'Какой опыт работы у вас с React?', topic: 'Frontend', level: 'Junior', score: 92, icon: 'pi pi-code' },
  { title: 'Расскажите о проектировании REST API.', topic: 'Backend', level: 'Middle', score: 86, icon: 'pi pi-server' },
  { title: 'Как вы находите узкие места в системе?', topic: 'System Design', level: 'Senior', score: 74, icon: 'pi pi-cog' },
  { title: 'Чем отличается Kafka от очереди задач?', topic: 'Backend', level: 'Middle', score: 68, icon: 'pi pi-database' }
]

async function loadStats() {
  try {
    const r = await api.getPublicStats()
    const data = r.data || {}
    stats.value = {
      questions: data.questions_count?.toLocaleString('ru-RU') || stats.value.questions,
      videos: data.videos_count?.toLocaleString('ru-RU') || stats.value.videos,
      skills: data.skills_count?.toLocaleString('ru-RU') || stats.value.skills,
      assignments: data.assignments_count?.toLocaleString('ru-RU') || stats.value.assignments,
      ready: stats.value.ready
    }
  } catch {}
}

onMounted(loadStats)
</script>

<style scoped>
.home-screen { padding-top: 46px; padding-bottom: 80px; }
.hero { min-height: 520px; display: grid; grid-template-columns: 1.08fr .92fr; align-items: center; gap: 60px; }
.hero-copy h1 { margin: 0; max-width: 900px; font-size: 58px; line-height: 1.2; letter-spacing: -.045em; }
.hero-copy h1 span { color: var(--cyan); }
.hero-copy p { max-width: 650px; margin: 28px 0 34px; color: var(--muted); font-size: 22px; line-height: 1.55; }
.hero-actions { display: flex; gap: 26px; }
.hero-visual { position: relative; min-height: 440px; }
.orb { position: absolute; border-radius: 50%; border: 5px solid rgba(18, 230, 209, .35); filter: drop-shadow(0 0 28px rgba(18, 230, 209, .16)); }
.orb.one { width: 250px; height: 250px; right: 130px; top: 20px; }
.orb.two { width: 195px; height: 195px; right: 60px; bottom: 20px; border-color: rgba(28, 114, 190, .25); }
.float-card, .progress-card { position: absolute; border: 1px solid rgba(39, 210, 229, .32); background: linear-gradient(145deg, rgba(8, 55, 78, .78), rgba(5, 21, 42, .92)); box-shadow: 0 28px 80px rgba(0, 0, 0, .35), inset 0 1px 0 rgba(255, 255, 255, .06); border-radius: 18px; }
.float-card { width: 88px; height: 88px; display: grid; place-items: center; color: var(--cyan); font-size: 34px; transform: rotate(4deg); animation: floatCard 4s ease-in-out infinite alternate; }
.chat { left: 110px; top: 90px; }
.award { left: 50px; top: 240px; color: #c8d6ef; transform: rotate(8deg); animation-delay: .4s; }
.code { right: 155px; top: 120px; color: #19caff; animation-delay: .8s; }
.play { right: 80px; bottom: 115px; color: #7aa7ff; animation-delay: 1.1s; }
@keyframes floatCard { to { translate: 0 -14px; } }
.progress-card { left: 230px; top: 130px; width: 290px; height: 235px; padding: 34px 30px; transform: perspective(700px) rotateY(-15deg) rotateX(4deg); }
.progress-card span, .progress-card small { color: var(--muted); font-size: 17px; }
.progress-card strong { display: block; margin-top: 28px; font-size: 38px; }
.curve { height: 78px; margin-top: 18px; background: linear-gradient(180deg, rgba(18, 230, 209, .48), rgba(18, 230, 209, .02)); border-radius: 60% 40% 0 0; position: relative; }
.curve span { position: absolute; right: 28px; top: -4px; width: 10px; height: 10px; border-radius: 50%; background: white; box-shadow: 0 0 20px var(--cyan); }
.chips { margin: 10px 0 30px; }
.chips p { margin: 0 0 10px; color: var(--muted); }
.chips div { display: flex; gap: 8px; flex-wrap: wrap; }
.tech-chip { height: 43px; display: inline-flex; align-items: center; gap: 8px; padding: 0 14px; border: 1px solid rgba(74, 137, 178, .28); border-radius: var(--radius); background: rgba(4, 21, 38, .82); color: #c3cfde; font-size: 14px; transition: .18s ease; box-shadow: inset 0 1px 0 rgba(255,255,255,.03); }
.tech-chip:hover { border-color: var(--line-strong); color: #fff; transform: translateY(-1px); }
.chips i { color: #61b9ff; font-size: 13px; }
.why { padding: 34px 28px 42px; }
.why header { text-align: center; margin-bottom: 34px; }
.why h2, .product-flow h2, .metrics-band h2, .usecases h2 { margin: 0; font-size: 31px; letter-spacing: -.03em; }
.why h2 span { color: var(--cyan); }
.why header p { margin: 10px 0 0; color: var(--muted); font-size: 17px; }
.why-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 34px; }
.reason-card { display: grid; grid-template-columns: 96px 1fr; gap: 18px; align-items: center; transition: .18s ease; }
.reason-card:hover { transform: translateY(-3px); }
.why h3 { margin: 0 0 10px; font-size: 20px; }
.why article p, .reason-card p { margin: 0; color: var(--muted); line-height: 1.55; }
.product-flow { display: grid; grid-template-columns: 1.06fr .94fr; gap: 18px; margin-top: 28px; align-items: stretch; }
.flow-copy, .flow-preview, .metrics-band, .usecase-card {
  border: 1px solid rgba(44, 202, 224, .14);
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(8, 35, 60, .58), rgba(4, 22, 40, .52));
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
}
.flow-copy, .metrics-band { padding: 28px 30px; }
.kicker { color: var(--cyan); font-weight: 800; text-transform: uppercase; font-size: 13px; }
.product-flow p, .metrics-band span, .usecases p { color: var(--muted); line-height: 1.55; }
.steps { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 26px; }
.steps button { min-height: 62px; border: 1px solid rgba(83, 137, 174, .2); border-radius: 8px; background: rgba(4, 20, 37, .54); color: var(--text); text-align: left; padding: 12px 16px; min-width: 150px; }
.steps button.active { border-color: rgba(18, 230, 209, .58); background: rgba(18, 230, 209, .1); box-shadow: 0 0 24px rgba(18, 230, 209, .06); }
.steps b { color: var(--cyan); margin-right: 9px; }
.flow-preview { position: relative; min-height: 300px; overflow: hidden; padding: 28px; display: grid; place-items: center; }
.preview-orbit { position: absolute; width: 270px; height: 270px; border-radius: 50%; border: 4px solid rgba(18, 230, 209, .2); right: 42px; top: 24px; }
.preview-card { position: relative; width: min(430px, 100%); border: 1px solid rgba(18, 230, 209, .24); border-radius: 14px; padding: 26px; background: linear-gradient(145deg, rgba(8, 55, 78, .62), rgba(5, 21, 42, .86)); }
.preview-card i { color: var(--cyan); font-size: 42px; }
.preview-card h3 { font-size: 28px; margin: 20px 0 8px; }
.metrics-band { margin-top: 18px; }
.metrics-band header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.stats-grid article { border: 1px solid rgba(83, 137, 174, .14); border-radius: 8px; padding: 20px; background: rgba(3, 20, 37, .34); }
.stats-grid strong { display: block; font-size: 34px; margin-top: 8px; }
.stats-grid small { color: var(--soft); }
.usecases { margin-top: 42px; }
.section-row { display: flex; justify-content: space-between; align-items: end; gap: 20px; }
.section-row.compact { margin-bottom: 22px; }
.quiet-link { color: var(--cyan); font-weight: 800; }
.usecase-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 18px; }
.usecase-card { min-height: 210px; padding: 24px; transition: .18s ease; }
.usecase-card:hover { transform: translateY(-4px); border-color: var(--line-strong); }
.usecases i { color: var(--cyan); font-size: 32px; }
.usecases h3 { font-size: 22px; margin: 22px 0 8px; }
.roadmap {
  margin-top: 18px;
  padding: 28px;
}
.roadmap-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-top: 22px;
}
.roadmap-card {
  min-height: 220px;
  padding: 22px;
  border: 1px solid rgba(83, 137, 174, .16);
  border-radius: var(--radius);
  background: rgba(3, 20, 37, .38);
  position: relative;
  overflow: hidden;
}
.roadmap-card::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  width: 3px;
  height: 100%;
  background: linear-gradient(180deg, var(--cyan), rgba(77, 163, 255, .2));
}
.roadmap-card span {
  color: var(--cyan);
  font-weight: 800;
  font-size: 14px;
}
.roadmap-card h3 {
  margin: 18px 0 10px;
  font-size: 22px;
}
.roadmap-card p {
  min-height: 74px;
  margin: 0 0 18px;
  color: var(--muted);
  line-height: 1.55;
}
.roadmap-card div {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.roadmap-card b {
  padding: 6px 10px;
  border-radius: 8px;
  background: rgba(0, 116, 207, .18);
  color: #62b7ff;
  font-size: 13px;
}
.home-workspace {
  display: grid;
  grid-template-columns: 1.18fr .82fr;
  gap: 18px;
  margin-top: 18px;
}
.latest-panel,
.practice-panel,
.source-cta {
  border: 1px solid rgba(44, 202, 224, .14);
  border-radius: var(--radius);
  background: linear-gradient(180deg, rgba(8, 35, 60, .58), rgba(4, 22, 40, .52));
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
}
.latest-panel,
.practice-panel {
  padding: 28px;
}
.question-list {
  display: grid;
  gap: 10px;
}
.question-row {
  min-height: 76px;
  display: grid;
  grid-template-columns: 48px 1fr auto;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid rgba(83, 137, 174, .14);
  border-radius: var(--radius);
  background: rgba(3, 20, 37, .36);
  transition: .18s ease;
}
.question-row:hover {
  border-color: var(--line-strong);
  transform: translateY(-1px);
}
.question-row i {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(18, 230, 209, .2);
  border-radius: var(--radius);
  color: var(--cyan);
  background: rgba(0, 229, 209, .05);
  font-size: 20px;
}
.question-row h3 {
  margin: 0 0 4px;
  font-size: 18px;
}
.question-row p {
  margin: 0;
  color: var(--muted);
}
.question-row strong {
  color: var(--cyan);
  font-size: 20px;
}
.practice-panel {
  position: relative;
  overflow: hidden;
}
.pulse-ring {
  width: 86px;
  height: 86px;
  display: grid;
  place-items: center;
  margin-bottom: 24px;
  border-radius: 50%;
  border: 1px solid rgba(18, 230, 209, .38);
  color: var(--cyan);
  background: rgba(18, 230, 209, .08);
  box-shadow: 0 0 42px rgba(18, 230, 209, .12);
  font-size: 34px;
}
.practice-panel h2,
.source-cta h2 {
  margin: 8px 0 12px;
  font-size: 31px;
  letter-spacing: -.03em;
}
.practice-panel p,
.source-cta p {
  margin: 0;
  color: var(--muted);
  line-height: 1.55;
}
.practice-plan {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin: 24px 0;
}
.practice-plan span {
  padding: 16px 12px;
  border: 1px solid rgba(83, 137, 174, .14);
  border-radius: var(--radius);
  background: rgba(3, 20, 37, .38);
  color: var(--muted);
  text-align: center;
}
.practice-plan b {
  display: block;
  color: var(--text);
  font-size: 26px;
}
.source-cta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
  margin-top: 18px;
  padding: 30px;
}
.source-cta > div:first-child {
  max-width: 760px;
}
.source-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
@media (max-width: 1200px) { .hero, .product-flow, .home-workspace { grid-template-columns: 1fr; } .hero-visual { display: none; } .why-grid, .stats-grid, .usecase-grid, .roadmap-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 720px) { .home-screen { padding-top: 32px; } .hero-copy h1 { font-size: 38px; } .hero-copy p { font-size: 17px; } .hero-actions, .steps, .source-cta, .source-actions { flex-direction: column; align-items: stretch; } .why-grid, .stats-grid, .usecase-grid, .roadmap-grid, .practice-plan { grid-template-columns: 1fr; } .section-row { align-items: flex-start; flex-direction: column; } .question-row { grid-template-columns: 42px 1fr; } .question-row strong { grid-column: 2; } }
</style>
