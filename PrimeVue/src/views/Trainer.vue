<template>
  <div class="page">
    <NavBar />
    <main class="screen trainer">

      <!-- Mode Select -->
      <div v-if="mode === 'select'" class="mode-select">
        <section class="trainer-hero glass">
          <div>
            <p class="eyebrow">Тренажёр</p>
            <h1>Практика вопросов</h1>
            <p>Спокойная сессия подготовки: вопрос, ответ, затем простая оценка «знаю» или «на повтор».</p>
          </div>
          <div class="hero-metrics">
            <article><b>{{ totalQuestions }}</b><span>вопросов</span></article>
            <article><b>{{ repeatCount }}</b><span>на повтор</span></article>
            <article><b>{{ availableInterviews }}</b><span>записей</span></article>
          </div>
        </section>

        <div v-if="loadError" class="state-panel glass">
          <h3>Часть данных недоступна</h3>
          <p>{{ loadError }}</p>
          <button class="btn small" @click="loadStats">Повторить</button>
        </div>

        <div v-if="sm2Stats.total > 0" class="sm2-row">
          <div class="sm2-pill new"><span>{{ sm2Stats.new }}</span> новых</div>
          <div class="sm2-pill review"><span>{{ sm2Stats.review }}</span> на повтор</div>
          <div class="sm2-pill learned"><span>{{ sm2Stats.learned }}</span> выучено</div>
        </div>

        <div class="mode-grid stagger">
          <div class="mode-card glass" @click="startFlashcards">
            <div class="mc-icon"><i class="pi pi-clone"></i></div>
            <h3>Проработка вопросов</h3>
            <p>Карточки с SM-2. Отмечайте «Знаю» или «На повтор».</p>
            <div class="mc-footer">
              <span class="tag">{{ totalQuestions }} вопросов</span>
              <span v-if="repeatCount > 0" class="tag middle">{{ repeatCount }} на повтор</span>
            </div>
          </div>
          <div class="mode-card glass" @click="startInterview">
            <div class="mc-icon"><i class="pi pi-comments"></i></div>
            <h3>Реальное собеседование</h3>
            <p>Вопросы из настоящих собеседований в хронологическом порядке.</p>
            <div class="mc-footer">
              <span class="tag">{{ availableInterviews }} записей</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Flashcard Setup -->
      <div v-if="mode === 'flashcard-setup'" class="setup glass">
        <button class="back-btn" @click="mode = 'select'"><i class="pi pi-arrow-left"></i>Назад</button>
        <h2>Настройка карточек</h2>

        <div class="form-stack">
          <div class="field">
            <label>Технология</label>
            <select v-model="selectedTopic" class="field-control">
              <option value="">Все</option>
              <option v-for="t in topics" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div class="field">
            <label>Сложность</label>
            <select v-model="selectedDifficulty" class="field-control">
              <option value="">Любая</option>
              <option value="junior">Junior</option>
              <option value="middle">Middle</option>
              <option value="senior">Senior</option>
            </select>
          </div>
          <div class="field">
            <label>Количество: <strong>{{ cardCount }}</strong></label>
            <input type="range" v-model.number="cardCount" min="5" max="50" step="5" class="range" />
          </div>
          <label class="check-label">
            <input type="checkbox" v-model="prioritizeRepeat" />
            <span>Сначала «на повтор»</span>
          </label>
          <button class="btn primary" @click="loadFlashcards" :disabled="loadingCards" style="width:100%">
            {{ loadingCards ? 'Загрузка...' : 'Начать' }}
          </button>
        </div>
      </div>

      <!-- Flashcard Mode -->
      <div v-if="mode === 'flashcard'" class="fc-mode">
        <div class="fc-top">
          <button class="icon-button" @click="mode = 'select'">
            <i class="pi pi-arrow-left"></i>
          </button>
          <div class="fc-progress-area">
            <span class="fc-counter">{{ currentCardIndex + 1 }} / {{ flashcards.length }}</span>
            <div class="progress"><div class="progress-fill" :style="{ width: flashcardProgress + '%' }"></div></div>
          </div>
          <div class="fc-stats">
            <span class="tag ok">Знаю {{ knownCount }}</span>
            <span class="tag middle">Повтор {{ repeatQueue.length }}</span>
          </div>
        </div>

        <Transition name="question-shift" mode="out-in">
          <div v-if="currentCard && !sessionComplete" :key="currentCard.id || currentCard.question" class="practice-card glass">
            <div class="fc-tags">
              <span class="tag" :class="diffTag(currentCard.difficulty)">{{ currentCard.difficulty }}</span>
              <span class="tag">{{ currentCard.topic }}</span>
            </div>
            <h2 class="fc-question">{{ currentCard.question }}</h2>

            <section class="trainer-videos">
              <h3><i class="pi pi-video"></i>Видео с этим вопросом</h3>
              <div v-for="video in currentCardVideos" :key="video.title + video.time" class="trainer-video-row">
                <span><i class="pi pi-play"></i>{{ video.title }}</span>
                <b :class="video.source === 'YouTube' ? 'youtube' : 'rutube'">{{ video.source === 'YouTube' ? '▶' : 'R' }}</b>
                <span>{{ video.source }}</span>
                <time>{{ video.time }}</time>
              </div>
            </section>

            <button v-if="!cardFlipped" class="btn primary answer-toggle" @click="showAnswer">
              <i class="pi pi-eye"></i>Показать ответ
            </button>
            <Transition name="answer-reveal">
              <div v-if="cardFlipped" class="answer-panel">
                <div class="answer-head">
                  <span>Ответ</span>
                  <button @click="cardFlipped = false"><i class="pi pi-angle-up"></i>Свернуть</button>
                </div>
                <div class="fc-answer" v-html="formatAnswer(currentCard.answer || 'Ответ не сгенерирован')"></div>
                <div class="fc-actions">
                  <button class="fc-btn repeat" @click="markRepeat">
                    <span>На повтор</span><kbd>←</kbd>
                  </button>
                  <button class="fc-btn known" @click="markKnown">
                    <span>Знаю</span><kbd>→</kbd>
                  </button>
                </div>
              </div>
            </Transition>
          </div>
        </Transition>

        <!-- Session Complete -->
        <div v-if="sessionComplete" class="fc-results glass">
          <div class="fr-icon"><i class="pi pi-check-circle"></i></div>
          <h2>Сессия завершена!</h2>
          <div class="fr-stats">
            <div class="fr-s"><span class="fr-val ok">{{ knownCount }}</span><span class="fr-lbl">Знаю</span></div>
            <div class="fr-s"><span class="fr-val warn">{{ repeatQueue.length }}</span><span class="fr-lbl">На повтор</span></div>
            <div class="fr-s"><span class="fr-val">{{ flashcards.length }}</span><span class="fr-lbl">Всего</span></div>
          </div>
          <div class="fr-actions">
            <button class="btn" @click="retryDifficult" :disabled="repeatQueue.length === 0">Повторить сложные</button>
            <button class="btn primary" @click="mode = 'flashcard-setup'">Новая сессия</button>
            <button class="btn" @click="mode = 'select'">На главную</button>
          </div>
        </div>
      </div>

      <!-- Interview Setup -->
      <div v-if="mode === 'interview-setup'" class="setup glass">
        <button class="back-btn" @click="mode = 'select'"><i class="pi pi-arrow-left"></i>Назад</button>
        <h2>Выберите запись</h2>

        <div v-if="loadingInterviews" class="iv-list">
          <div v-for="i in 4" :key="i" class="skeleton-card" style="padding:1rem;">
            <div class="skeleton-line lg" style="margin-bottom:.5rem"></div>
            <div class="skeleton-line" style="width:40%"></div>
          </div>
        </div>
        <div v-else class="iv-list">
          <div v-for="iv in interviewVideos" :key="iv.id" class="iv-item glass" @click="startInterviewSession(iv)">
            <div class="iv-info">
              <h3>{{ iv.title || 'Без названия' }}</h3>
              <div class="iv-meta">
                <span class="tag">{{ iv.platform || 'video' }}</span>
                <span class="iv-count">{{ videoQuestionCount(iv) }} вопросов</span>
              </div>
            </div>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
          </div>
          <div v-if="interviewVideos.length === 0" class="empty-state"><p>Нет записей</p></div>
        </div>
      </div>

      <!-- Interview Mode -->
      <div v-if="mode === 'interview'" class="interview">
        <div class="iv-header">
          <button class="icon-button" @click="mode = 'select'">
            <i class="pi pi-arrow-left"></i>
          </button>
          <h3>{{ currentInterviewTitle }}</h3>
          <span class="iv-counter">{{ interviewIndex + 1 }} / {{ interviewQuestions.length }}</span>
        </div>

        <Transition name="question-shift" mode="out-in">
          <div v-if="currentInterviewQuestion" :key="currentInterviewQuestion.id || currentInterviewQuestion.question" class="iv-card glass">
            <span class="tag" :class="diffTag(currentInterviewQuestion.difficulty)">{{ currentInterviewQuestion.difficulty }}</span>
            <h2>{{ currentInterviewQuestion.question }}</h2>
            <section class="trainer-videos compact">
              <h3><i class="pi pi-video"></i>Видео с этим вопросом</h3>
              <div v-for="video in currentInterviewVideos" :key="video.title + video.time" class="trainer-video-row">
                <span><i class="pi pi-play"></i>{{ video.title }}</span>
                <b :class="video.source === 'YouTube' ? 'youtube' : 'rutube'">{{ video.source === 'YouTube' ? '▶' : 'R' }}</b>
                <span>{{ video.source }}</span>
                <time>{{ video.time }}</time>
              </div>
            </section>
            <Transition name="answer-reveal">
              <div v-if="showInterviewAnswer" class="iv-answer" v-html="formatAnswer(currentInterviewQuestion.answer || 'Ответ не добавлен')"></div>
            </Transition>
            <div class="iv-actions">
              <button v-if="!showInterviewAnswer" class="btn primary" @click="showInterviewAnswer = true">Показать ответ</button>
              <button v-else class="btn" @click="nextInterviewQuestion" :disabled="interviewIndex >= interviewQuestions.length - 1">Следующий <i class="pi pi-arrow-right"></i></button>
            </div>
          </div>
        </Transition>

        <div v-if="interviewIndex >= interviewQuestions.length - 1 && showInterviewAnswer" class="iv-done">
          <p>Все вопросы пройдены!</p>
          <button class="btn" @click="mode = 'select'">Вернуться</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import NavBar from '../components/NavBar.vue'
