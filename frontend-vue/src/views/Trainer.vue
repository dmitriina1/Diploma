<template>
  <div class="trainer-page">
    <NavBar />
    
    <div class="trainer-container">
      <!-- Mode Selection -->
      <div v-if="mode === 'select'" class="mode-select">
        <h1 class="page-title">
          <i class="pi pi-bolt"></i> Тренажёр SM-2
        </h1>
        <p class="page-subtitle">Интервальные повторения по алгоритму SuperMemo 2</p>

        <!-- SM-2 Stats -->
        <div v-if="sm2Stats.total > 0" class="sm2-overview">
          <div class="sm2-stat new"><i class="pi pi-plus-circle"></i> <span>{{ sm2Stats.new }}</span> новых</div>
          <div class="sm2-stat review"><i class="pi pi-replay"></i> <span>{{ sm2Stats.review }}</span> к повтору</div>
          <div class="sm2-stat learned"><i class="pi pi-check-circle"></i> <span>{{ sm2Stats.learned }}</span> выучено</div>
        </div>

        <div class="mode-cards">
          <div class="mode-card" @click="startFlashcards">
            <div class="mode-icon flashcard-icon">
              <i class="pi pi-clone"></i>
            </div>
            <h2>Проработка вопросов</h2>
            <p>Карточки с алгоритмом SM-2. Отмечайте «Знаю» или «На повтор» — система рассчитает оптимальный интервал повторения.</p>
            <div class="mode-stats">
              <Tag icon="pi pi-question-circle" :value="`${totalQuestions} вопросов`" severity="info" />
              <Tag v-if="repeatCount > 0" icon="pi pi-replay" :value="`${repeatCount} на повтор`" severity="warning" />
            </div>
          </div>

          <div class="mode-card" @click="startInterview">
            <div class="mode-icon interview-icon">
              <i class="pi pi-microphone"></i>
            </div>
            <h2>Реальное собеседование</h2>
            <p>Вопросы из настоящих собеседований в хронологическом порядке. Проверьте, сможете ли вы ответить в условиях, приближённых к реальным.</p>
            <div class="mode-stats">
              <Tag icon="pi pi-video" :value="`${availableInterviews} записей`" severity="info" />
            </div>
          </div>
        </div>
      </div>

      <!-- Flashcard Setup -->
      <div v-if="mode === 'flashcard-setup'" class="setup-panel">
        <Button icon="pi pi-arrow-left" label="Назад" text @click="mode = 'select'" class="back-btn" />
        <h2><i class="pi pi-clone"></i> Настройка карточек</h2>
        
        <div class="setup-form">
          <div class="form-group">
            <label>Технология</label>
            <Dropdown v-model="selectedTopic" :options="topics" placeholder="Все технологии" showClear class="w-full" />
          </div>
          <div class="form-group">
            <label>Сложность</label>
            <Dropdown v-model="selectedDifficulty" :options="difficulties" optionLabel="label" optionValue="value" placeholder="Любая" showClear class="w-full" />
          </div>
          <div class="form-group">
            <label>Количество карточек</label>
            <Slider v-model="cardCount" :min="5" :max="50" :step="5" class="w-full" />
            <span class="slider-value">{{ cardCount }} карточек</span>
          </div>
          <div class="form-group">
            <label>
              <Checkbox v-model="prioritizeRepeat" :binary="true" />
              <span class="ml-2">Сначала вопросы «На повтор»</span>
            </label>
          </div>

          <Button label="Начать" icon="pi pi-play" @click="loadFlashcards" :loading="loadingCards" class="start-btn" />
        </div>
      </div>

      <!-- Flashcard Mode -->
      <div v-if="mode === 'flashcard'" class="flashcard-mode">
        <div class="flashcard-header">
          <Button icon="pi pi-arrow-left" text @click="mode = 'select'" />
          <div class="progress-info">
            <span>{{ currentCardIndex + 1 }} / {{ flashcards.length }}</span>
            <ProgressBar :value="flashcardProgress" :showValue="false" class="progress-bar" />
          </div>
          <div class="session-stats">
            <Tag :value="`✓ ${knownCount}`" severity="success" />
            <Tag :value="`↻ ${repeatQueueCount}`" severity="warning" />
          </div>
        </div>

        <div v-if="currentCard" class="flashcard-container">
          <div class="flashcard" :class="{ flipped: cardFlipped }" @click="flipCard">
            <div class="flashcard-front">
              <div class="card-difficulty">
                <Tag :value="currentCard.difficulty" :severity="diffSeverity(currentCard.difficulty)" />
                <Tag :value="currentCard.topic" severity="info" />
              </div>
              <h2 class="card-question">{{ currentCard.question }}</h2>
              <p class="flip-hint"><i class="pi pi-sync"></i> Нажмите, чтобы увидеть ответ</p>
            </div>
            <div class="flashcard-back">
              <div class="card-answer" v-html="formatAnswer(currentCard.answer || 'Ответ не сгенерирован')"></div>
            </div>
          </div>

          <div v-if="cardFlipped" class="flashcard-actions">
            <Button label="На повтор" icon="pi pi-replay" severity="warning" size="large"
                    @click="markRepeat" class="action-btn" />
            <Button label="Знаю" icon="pi pi-check" severity="success" size="large"
                    @click="markKnown" class="action-btn" />
          </div>
        </div>

        <!-- Session Complete -->
        <div v-if="sessionComplete" class="session-results">
          <div class="results-card">
            <i class="pi pi-trophy results-icon"></i>
            <h2>Сессия завершена!</h2>
            <div class="results-stats">
              <div class="stat">
                <span class="stat-value success">{{ knownCount }}</span>
                <span class="stat-label">Знаю</span>
              </div>
              <div class="stat">
                <span class="stat-value warning">{{ repeatQueueCount }}</span>
                <span class="stat-label">На повтор</span>
              </div>
              <div class="stat">
                <span class="stat-value">{{ flashcards.length }}</span>
                <span class="stat-label">Всего</span>
              </div>
            </div>
            <div class="results-actions">
              <Button label="Повторить сложные" icon="pi pi-replay" severity="warning"
                      @click="retryDifficult" :disabled="repeatQueueCount === 0" />
              <Button label="Новая сессия" icon="pi pi-refresh" severity="info" @click="mode = 'flashcard-setup'" />
              <Button label="На главную" icon="pi pi-home" text @click="mode = 'select'" />
            </div>
          </div>
        </div>
      </div>

      <!-- Interview Mode Setup -->
      <div v-if="mode === 'interview-setup'" class="setup-panel">
        <Button icon="pi pi-arrow-left" label="Назад" text @click="mode = 'select'" class="back-btn" />
        <h2><i class="pi pi-microphone"></i> Выберите запись собеседования</h2>
        
        <div v-if="loadingInterviews" class="loading-interviews">
          <ProgressSpinner />
        </div>
        <div v-else class="interview-list">
          <div v-for="interview in interviewVideos" :key="interview.id" 
               class="interview-item" @click="startInterviewSession(interview)">
            <div class="interview-info">
              <h3>{{ interview.title || 'Без названия' }}</h3>
              <div class="interview-meta">
                <Tag :value="interview.platform" severity="secondary" />
                <span>{{ interview.question_count || 0 }} вопросов</span>
              </div>
            </div>
            <i class="pi pi-chevron-right"></i>
          </div>
          <div v-if="interviewVideos.length === 0" class="no-interviews">
            <i class="pi pi-inbox"></i>
            <p>Пока нет обработанных записей собеседований</p>
          </div>
        </div>
      </div>

      <!-- Interview Mode Active -->
      <div v-if="mode === 'interview'" class="interview-mode">
        <div class="interview-header">
          <Button icon="pi pi-arrow-left" text @click="mode = 'select'" />
          <h3>{{ currentInterviewTitle }}</h3>
          <span class="q-counter">Вопрос {{ interviewIndex + 1 }} / {{ interviewQuestions.length }}</span>
        </div>

        <div v-if="currentInterviewQuestion" class="interview-question-card">
          <div class="iq-difficulty">
            <Tag :value="currentInterviewQuestion.difficulty" :severity="diffSeverity(currentInterviewQuestion.difficulty)" />
          </div>
          <h2>{{ currentInterviewQuestion.question }}</h2>
          
          <div v-if="showInterviewAnswer" class="iq-answer" v-html="formatAnswer(currentInterviewQuestion.answer || 'Ответ не добавлен')"></div>
          
          <div class="iq-actions">
            <Button v-if="!showInterviewAnswer" label="Показать ответ" icon="pi pi-eye" @click="showInterviewAnswer = true" />
            <Button v-else label="Следующий вопрос" icon="pi pi-arrow-right" @click="nextInterviewQuestion" 
                    :disabled="interviewIndex >= interviewQuestions.length - 1" />
          </div>
        </div>

        <div v-if="interviewIndex >= interviewQuestions.length - 1 && showInterviewAnswer" class="interview-complete">
          <p><i class="pi pi-check-circle"></i> Все вопросы из этой записи пройдены!</p>
          <Button label="Вернуться" icon="pi pi-home" @click="mode = 'select'" />
        </div>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import api from '../api/client'

