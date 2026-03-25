<template>
  <div class="page">
    <NavBar />
    <div class="container" style="padding-top:2rem; padding-bottom:3rem;">

      <!-- Mode Select -->
      <div v-if="mode === 'select'" class="mode-select">
        <h1 class="page-heading h-page">Тренажёр SM-2</h1>
        <p class="page-desc p-muted">Интервальные повторения по алгоритму SuperMemo 2</p>

        <div v-if="loadError" class="state-panel" style="margin:0 auto 1.2rem; max-width:680px;">
          <h3>Часть данных недоступна</h3>
          <p>{{ loadError }}</p>
          <button class="btn btn-secondary btn-sm" style="margin-top:.7rem" @click="loadStats">Повторить</button>
        </div>

        <div v-if="sm2Stats.total > 0" class="sm2-row">
          <div class="sm2-pill new"><span>{{ sm2Stats.new }}</span> новых</div>
          <div class="sm2-pill review"><span>{{ sm2Stats.review }}</span> на повтор</div>
          <div class="sm2-pill learned"><span>{{ sm2Stats.learned }}</span> выучено</div>
        </div>

        <div class="mode-grid stagger">
          <div class="mode-card card card-hover interactive-card" @click="startFlashcards">
            <div class="mc-icon"><BrandIcon name="flashcards" :size="72" /></div>
            <h3>Проработка вопросов</h3>
            <p>Карточки с SM-2. Отмечайте «Знаю» или «На повтор».</p>
            <div class="mc-footer">
              <span class="badge badge-info">{{ totalQuestions }} вопросов</span>
              <span v-if="repeatCount > 0" class="badge badge-warn">{{ repeatCount }} на повтор</span>
            </div>
          </div>
          <div class="mode-card card card-hover interactive-card" @click="startInterview">
            <div class="mc-icon"><BrandIcon name="interview" :size="72" /></div>
            <h3>Реальное собеседование</h3>
            <p>Вопросы из настоящих собеседований в хронологическом порядке.</p>
            <div class="mc-footer">
              <span class="badge badge-info">{{ availableInterviews }} записей</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Flashcard Setup -->
      <div v-if="mode === 'flashcard-setup'" class="setup container-sm">
        <button class="btn btn-ghost btn-sm" @click="mode = 'select'" style="margin-bottom:1rem">← Назад</button>
        <h2 class="page-heading" style="font-size:1.25rem">Настройка карточек</h2>

        <div class="form-stack">
          <div class="field">
            <label>Технология</label>
            <select v-model="selectedTopic" class="input">
              <option value="">Все</option>
              <option v-for="t in topics" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div class="field">
            <label>Сложность</label>
            <select v-model="selectedDifficulty" class="input">
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
          <button class="btn btn-primary btn-lg" @click="loadFlashcards" :disabled="loadingCards" style="width:100%">
            {{ loadingCards ? 'Загрузка...' : 'Начать' }}
          </button>
        </div>
      </div>

      <!-- Flashcard Mode -->
      <div v-if="mode === 'flashcard'" class="fc-mode">
        <div class="fc-top">
          <button class="btn btn-ghost btn-icon" @click="mode = 'select'">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          </button>
          <div class="fc-progress-area">
            <span class="fc-counter">{{ currentCardIndex + 1 }} / {{ flashcards.length }}</span>
            <div class="progress"><div class="progress-fill" :style="{ width: flashcardProgress + '%' }"></div></div>
          </div>
          <div class="fc-stats">
            <span class="badge badge-ok">✓ {{ knownCount }}</span>
            <span class="badge badge-warn">↻ {{ repeatQueue.length }}</span>
          </div>
        </div>

        <div v-if="currentCard && !sessionComplete" class="fc-scene" @click="flipCard">
          <div class="fc-card" :class="{ flipped: cardFlipped }">
            <div class="fc-face fc-front">
              <div class="fc-tags">
                <span class="badge" :class="diffBadge(currentCard.difficulty)">{{ currentCard.difficulty }}</span>
                <span class="badge badge-info">{{ currentCard.topic }}</span>
              </div>
              <h2 class="fc-question">{{ currentCard.question }}</h2>
              <span class="fc-hint">Нажмите, чтобы перевернуть · <kbd>Space</kbd></span>
            </div>
            <div class="fc-face fc-back">
              <div class="fc-answer" v-html="formatAnswer(currentCard.answer || 'Ответ не сгенерирован')"></div>
            </div>
          </div>
        </div>

        <div v-if="cardFlipped && !sessionComplete" class="fc-actions">
          <button class="fc-btn repeat" @click="markRepeat">
            <span>↻ На повтор</span><kbd>←</kbd>
          </button>
          <button class="fc-btn known" @click="markKnown">
            <span>✓ Знаю</span><kbd>→</kbd>
          </button>
        </div>

        <!-- Session Complete -->
        <div v-if="sessionComplete" class="fc-results card">
          <div class="fr-emoji">🎉</div>
          <h2>Сессия завершена!</h2>
          <div class="fr-stats">
            <div class="fr-s"><span class="fr-val ok">{{ knownCount }}</span><span class="fr-lbl">Знаю</span></div>
            <div class="fr-s"><span class="fr-val warn">{{ repeatQueue.length }}</span><span class="fr-lbl">На повтор</span></div>
            <div class="fr-s"><span class="fr-val">{{ flashcards.length }}</span><span class="fr-lbl">Всего</span></div>
          </div>
          <div class="fr-actions">
            <button class="btn btn-warn" @click="retryDifficult" :disabled="repeatQueue.length === 0">Повторить сложные</button>
            <button class="btn btn-secondary" @click="mode = 'flashcard-setup'">Новая сессия</button>
            <button class="btn btn-ghost" @click="mode = 'select'">На главную</button>
          </div>
        </div>
      </div>

      <!-- Interview Setup -->
      <div v-if="mode === 'interview-setup'" class="setup container-sm">
        <button class="btn btn-ghost btn-sm" @click="mode = 'select'" style="margin-bottom:1rem">← Назад</button>
        <h2 class="page-heading" style="font-size:1.25rem">Выберите запись</h2>

        <div v-if="loadingInterviews" class="iv-list">
          <div v-for="i in 4" :key="i" class="skeleton-card" style="padding:1rem;">
            <div class="skeleton-line lg" style="margin-bottom:.5rem"></div>
            <div class="skeleton-line" style="width:40%"></div>
          </div>
        </div>
        <div v-else class="iv-list">
          <div v-for="iv in interviewVideos" :key="iv.id" class="iv-item card card-hover" @click="startInterviewSession(iv)">
            <div class="iv-info">
              <h3>{{ iv.title || 'Без названия' }}</h3>
              <div class="iv-meta">
                <span class="badge badge-muted">{{ iv.platform }}</span>
                <span class="iv-count">{{ iv.question_count || 0 }} вопросов</span>
              </div>
            </div>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
          </div>
          <div v-if="interviewVideos.length === 0" class="empty-state"><p>Нет записей</p></div>
        </div>
      </div>

      <!-- Interview Mode -->
      <div v-if="mode === 'interview'" class="interview container-sm">
        <div class="iv-header">
          <button class="btn btn-ghost btn-icon" @click="mode = 'select'">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          </button>
          <h3>{{ currentInterviewTitle }}</h3>
          <span class="iv-counter">{{ interviewIndex + 1 }} / {{ interviewQuestions.length }}</span>
        </div>

        <div v-if="currentInterviewQuestion" class="iv-card card">
          <span class="badge" :class="diffBadge(currentInterviewQuestion.difficulty)" style="margin-bottom:.75rem">{{ currentInterviewQuestion.difficulty }}</span>
          <h2>{{ currentInterviewQuestion.question }}</h2>
          <div v-if="showInterviewAnswer" class="iv-answer" v-html="formatAnswer(currentInterviewQuestion.answer || 'Ответ не добавлен')"></div>
          <div class="iv-actions">
            <button v-if="!showInterviewAnswer" class="btn btn-primary" @click="showInterviewAnswer = true">Показать ответ</button>
            <button v-else class="btn btn-secondary" @click="nextInterviewQuestion" :disabled="interviewIndex >= interviewQuestions.length - 1">Следующий →</button>
          </div>
        </div>

        <div v-if="interviewIndex >= interviewQuestions.length - 1 && showInterviewAnswer" class="iv-done">
          <p>✅ Все вопросы пройдены!</p>
          <button class="btn btn-secondary" @click="mode = 'select'">Вернуться</button>
        </div>
      </div>

    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import BrandIcon from '../components/BrandIcon.vue'