import api from '../api/client'
import { trackMetrikaGoal } from '../utils/metrika'
import { questions as fallbackQuestions, recordings as fallbackRecordings, extractedQuestions } from '../data/mock'

const mode = ref('select')
const totalQuestions = ref(0)
const repeatCount = ref(0)
const availableInterviews = ref(0)
const topics = ref([])
const sm2Stats = ref({ total: 0, new: 0, review: 0, learned: 0 })

const selectedTopic = ref('')
const selectedDifficulty = ref('')
const cardCount = ref(20)
const prioritizeRepeat = ref(true)
const loadingCards = ref(false)

const flashcards = ref([])
const currentCardIndex = ref(0)
const cardFlipped = ref(false)
const knownCount = ref(0)
const repeatQueue = ref([])
const sessionComplete = ref(false)

const currentCard = computed(() => flashcards.value[currentCardIndex.value])
const fallbackVideos = [
  { title: 'Собеседование на Backend Developer', source: 'YouTube', time: '12:34' },
  { title: 'Mock interview. Java Developer', source: 'Rutube', time: '08:52' },
  { title: 'Интервью на Frontend Developer', source: 'YouTube', time: '16:41' }
]
const flashcardProgress = computed(() => {
  if (!flashcards.value.length) return 0
  return Math.round(((currentCardIndex.value + (sessionComplete.value ? 1 : 0)) / flashcards.value.length) * 100)
})