const mode = ref('select')

// General
const totalQuestions = ref(0)
const repeatCount = ref(0)
const availableInterviews = ref(0)
const topics = ref([])

// SM-2 stats
const sm2Stats = ref({ total: 0, new: 0, review: 0, learned: 0 })

// Flashcard setup
const selectedTopic = ref(null)
const selectedDifficulty = ref(null)
const cardCount = ref(20)
const prioritizeRepeat = ref(true)
const loadingCards = ref(false)
const difficulties = [
  { label: 'Junior', value: 'junior' },
  { label: 'Middle', value: 'middle' },
  { label: 'Senior', value: 'senior' }
]

// Flashcard session
const flashcards = ref([])
const currentCardIndex = ref(0)
const cardFlipped = ref(false)
const knownCount = ref(0)
const repeatQueue = ref([])
const sessionComplete = ref(false)

const currentCard = computed(() => flashcards.value[currentCardIndex.value])
const repeatQueueCount = computed(() => repeatQueue.value.length)
const flashcardProgress = computed(() => {
  if (!flashcards.value.length) return 0
  return Math.round(((currentCardIndex.value + (sessionComplete.value ? 1 : 0)) / flashcards.value.length) * 100)
})

const flipCard = () => { cardFlipped.value = !cardFlipped.value }