import api from '../api/client'

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
const flashcardProgress = computed(() => {
  if (!flashcards.value.length) return 0
  return Math.round(((currentCardIndex.value + (sessionComplete.value ? 1 : 0)) / flashcards.value.length) * 100)
})

const diffBadge = (d) => ({ junior: 'badge-ok', middle: 'badge-warn', senior: 'badge-err' }[d] || 'badge-muted')
const formatAnswer = (t) => t ? t.replace(/\n/g, '<br>') : ''

const flipCard = () => { cardFlipped.value = !cardFlipped.value }

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
  if (e.code === 'Space') { e.preventDefault(); flipCard() }
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
  try { const r = await api.getQuestions(); const qs = r.data.questions || []; totalQuestions.value = r.data.total || qs.length; topics.value = [...new Set(qs.map(q => q.topic).filter(Boolean))].sort() } catch { loadError.value = 'Не удалось загрузить список вопросов' }
  try { const r = await api.getSM2Cards({}); sm2Stats.value = r.data.stats || { total: 0, new: 0, review: 0, learned: 0 }; repeatCount.value = sm2Stats.value.review } catch { loadError.value = loadError.value || 'Не удалось загрузить статистику SM-2' }
  try { const r = await api.getProcessedVideos(); interviewVideos.value = r.data?.videos || []; availableInterviews.value = interviewVideos.value.length } catch { availableInterviews.value = 0; loadError.value = loadError.value || 'Не удалось загрузить записи' }
}