const diffTag = (d) => ({ junior: 'ok', middle: 'middle', senior: 'senior' }[d] || '')
const formatAnswer = (t) => t ? t.replace(/\n/g, '<br>') : ''
const normalizeVideos = (question) => {
  const raw = question?.videos || question?.sources || question?.video_sources || question?.related_videos || []
  const list = Array.isArray(raw) && raw.length ? raw : fallbackVideos
  return list.slice(0, 5).map((video, index) => ({
    title: video.title || video.video_title || video.name || `Видео ${index + 1}`,
    source: video.source || video.platform || 'YouTube',
    time: video.time || video.timecode || video.timestamp || '—',
    url: video.url || video.video_url || ''
  }))
}
const currentCardVideos = computed(() => normalizeVideos(currentCard.value))
const currentInterviewVideos = computed(() => normalizeVideos(currentInterviewQuestion.value))
const videoQuestionCount = (v) => {
  const raw = v?.question_count ?? v?.questions_count ?? v?.linked_questions ?? 0
  const n = Number(raw)
  return Number.isFinite(n) ? n : 0
}

const showAnswer = () => { cardFlipped.value = true }

const markKnown = async () => {
  if (currentCard.value) { knownCount.value++; try { await api.submitSM2Review(currentCard.value.id, 5) } catch {} }
  advanceCard()
}
const markRepeat = async () => {
  if (currentCard.value) { repeatQueue.value.push(currentCard.value); try { await api.submitSM2Review(currentCard.value.id, 1) } catch {} }
  advanceCard()
}
const advanceCard = () => {
  cardFlipped.value = false
  if (currentCardIndex.value < flashcards.value.length - 1) currentCardIndex.value++
  else sessionComplete.value = true
}
const retryDifficult = () => {
  flashcards.value = [...repeatQueue.value]; repeatQueue.value = []
  currentCardIndex.value = 0; knownCount.value = 0; cardFlipped.value = false; sessionComplete.value = false
}