const markKnown = async () => {
  if (currentCard.value) {
    knownCount.value++
    // SM-2: quality = 5 (идеально знаю)
    try {
      await api.submitSM2Review(currentCard.value.id, 5)
    } catch (e) { console.error('SM-2 review error:', e) }
  }
  advanceCard()
}

const markRepeat = async () => {
  if (currentCard.value) {
    repeatQueue.value.push(currentCard.value)
    // SM-2: quality = 1 (не знаю, нужен повтор)
    try {
      await api.submitSM2Review(currentCard.value.id, 1)
    } catch (e) { console.error('SM-2 review error:', e) }
  }
  advanceCard()
}

const advanceCard = () => {
  cardFlipped.value = false
  if (currentCardIndex.value < flashcards.value.length - 1) {
    currentCardIndex.value++
  } else {
    sessionComplete.value = true
  }
}

const retryDifficult = () => {
  flashcards.value = [...repeatQueue.value]
  repeatQueue.value = []
  currentCardIndex.value = 0
  knownCount.value = 0
  cardFlipped.value = false
  sessionComplete.value = false
}

// Interview mode
const interviewVideos = ref([])
const loadingInterviews = ref(false)
const interviewQuestions = ref([])
const interviewIndex = ref(0)
const showInterviewAnswer = ref(false)
const currentInterviewTitle = ref('')

const currentInterviewQuestion = computed(() => interviewQuestions.value[interviewIndex.value])

const nextInterviewQuestion = () => {
  showInterviewAnswer.value = false
  if (interviewIndex.value < interviewQuestions.value.length - 1) {
    interviewIndex.value++
  }
}

const diffSeverity = (d) => {
  return { junior: 'success', middle: 'warning', senior: 'danger' }[d] || 'info'
}

const formatAnswer = (text) => {
  if (!text) return ''
  return text.replace(/\n/g, '<br>')
}

// API calls
const loadStats = async () => {
  try {
    const r = await api.getQuestions({ status: 'approved', limit: 1 })
    const data = r.data
    totalQuestions.value = data.total || (data.questions || []).length
  } catch (e) { console.error(e) }

  // Load SM-2 stats from server
  try {
    const r = await api.getSM2Cards({ })
    sm2Stats.value = r.data.stats || { total: 0, new: 0, review: 0, learned: 0 }
    repeatCount.value = sm2Stats.value.review
  } catch (e) { console.error('SM-2 stats error:', e) }

  // Count available interview videos
  try {
    const r = await api.getProcessedVideos()
    const videos = r.data?.videos || r.data || []
    availableInterviews.value = videos.length
    interviewVideos.value = videos
  } catch { availableInterviews.value = 0 }
}