const loadFlashcards = async () => {
  loadingCards.value = true
  try {
    const params = {}
    if (selectedTopic.value) params.topic = selectedTopic.value
    if (selectedDifficulty.value) params.difficulty = selectedDifficulty.value
    const r = await api.getSM2Cards(params)
    let cards = r.data.cards || []
    if (!prioritizeRepeat.value) { for (let i = cards.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [cards[i], cards[j]] = [cards[j], cards[i]] } }
    flashcards.value = cards.slice(0, cardCount.value)
    currentCardIndex.value = 0; knownCount.value = 0; repeatQueue.value = []; cardFlipped.value = false; sessionComplete.value = false
    mode.value = 'flashcard'
  } catch (e) { console.error(e); loadError.value = 'Не удалось подготовить карточки. Попробуйте снова.' }
  loadingCards.value = false
}

const startFlashcards = () => { mode.value = 'flashcard-setup' }
const startInterview = async () => {
  mode.value = 'interview-setup'; loadingInterviews.value = true
  try { const r = await api.getProcessedVideos(); interviewVideos.value = r.data?.videos || [] } catch { loadError.value = 'Не удалось получить список записей.' }
  loadingInterviews.value = false
}
const startInterviewSession = async (v) => {
  currentInterviewTitle.value = v.title || 'Собеседование'
  try { const r = await api.getVideoQuestions(v.id); interviewQuestions.value = r.data?.questions || [] } catch { loadError.value = 'Не удалось загрузить вопросы выбранной записи.' }
  interviewIndex.value = 0; showInterviewAnswer.value = false; mode.value = 'interview'
}
</script>

<style scoped>
.page-heading { font-size: 1.85rem; font-weight: 700; text-align: center; margin-bottom: .3rem; }
.page-desc { text-align: center; color: var(--c-text-3); font-size: 1rem; margin-bottom: 1.75rem; }

/* SM-2 stats */
.sm2-row { display: flex; justify-content: center; gap: .75rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.sm2-pill { display: flex; align-items: center; gap: .35rem; padding: .45rem .95rem; border-radius: var(--r-full); font-size: .92rem; font-weight: 600; }
.sm2-pill span { font-weight: 800; font-size: 1.05rem; }
.sm2-pill.new     { background: var(--c-brand-bg); color: var(--c-brand-h); }
.sm2-pill.review  { background: var(--c-warn-bg);  color: var(--c-warn); }
.sm2-pill.learned { background: var(--c-ok-bg);    color: var(--c-ok); }

/* Mode cards */
.mode-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.mode-card { padding: 2rem; text-align: center; cursor: pointer; }
.mode-card { position: relative; overflow: hidden; }
.mode-card::after {
  content: '';
  position: absolute;
  right: -34px;
  top: -34px;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(130deg, color-mix(in srgb, var(--c-brand) 40%, transparent), transparent);
  opacity: .34;
}
.mc-icon { margin-bottom: .85rem; display:flex; justify-content:center; }
.mode-card h3 { font-size: 1.22rem; font-weight: 600; margin-bottom: .4rem; }
.mode-card p { font-size: .97rem; color: var(--c-text-3); line-height: 1.55; margin-bottom: .85rem; }
.mc-footer { display: flex; gap: .4rem; justify-content: center; flex-wrap: wrap; }

/* Setup */
.form-stack { display: flex; flex-direction: column; gap: 1.1rem; margin-top: 1.25rem; }
.field { display: flex; flex-direction: column; gap: .35rem; }
.field label { font-size: .85rem; color: var(--c-text-2); font-weight: 500; }
.range { width: 100%; accent-color: var(--c-brand); }
.check-label { display: flex; align-items: center; gap: .5rem; font-size: .88rem; color: var(--c-text-2); cursor: pointer; }
.check-label input { accent-color: var(--c-brand); }

/* Flashcard */
.fc-mode { display: flex; flex-direction: column; align-items: center; }
.fc-top { display: flex; align-items: center; gap: 1rem; width: 100%; margin-bottom: 1.5rem; }
.fc-progress-area { flex: 1; text-align: center; }
.fc-counter { font-size: .82rem; color: var(--c-text-3); margin-bottom: .3rem; display: block; }
.fc-stats { display: flex; gap: .35rem; }

/* 3D Flip */
.fc-scene {
  width: 100%;
  max-width: 720px;
  min-height: 360px;
  perspective: 1000px;
  cursor: pointer;
  margin-bottom: 1.5rem;
}
.fc-card {
  width: 100%;
  min-height: 360px;
  position: relative;
  transform-style: preserve-3d;
  transition: transform .5s var(--ease);
}
.fc-card.flipped { transform: rotateY(180deg); }
.fc-face {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-md);
}
.fc-back {
  transform: rotateY(180deg);
  overflow-y: auto;
  justify-content: flex-start;
  align-items: flex-start;
}
.fc-tags { display: flex; gap: .4rem; margin-bottom: 1.25rem; }
.fc-question { font-size: 1.5rem; font-weight: 600; text-align: center; line-height: 1.5; color: var(--c-text); }
.fc-hint { margin-top: 1.5rem; font-size: .78rem; color: var(--c-text-4); display: flex; align-items: center; gap: .35rem; }
.fc-hint kbd, .fc-btn kbd {
  background: var(--c-bg-2);
  border: 1px solid var(--c-border);
  border-radius: 4px;
  padding: .05rem .3rem;
  font-size: .68rem;
  color: var(--c-text-4);
  font-family: inherit;
}
.fc-answer { font-size: 1rem; color: var(--c-text-2); line-height: 1.75; width: 100%; }