// Keyboard
const handleKey = (e) => {
  if (mode.value !== 'flashcard' || sessionComplete.value) return
  if (e.code === 'Space') { e.preventDefault(); showAnswer() }
  else if (e.code === 'ArrowLeft' && cardFlipped.value) markRepeat()
  else if (e.code === 'ArrowRight' && cardFlipped.value) markKnown()
}
onMounted(() => { document.addEventListener('keydown', handleKey); loadStats() })
onUnmounted(() => document.removeEventListener('keydown', handleKey))

// Interview
const interviewVideos = ref([])
const loadingInterviews = ref(false)
const interviewQuestions = ref([])
const interviewIndex = ref(0)
const showInterviewAnswer = ref(false)
const currentInterviewTitle = ref('')
const currentInterviewQuestion = computed(() => interviewQuestions.value[interviewIndex.value])
const nextInterviewQuestion = () => { showInterviewAnswer.value = false; if (interviewIndex.value < interviewQuestions.value.length - 1) interviewIndex.value++ }
const loadError = ref('')

const loadStats = async () => {
  loadError.value = ''
  try {
    const r = await api.getQuestions()
    const qs = r.data.questions || []
    const source = qs.length ? qs : fallbackQuestions
    totalQuestions.value = r.data.total || source.length
    topics.value = [...new Set(source.map(q => q.topic).filter(Boolean))].sort()
  } catch {
    totalQuestions.value = fallbackQuestions.length
    topics.value = [...new Set(fallbackQuestions.map(q => q.topic).filter(Boolean))].sort()
    loadError.value = 'Показаны демо-данные: API вопросов временно недоступен'
  }
  try { const r = await api.getSM2Cards({}); sm2Stats.value = r.data.stats || { total: 0, new: 0, review: 0, learned: 0 }; repeatCount.value = sm2Stats.value.review } catch { loadError.value = loadError.value || 'Не удалось загрузить статистику SM-2' }
  try {
    const r = await api.getProcessedVideos()
    const videos = r.data?.videos || []
    interviewVideos.value = videos.length ? videos : fallbackRecordings.map((item) => ({ ...item, platform: 'demo', question_count: extractedQuestions.length }))
    availableInterviews.value = interviewVideos.value.length
  } catch {
    interviewVideos.value = fallbackRecordings.map((item) => ({ ...item, platform: 'demo', question_count: extractedQuestions.length }))
    availableInterviews.value = interviewVideos.value.length
    loadError.value = loadError.value || 'Показаны демо-записи: API записей временно недоступен'
  }
}