const loadFlashcards = async () => {
  loadingCards.value = true
  try {
    // Use SM-2 endpoint — it sorts cards by due date (review first, then new, then learned)
    const params = {}
    if (selectedTopic.value) params.topic = selectedTopic.value
    if (selectedDifficulty.value) params.difficulty = selectedDifficulty.value

    const r = await api.getSM2Cards(params)
    let cards = r.data.cards || []

    // If not prioritizing repeat, shuffle
    if (!prioritizeRepeat.value) {
      for (let i = cards.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [cards[i], cards[j]] = [cards[j], cards[i]]
      }
    }

    // Populate topics from first load
    const topicSet = new Set(cards.map(c => c.topic).filter(Boolean))
    topics.value = [...topicSet].sort()

    flashcards.value = cards.slice(0, cardCount.value)
    currentCardIndex.value = 0
    knownCount.value = 0
    repeatQueue.value = []
    cardFlipped.value = false
    sessionComplete.value = false
    mode.value = 'flashcard'
  } catch (e) {
    console.error('Failed to load flashcards:', e)
  }
  loadingCards.value = false
}

const startFlashcards = () => { mode.value = 'flashcard-setup' }

const startInterview = async () => {
  mode.value = 'interview-setup'
  loadingInterviews.value = true
  try {
    const r = await api.getProcessedVideos()
    interviewVideos.value = r.data?.videos || r.data || []
  } catch { interviewVideos.value = [] }
  loadingInterviews.value = false
}

const startInterviewSession = async (video) => {
  currentInterviewTitle.value = video.title || 'Собеседование'
  try {
    const r = await api.getVideoQuestions(video.id)
    interviewQuestions.value = r.data?.questions || r.data || []
  } catch { interviewQuestions.value = [] }
  
  interviewIndex.value = 0
  showInterviewAnswer.value = false
  mode.value = 'interview'
}

onMounted(loadStats)
</script>

<style scoped>
.trainer-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
}
.trainer-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
}