/* Action buttons */
.fc-actions { display: flex; gap: .75rem; width: 100%; max-width: 420px; }
.fc-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: .5rem;
  padding: .8rem 1rem;
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  background: var(--c-surface);
  color: var(--c-text);
  font-size: .9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--dur) var(--ease);
}
.fc-btn.repeat:hover { background: var(--c-warn-bg); border-color: var(--c-warn); color: var(--c-warn); }
.fc-btn.known:hover  { background: var(--c-ok-bg);   border-color: var(--c-ok);   color: var(--c-ok); }

/* Results */
.fc-results { padding: 2.5rem; text-align: center; max-width: 440px; width: 100%; }
.fr-emoji { font-size: 3rem; margin-bottom: .75rem; }
.fc-results h2 { font-size: 1.3rem; margin-bottom: 1.25rem; }
.fr-stats { display: flex; justify-content: center; gap: 2rem; margin-bottom: 1.5rem; }
.fr-s { display: flex; flex-direction: column; align-items: center; }
.fr-val { font-size: 1.75rem; font-weight: 800; }
.fr-val.ok { color: var(--c-ok); }
.fr-val.warn { color: var(--c-warn); }
.fr-lbl { font-size: .75rem; color: var(--c-text-3); }
.fr-actions { display: flex; flex-direction: column; gap: .5rem; }

/* Interview */
.iv-list { display: flex; flex-direction: column; gap: .5rem; }
.iv-item { display: flex; align-items: center; justify-content: space-between; padding: 1rem 1.15rem; cursor: pointer; }
.iv-info h3 { font-size: 1rem; font-weight: 600; margin-bottom: .3rem; }
.iv-meta { display: flex; align-items: center; gap: .5rem; }
.iv-count { font-size: .78rem; color: var(--c-text-3); }
.iv-item svg { color: var(--c-text-4); }

.iv-header { display: flex; align-items: center; gap: .75rem; margin-bottom: 1.25rem; }
.iv-header h3 { flex: 1; font-size: 1rem; }
.iv-counter { font-size: .82rem; color: var(--c-text-3); white-space: nowrap; }

.iv-card { padding: 2rem; text-align: center; }
.iv-card h2 { font-size: 1.3rem; font-weight: 600; line-height: 1.45; margin-bottom: 1.25rem; }
.iv-answer { text-align: left; color: var(--c-text-2); line-height: 1.7; background: var(--c-bg-2); border-radius: var(--r-md); padding: 1.25rem; margin-bottom: 1.25rem; font-size: .96rem; }
.iv-actions { display: flex; justify-content: center; gap: .75rem; }
.iv-done { text-align: center; padding: 1.5rem; color: var(--c-text-2); margin-top: 1rem; }

.center-block { display: flex; justify-content: center; padding: 3rem; }
.empty-state { text-align: center; padding: 3rem; color: var(--c-text-3); }

@media (max-width: 640px) {
  .mode-grid { grid-template-columns: 1fr; }
  .fc-actions { flex-direction: column; }
  .fc-scene { min-height: 260px; }
  .fc-card { min-height: 260px; }
}
</style>