const loadFlashcards = async () => {
  loadingCards.value = true
  try {
    const params = {}
    if (selectedTopic.value) params.topic = selectedTopic.value
    if (selectedDifficulty.value) params.difficulty = selectedDifficulty.value
    const r = await api.getSM2Cards(params)
    let cards = r.data.cards || []
    if (!cards.length) {
      cards = fallbackQuestions.map((q) => ({
        id: q.id,
        question: q.title,
        answer: 'Сформулируйте ответ через конкретный пример из опыта: контекст, решение, результат и вывод.',
        topic: q.topic,
        difficulty: q.level
      }))
    }
    if (!prioritizeRepeat.value) { for (let i = cards.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [cards[i], cards[j]] = [cards[j], cards[i]] } }
    flashcards.value = cards.slice(0, cardCount.value)
    currentCardIndex.value = 0; knownCount.value = 0; repeatQueue.value = []; cardFlipped.value = false; sessionComplete.value = false
    mode.value = 'flashcard'
    if (flashcards.value.length > 0) {
      trackMetrikaGoal('start_trainer', {
        mode: 'flashcards',
        cards: flashcards.value.length,
        topic: selectedTopic.value || 'any',
        difficulty: selectedDifficulty.value || 'any'
      })
    }
  } catch (e) {
    const fallbackCards = fallbackQuestions.map((q) => ({
      id: q.id,
      question: q.title,
      answer: 'Сформулируйте ответ через конкретный пример из опыта: контекст, решение, результат и вывод.',
      topic: q.topic,
      difficulty: q.level
    }))
    flashcards.value = fallbackCards.slice(0, cardCount.value)
    currentCardIndex.value = 0; knownCount.value = 0; repeatQueue.value = []; cardFlipped.value = false; sessionComplete.value = false
    mode.value = 'flashcard'
    loadError.value = 'API карточек недоступен, открыта демо-сессия'
  }
  loadingCards.value = false
}

const startFlashcards = () => { mode.value = 'flashcard-setup' }
const startInterview = async () => {
  mode.value = 'interview-setup'; loadingInterviews.value = true
  try {
    const r = await api.getProcessedVideos()
    const videos = r.data?.videos || []
    interviewVideos.value = videos.length ? videos : fallbackRecordings.map((item) => ({ ...item, platform: 'demo', question_count: extractedQuestions.length }))
  } catch {
    interviewVideos.value = fallbackRecordings.map((item) => ({ ...item, platform: 'demo', question_count: extractedQuestions.length }))
    loadError.value = 'API записей недоступен, показаны демо-записи.'
  }
  loadingInterviews.value = false
}
const startInterviewSession = async (v) => {
  currentInterviewTitle.value = v.title || 'Собеседование'
  try {
    const r = await api.getVideoQuestions(v.id)
    const questions = r.data?.questions || []
    interviewQuestions.value = questions.length ? questions : extractedQuestions.map((q) => ({
      id: q.id,
      question: q.title,
      answer: 'Отвечайте структурно: короткое определение, пример, возможные trade-off и связь с вакансией.',
      difficulty: q.level
    }))
  } catch {
    interviewQuestions.value = extractedQuestions.map((q) => ({
      id: q.id,
      question: q.title,
      answer: 'Отвечайте структурно: короткое определение, пример, возможные trade-off и связь с вакансией.',
      difficulty: q.level
    }))
    loadError.value = 'API вопросов записи недоступен, открыта демо-сессия.'
  }
  interviewIndex.value = 0; showInterviewAnswer.value = false; mode.value = 'interview'
}
</script>