/* Mode Selection */
.page-title {
  font-size: 2.2rem;
  text-align: center;
  margin-bottom: 0.5rem;
  color: white;
}
.page-title i { color: #667eea; }
.page-subtitle {
  text-align: center;
  color: rgba(255,255,255,0.6);
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.sm2-overview {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}
.sm2-stat {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.6rem 1.2rem;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255,255,255,0.8);
}
.sm2-stat span { font-weight: 800; font-size: 1.2rem; }
.sm2-stat.new { background: rgba(102, 126, 234, 0.2); color: #a4b4f7; }
.sm2-stat.review { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
.sm2-stat.learned { background: rgba(34, 197, 94, 0.2); color: #4ade80; }

.mode-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}
.mode-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  padding: 2rem;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}
.mode-card:hover {
  background: rgba(255,255,255,0.08);
  border-color: #667eea;
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(102,126,234,0.2);
}
.mode-card h2 { margin: 1rem 0 0.5rem; font-size: 1.3rem; color: white; }
.mode-card p { color: rgba(255,255,255,0.6); font-size: 0.9rem; line-height: 1.5; margin-bottom: 1rem; }
.mode-icon {
  width: 80px; height: 80px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto;
  font-size: 2rem;
}
.flashcard-icon { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
.interview-icon { background: linear-gradient(135deg, #f093fb, #f5576c); color: white; }
.mode-stats { display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; }

/* Setup */
.setup-panel { max-width: 600px; margin: 0 auto; }
.setup-panel h2 { color: white; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem; }
.back-btn { margin-bottom: 1rem; }
.setup-form { display: flex; flex-direction: column; gap: 1.5rem; }
.form-group { display: flex; flex-direction: column; gap: 0.5rem; }
.form-group label { color: rgba(255,255,255,0.8); font-weight: 600; display: flex; align-items: center; gap: 0.5rem; }
.slider-value { text-align: center; color: #667eea; font-weight: 700; font-size: 1.1rem; }
.start-btn { margin-top: 1rem; }

/* Flashcard Mode */
.flashcard-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;
}
.progress-info { flex: 1; margin: 0 1rem; text-align: center; color: rgba(255,255,255,0.8); }
.progress-bar { margin-top: 0.5rem; }
.session-stats { display: flex; gap: 0.5rem; }

.flashcard-container { display: flex; flex-direction: column; align-items: center; gap: 2rem; }
.flashcard {
  width: 100%; max-width: 700px;
  min-height: 350px;
  perspective: 1000px;
  cursor: pointer;
  position: relative;
}
.flashcard-front, .flashcard-back {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  padding: 2.5rem;
  min-height: 350px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  transition: all 0.3s;
}
.flashcard-front { display: flex; }
.flashcard-back { display: none; }
.flashcard.flipped .flashcard-front { display: none; }
.flashcard.flipped .flashcard-back { display: flex; }
.card-difficulty { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
.card-question { color: white; font-size: 1.5rem; text-align: center; line-height: 1.6; }
.flip-hint { color: rgba(255,255,255,0.3); font-size: 0.85rem; margin-top: 2rem; }
.card-answer {
  color: rgba(255,255,255,0.85); font-size: 1rem; line-height: 1.8;
  text-align: left; width: 100%; max-height: 400px; overflow-y: auto;
}

.flashcard-actions {
  display: flex; gap: 1.5rem;
}
.action-btn { min-width: 180px; }

/* Session Results */
.session-results { display: flex; justify-content: center; padding: 2rem 0; }
.results-card {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  padding: 3rem;
  text-align: center;
  max-width: 500px; width: 100%;
}
.results-icon { font-size: 4rem; color: #FFD700; margin-bottom: 1rem; }
.results-card h2 { color: white; margin-bottom: 1.5rem; }
.results-stats { display: flex; justify-content: center; gap: 2rem; margin-bottom: 2rem; }
.stat { display: flex; flex-direction: column; align-items: center; }
.stat-value { font-size: 2rem; font-weight: 700; color: white; }
.stat-value.success { color: #22c55e; }
.stat-value.warning { color: #f59e0b; }
.stat-label { color: rgba(255,255,255,0.5); font-size: 0.85rem; }
.results-actions { display: flex; flex-direction: column; gap: 0.75rem; }

/* Interview Mode */
.interview-list { display: flex; flex-direction: column; gap: 0.75rem; }
.interview-item {
  display: flex; align-items: center; justify-content: space-between;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px; padding: 1.25rem; cursor: pointer; transition: all 0.2s;
}
.interview-item:hover { background: rgba(255,255,255,0.08); border-color: #667eea; }
.interview-info h3 { color: white; margin: 0 0 0.5rem; font-size: 1rem; }
.interview-meta { display: flex; align-items: center; gap: 0.75rem; color: rgba(255,255,255,0.5); font-size: 0.85rem; }
.no-interviews { text-align: center; padding: 3rem; color: rgba(255,255,255,0.4); }
.no-interviews i { font-size: 3rem; margin-bottom: 1rem; display: block; }
.loading-interviews { display: flex; justify-content: center; padding: 3rem; }

.interview-header {
  display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;
}
.interview-header h3 { flex: 1; color: white; margin: 0; }
.q-counter { color: rgba(255,255,255,0.6); font-size: 0.9rem; white-space: nowrap; }

.interview-question-card {
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px; padding: 2rem; text-align: center;
}
.interview-question-card h2 { color: white; font-size: 1.4rem; line-height: 1.5; margin: 1rem 0 1.5rem; }
.iq-difficulty { margin-bottom: 0.5rem; }
.iq-answer {
  text-align: left; color: rgba(255,255,255,0.8); line-height: 1.7;
  background: rgba(255,255,255,0.03); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;
}
.iq-actions { display: flex; justify-content: center; gap: 1rem; }
.interview-complete {
  text-align: center; padding: 2rem; color: rgba(255,255,255,0.7); margin-top: 1.5rem;
}
.interview-complete i { color: #22c55e; font-size: 1.2rem; }

@media (max-width: 768px) {
  .mode-cards { grid-template-columns: 1fr; }
  .flashcard-actions { flex-direction: column; }
  .action-btn { min-width: auto; width: 100%; }
  .detail-header { flex-direction: column; gap: 1rem; }
}
</style>