<style scoped>
.trainer { padding-top: 30px; padding-bottom: 58px; }
.mode-select { display: grid; gap: 18px; }
.trainer-hero {
  min-height: 235px;
  padding: 28px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 430px;
  gap: 28px;
  align-items: end;
  overflow: hidden;
}
.eyebrow { margin: 0 0 10px; color: var(--cyan); text-transform: uppercase; font-size: 13px; font-weight: 800; letter-spacing: .08em; }
.trainer-hero h1 { margin: 0 0 12px; font-size: 44px; line-height: 1.06; letter-spacing: -.035em; }
.trainer-hero p { max-width: 680px; margin: 0; color: var(--muted); font-size: 18px; line-height: 1.5; }
.hero-metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.hero-metrics article { min-height: 92px; padding: 15px; display: grid; align-content: end; border-radius: var(--radius); border: 1px solid rgba(83, 121, 148, .14); background: rgba(4, 20, 37, .42); }
.hero-metrics b { display: block; font-size: 30px; line-height: 1; }
.hero-metrics span { color: var(--muted); font-weight: 700; font-size: 14px; }
.state-panel { max-width: 780px; padding: 18px 20px; }
.state-panel h3 { margin: 0 0 6px; font-size: 19px; }
.state-panel p { margin: 0 0 12px; color: var(--muted); }
.sm2-row { display: flex; gap: 10px; flex-wrap: wrap; }
.sm2-pill { min-height: 40px; display: inline-flex; align-items: center; gap: 8px; padding: 0 13px; border: 1px solid rgba(83, 121, 148, .14); border-radius: var(--radius); background: rgba(4, 20, 37, .52); color: var(--muted); font-weight: 800; }
.sm2-pill span { color: var(--text); font-size: 18px; }
.sm2-pill.review span { color: var(--yellow); }
.sm2-pill.learned span { color: var(--cyan); }
.mode-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.mode-card { min-height: 218px; padding: 22px; display: grid; align-content: space-between; cursor: pointer; border-left: 3px solid var(--cyan); transition: transform .18s ease, border-color .18s ease, background .18s ease; }
.mode-card:nth-child(2) { border-left-color: var(--blue); }
.mode-card:hover { transform: translateY(-2px); border-color: rgba(18, 230, 209, .3); background: linear-gradient(180deg, rgba(10, 39, 64, .9), rgba(5, 27, 48, .86)); }
.mc-icon { width: 54px; height: 54px; display: grid; place-items: center; border: 1px solid rgba(18, 230, 209, .2); border-radius: var(--radius); color: var(--cyan); background: rgba(18, 230, 209, .055); font-size: 24px; }
.mode-card h3 { margin: 20px 0 8px; font-size: 24px; letter-spacing: -.025em; }
.mode-card p { margin: 0; color: var(--muted); font-size: 16px; line-height: 1.5; }
.mc-footer { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
.setup { width: min(700px, 100%); margin: 0 auto; padding: 24px; }
.setup h2 { margin: 16px 0 20px; font-size: 28px; letter-spacing: -.025em; }
.back-btn, .icon-button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 42px; padding: 0 14px; border: 1px solid rgba(83, 121, 148, .16); border-radius: var(--radius); background: rgba(4, 20, 37, .62); color: var(--text); font-weight: 800; }
.icon-button { width: 44px; padding: 0; flex: 0 0 44px; }
.form-stack { display: grid; gap: 16px; }
.field { display: grid; gap: 8px; }
.field label, .check-label { color: #d8e2ef; font-weight: 800; }
.field-control { height: 54px; width: 100%; border: 1px solid rgba(86, 132, 167, .22); background: rgba(4, 20, 37, .72); border-radius: var(--radius); color: var(--text); padding: 0 16px; outline: none; }
.range { width: 100%; accent-color: var(--cyan); }
.check-label { display: flex; align-items: center; gap: 10px; }
.check-label input { accent-color: var(--cyan); }
.fc-mode { display: grid; justify-items: center; }
.fc-top { width: 100%; display: grid; grid-template-columns: 44px minmax(0, 1fr) auto; align-items: center; gap: 16px; margin-bottom: 22px; }
.fc-progress-area { display: grid; gap: 8px; }
.fc-counter { color: var(--muted); font-weight: 800; text-align: center; }
.progress { height: 8px; overflow: hidden; border-radius: 999px; background: rgba(115, 131, 154, .2); }
.progress-fill { height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--cyan), var(--blue)); }
.fc-stats { display: flex; gap: 8px; }
.practice-card { width: min(980px, 100%); min-height: 340px; display: grid; align-content: center; justify-items: center; padding: 34px; margin-bottom: 18px; border-color: rgba(18, 230, 209, .22); background: linear-gradient(180deg, rgba(8, 33, 56, .92), rgba(5, 27, 48, .9)), url('../assets/media/hybrid/trainer-grid.svg') center / cover no-repeat; box-shadow: 0 18px 60px rgba(0,0,0,.24); }
.fc-tags { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; margin-bottom: 20px; }
.fc-question { max-width: 760px; margin: 0; text-align: center; font-size: 28px; line-height: 1.32; letter-spacing: -.02em; }
.answer-toggle { margin-top: 24px; }
.trainer-videos { width: min(820px, 100%); margin-top: 24px; border: 1px solid rgba(83, 121, 148, .14); border-radius: var(--radius); background: rgba(4, 20, 37, .42); overflow: hidden; text-align: left; }
.trainer-videos.compact { margin: 20px auto 0; }
.trainer-videos h3 { height: 46px; margin: 0; padding: 0 16px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid rgba(83, 121, 148, .12); color: #dbe6f3; font-size: 16px; }
.trainer-videos h3 i { color: var(--cyan); }
.trainer-video-row { min-height: 46px; display: grid; grid-template-columns: minmax(0, 1fr) 28px 110px 70px; align-items: center; gap: 12px; padding: 0 16px; border-bottom: 1px solid rgba(83, 121, 148, .09); color: #d7dee8; }
.trainer-video-row:last-child { border-bottom: 0; }
.trainer-video-row span:first-child { min-width: 0; display: flex; align-items: center; gap: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.trainer-video-row span:first-child i { color: var(--muted); }
.trainer-video-row span:nth-child(3), .trainer-video-row time { color: var(--muted); font-size: 14px; }
.youtube { color: #ff4d4d; }
.rutube { color: #d1b377; }
kbd { min-width: 28px; min-height: 24px; display: inline-grid; place-items: center; border: 1px solid rgba(83, 121, 148, .2); border-radius: 6px; background: rgba(4, 20, 37, .72); color: var(--text); font: inherit; font-size: 12px; }
.fc-answer { width: 100%; color: #d8e2ef; font-size: 17px; line-height: 1.7; }
.answer-panel { width: min(820px, 100%); margin-top: 24px; padding: 20px; border: 1px solid rgba(83, 121, 148, .14); border-radius: var(--radius); background: rgba(4, 20, 37, .58); }
.answer-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 14px; color: var(--cyan); font-weight: 800; }
.answer-head button { display: inline-flex; align-items: center; gap: 6px; border: 0; background: transparent; color: var(--muted); font-weight: 800; }
.answer-head button:hover { color: var(--cyan); }
.fc-actions { width: 100%; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 18px; }
.fc-btn { min-height: 56px; display: flex; align-items: center; justify-content: center; gap: 10px; border-radius: var(--radius); border: 1px solid rgba(83, 121, 148, .18); background: rgba(4, 20, 37, .72); color: var(--text); font-weight: 800; }
.fc-btn.repeat:hover { border-color: rgba(240, 203, 33, .65); color: var(--yellow); }
.fc-btn.known:hover { border-color: rgba(18, 230, 209, .65); color: var(--cyan); }
.fc-results { width: min(520px, 100%); padding: 34px; text-align: center; }
.fr-icon { width: 72px; height: 72px; display: inline-grid; place-items: center; margin-bottom: 12px; border-radius: 50%; border: 1px solid rgba(18, 230, 209, .35); color: var(--cyan); font-size: 34px; background: rgba(18, 230, 209, .08); }
.fc-results h2 { margin: 0 0 20px; font-size: 30px; }
.fr-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 18px; }
.fr-s { padding: 14px; border: 1px solid rgba(83, 121, 148, .14); border-radius: var(--radius); background: rgba(4, 20, 37, .5); }
.fr-val { display: block; font-size: 30px; font-weight: 800; }
.fr-val.ok { color: var(--cyan); }
.fr-val.warn { color: var(--yellow); }
.fr-lbl { color: var(--muted); font-weight: 700; }
.fr-actions { display: grid; gap: 10px; }
.iv-list { display: grid; gap: 10px; }
.iv-item { min-height: 86px; display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 16px 18px; cursor: pointer; transition: transform .18s ease, border-color .18s ease; }
.iv-item:hover { transform: translateX(4px); border-color: var(--line-strong); }
.iv-info h3 { margin: 0 0 8px; font-size: 19px; }
.iv-meta { display: flex; gap: 8px; align-items: center; }
.iv-count { color: var(--muted); font-weight: 700; }
.empty-state { text-align: center; padding: 28px; color: var(--muted); }
.interview { width: min(980px, 100%); margin: 0 auto; }
.iv-header { display: grid; grid-template-columns: 44px minmax(0, 1fr) auto; align-items: center; gap: 14px; margin-bottom: 18px; }
.iv-header h3 { margin: 0; font-size: 22px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.iv-counter { color: var(--muted); font-weight: 800; }
.iv-card { padding: 30px; text-align: center; }
.iv-card > .tag { margin-bottom: 18px; }
.iv-card h2 { margin: 0 0 22px; font-size: 28px; line-height: 1.32; letter-spacing: -.02em; }
.iv-answer { margin: 0 0 22px; padding: 20px; text-align: left; border: 1px solid rgba(83, 121, 148, .14); border-radius: var(--radius); background: rgba(4, 20, 37, .58); color: #d8e2ef; font-size: 17px; line-height: 1.7; }
.iv-actions { display: flex; justify-content: center; gap: 12px; }
.iv-done { margin-top: 16px; text-align: center; color: var(--muted); }
.question-shift-enter-active, .question-shift-leave-active { transition: opacity .28s ease, transform .28s ease; }
.question-shift-enter-from { opacity: 0; transform: translateY(10px); }
.question-shift-leave-to { opacity: 0; transform: translateY(-8px); }
.answer-reveal-enter-active, .answer-reveal-leave-active { transition: opacity .26s ease, transform .26s ease, max-height .32s ease; overflow: hidden; }
.answer-reveal-enter-from, .answer-reveal-leave-to { opacity: 0; transform: translateY(-6px); max-height: 0; }
.answer-reveal-enter-to, .answer-reveal-leave-from { opacity: 1; transform: translateY(0); max-height: 560px; }

@media (max-width: 1100px) {
  .trainer-hero { grid-template-columns: 1fr; }
  .hero-metrics { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 720px) {
  .trainer-hero { padding: 24px; }
  .trainer-hero h1 { font-size: 38px; }
  .hero-metrics, .mode-grid, .fr-stats, .fc-actions { grid-template-columns: 1fr; }
  .fc-top, .iv-header { grid-template-columns: 44px 1fr; }
  .fc-stats, .iv-counter { grid-column: 1 / -1; justify-content: center; }
  .practice-card { min-height: 380px; padding: 24px; }
  .fc-question, .iv-card h2 { font-size: 24px; }
  .trainer-video-row { grid-template-columns: 1fr; gap: 4px; padding: 10px 14px; }
}
</style>
