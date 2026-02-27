<template>
  <div class="mock-page">
    <NavBar />
    
    <div class="page-container">
      <!-- Setup Screen -->
      <div v-if="stage === 'setup'" class="setup-screen">
        <header class="page-header">
          <h1><i class="pi pi-bolt"></i> Мок-интервью</h1>
          <p class="subtitle">Проверьте свои знания в режиме симуляции собеседования</p>
        </header>

        <Card class="setup-card">
          <template #content>
            <div class="setup-form">
              <div class="field">
                <label>Тема</label>
                <Dropdown v-model="config.topic" :options="topicOptions" placeholder="Все темы" class="w-full" showClear editable />
              </div>
              <div class="field">
                <label>Уровень</label>
                <SelectButton v-model="config.difficulty" :options="difficultyOptions" optionLabel="label" optionValue="value" />
              </div>
              <div class="field">
                <label>Количество вопросов</label>
                <div class="count-selector">
                  <Button v-for="n in [5, 10, 15, 20]" :key="n" :label="String(n)" 
                          :outlined="config.count !== n" @click="config.count = n" class="count-btn" />
                </div>
              </div>
              <Button label="Начать интервью" icon="pi pi-play" @click="startInterview" 
                      :loading="loading" class="start-btn" severity="success" size="large" />
            </div>
          </template>
        </Card>

        <!-- История -->
        <section v-if="history.length > 0" class="history-section">
          <h2><i class="pi pi-history"></i> История интервью</h2>
          <div class="history-list">
            <div v-for="h in history" :key="h.id" class="history-item">
              <div class="history-score" :class="getScoreClass(h.score)">{{ Math.round(h.score) }}%</div>
              <div class="history-info">
                <div class="history-topic">{{ h.topic || 'Все темы' }} · {{ h.difficulty || 'Все уровни' }}</div>
                <div class="history-meta">
                  {{ h.correct_answers }}/{{ h.total_questions }} правильно · {{ formatDuration(h.duration_seconds) }}
                  <span class="history-date">{{ formatDate(h.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- Interview in Progress -->
      <div v-if="stage === 'interview'" class="interview-screen">
        <div class="interview-progress">
          <ProgressBar :value="progressPercent" :showValue="false" />
          <div class="progress-text">
            Вопрос {{ currentIndex + 1 }} из {{ questions.length }}
            <span class="timer"><i class="pi pi-clock"></i> {{ formatTimer(elapsed) }}</span>
          </div>
        </div>

        <Card class="question-card-interview">
          <template #content>
            <div class="question-topic">
              <Tag :value="currentQuestion.topic" severity="info" />
              <Tag :value="currentQuestion.difficulty" :severity="difficultyColor(currentQuestion.difficulty)" />
            </div>
            <h2 class="question-text">{{ currentQuestion.question }}</h2>
            
            <!-- User Answer Area -->
            <div class="answer-area" v-if="!showAnswer">
              <Textarea v-model="userAnswer" rows="4" placeholder="Напишите ваш ответ здесь..." class="w-full" />
              <div class="answer-actions">
                <Button label="Показать ответ" icon="pi pi-eye" @click="revealAnswer" severity="warning" />
                <Button label="Пропустить" icon="pi pi-forward" @click="skipQuestion" severity="secondary" outlined />
              </div>
            </div>

            <!-- Revealed Answer -->
            <div class="revealed-answer" v-if="showAnswer">
              <div class="correct-answer">
                <h4><i class="pi pi-check-circle"></i> Эталонный ответ:</h4>
                <div class="answer-text" v-html="formatAnswer(currentQuestion.answer)"></div>
              </div>
              <div class="self-evaluation">
                <p>Оцените свой ответ:</p>
                <div class="eval-buttons">
                  <Button label="Знал ✓" icon="pi pi-check" severity="success" @click="evaluateAndNext(true)" />
                  <Button label="Не знал ✗" icon="pi pi-times" severity="danger" @click="evaluateAndNext(false)" />
                  <Button label="Частично ~" icon="pi pi-minus" severity="warning" @click="evaluateAndNext(false)" />
                </div>
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- Results Screen -->
      <div v-if="stage === 'results'" class="results-screen">
        <header class="results-header">
          <div class="score-circle" :class="getScoreClass(finalScore)">
            <span class="score-value">{{ Math.round(finalScore) }}%</span>
            <span class="score-label">Результат</span>
          </div>
          <h1>Интервью завершено!</h1>
          <p class="results-meta">
            {{ correctCount }}/{{ questions.length }} правильных ответов · {{ formatDuration(elapsed) }}
          </p>
        </header>

        <div class="results-breakdown">
          <div v-for="(a, i) in answers" :key="i" class="result-item" :class="{ correct: a.is_correct, incorrect: !a.is_correct }">
            <span class="result-icon">{{ a.is_correct ? '✓' : '✗' }}</span>
            <span class="result-question">{{ a.question }}</span>
          </div>
        </div>

        <div class="results-actions">
          <Button label="Пройти ещё раз" icon="pi pi-refresh" @click="resetInterview" severity="success" />
          <Button label="На главную" icon="pi pi-home" @click="$router.push('/')" severity="secondary" outlined />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import NavBar from '../components/NavBar.vue'
import api from '../api/client'

const stage = ref('setup') // setup, interview, results
const loading = ref(false)
const questions = ref([])
const currentIndex = ref(0)
const userAnswer = ref('')
const showAnswer = ref(false)
const answers = ref([])
const history = ref([])
const elapsed = ref(0)
let timerInterval = null
const interviewId = ref(null)

const config = ref({ topic: '', difficulty: '', count: 10 })

const topicOptions = ['JavaScript', 'Python', 'Java', 'React', 'Vue', 'Node.js', 'Docker', 'SQL', 'System Design', 'Algorithms', 'DevOps', 'Backend', 'Frontend']

// Ensure session exists
api.getUserSession()

const difficultyOptions = [
  { label: 'Все', value: '' },
  { label: 'Junior', value: 'junior' },
  { label: 'Middle', value: 'middle' },
  { label: 'Senior', value: 'senior' }
]

const currentQuestion = computed(() => questions.value[currentIndex.value] || {})
const progressPercent = computed(() => ((currentIndex.value + 1) / questions.value.length) * 100)
const correctCount = computed(() => answers.value.filter(a => a.is_correct).length)
const finalScore = computed(() => questions.value.length ? (correctCount.value / questions.value.length) * 100 : 0)

const startInterview = async () => {
  loading.value = true
  try {
    const r = await api.startMockInterview({
      topic: config.value.topic,
      difficulty: config.value.difficulty,
      count: config.value.count
    })
    questions.value = r.data.questions
    interviewId.value = r.data.interview_id
    if (questions.value.length === 0) {
      alert('Нет вопросов по выбранным критериям')
      return
    }
    currentIndex.value = 0
    answers.value = []
    showAnswer.value = false
    userAnswer.value = ''
    elapsed.value = 0
    stage.value = 'interview'
    timerInterval = setInterval(() => elapsed.value++, 1000)
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

const revealAnswer = () => { showAnswer.value = true }

const skipQuestion = () => {
  answers.value.push({ question: currentQuestion.value.question, is_correct: false, skipped: true })
  nextQuestion()
}

const evaluateAndNext = (correct) => {
  answers.value.push({ 
    question: currentQuestion.value.question, 
    question_id: currentQuestion.value.id,
    user_answer: userAnswer.value, 
    is_correct: correct 
  })
  nextQuestion()
}

const nextQuestion = () => {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++
    userAnswer.value = ''
    showAnswer.value = false
  } else {
    finishInterview()
  }
}

const finishInterview = async () => {
  clearInterval(timerInterval)
  stage.value = 'results'
  try {
    await api.submitMockInterview(interviewId.value, {
      answers: answers.value,
      duration_seconds: elapsed.value
    })
    await loadHistory()
  } catch (e) { console.error(e) }
}

const resetInterview = () => {
  stage.value = 'setup'
  questions.value = []
  currentIndex.value = 0
  answers.value = []
}

const loadHistory = async () => {
  try {
    const r = await api.getMockInterviewHistory()
    history.value = r.data.interviews || []
  } catch (e) { console.error(e) }
}

const formatTimer = (s) => `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`
const formatDuration = (s) => s ? `${Math.floor(s/60)} мин ${s%60} сек` : '—'
const formatDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : ''
const getScoreClass = (s) => s >= 70 ? 'score-good' : s >= 40 ? 'score-medium' : 'score-bad'
const difficultyColor = (d) => ({ junior: 'success', middle: 'warning', senior: 'danger' }[d] || 'info')
const formatAnswer = (a) => a ? a.replace(/\n/g, '<br>') : '<em>Ответ не указан</em>'

onMounted(loadHistory)
onUnmounted(() => clearInterval(timerInterval))
</script>

<style scoped>
.mock-page { min-height: 100vh; background: linear-gradient(180deg, #0f0f1e 0%, #1a1a2e 50%, #16213e 100%); }
.page-container { max-width: 900px; margin: 0 auto; padding: 1.5rem 2rem 3rem; }
.page-header { margin-bottom: 2rem; }
.page-header h1 {
  display: flex; align-items: center; gap: 0.75rem; font-size: 1.8rem; font-weight: 800;
  background: linear-gradient(135deg, #f59e0b, #ef4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.subtitle { color: rgba(255,255,255,0.5); margin-top: 0.3rem; }
.setup-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; }
.setup-form { display: flex; flex-direction: column; gap: 1.5rem; }
.setup-form label { display: block; margin-bottom: 0.4rem; font-weight: 600; color: rgba(255,255,255,0.7); }
.count-selector { display: flex; gap: 0.5rem; }
.count-btn { min-width: 50px; }
.start-btn { width: 100%; font-weight: 700; margin-top: 0.5rem; }

/* Interview */
.interview-progress { margin-bottom: 1.5rem; }
.progress-text { display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.9rem; color: rgba(255,255,255,0.6); }
.timer { color: #f59e0b; font-weight: 600; }
.question-card-interview { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; }
.question-topic { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.question-text { font-size: 1.3rem; font-weight: 700; color: #e4e4e7; margin-bottom: 1.5rem; line-height: 1.5; }
.answer-area { display: flex; flex-direction: column; gap: 1rem; }
.answer-actions { display: flex; gap: 0.75rem; }
.revealed-answer { margin-top: 1rem; }
.correct-answer { background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.2); border-radius: 12px; padding: 1rem; margin-bottom: 1rem; }
.correct-answer h4 { color: #4ade80; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.4rem; }
.answer-text { color: rgba(255,255,255,0.8); line-height: 1.6; font-size: 0.95rem; }
.self-evaluation p { color: rgba(255,255,255,0.6); margin-bottom: 0.5rem; }
.eval-buttons { display: flex; gap: 0.5rem; }

/* Results */
.results-header { text-align: center; margin-bottom: 2rem; }
.score-circle {
  width: 120px; height: 120px; border-radius: 50%; margin: 0 auto 1rem;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  border: 4px solid; font-weight: 800;
}
.score-value { font-size: 2rem; }
.score-label { font-size: 0.75rem; opacity: 0.7; }
.score-good { border-color: #22c55e; color: #4ade80; background: rgba(34,197,94,0.1); }
.score-medium { border-color: #f59e0b; color: #fbbf24; background: rgba(245,158,11,0.1); }
.score-bad { border-color: #ef4444; color: #f87171; background: rgba(239,68,68,0.1); }
.results-meta { color: rgba(255,255,255,0.5); margin-top: 0.5rem; }
.results-breakdown { display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 2rem; }
.result-item {
  display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 0.8rem;
  background: rgba(255,255,255,0.04); border-radius: 8px; font-size: 0.9rem;
}
.result-item.correct { border-left: 3px solid #22c55e; }
.result-item.incorrect { border-left: 3px solid #ef4444; }
.result-icon { font-weight: 700; width: 20px; }
.result-item.correct .result-icon { color: #4ade80; }
.result-item.incorrect .result-icon { color: #f87171; }
.results-actions { display: flex; gap: 0.75rem; justify-content: center; }

/* History */
.history-section { margin-top: 2.5rem; }
.history-section h2 { display: flex; align-items: center; gap: 0.5rem; font-size: 1.3rem; margin-bottom: 1rem; color: rgba(255,255,255,0.85); }
.history-list { display: flex; flex-direction: column; gap: 0.5rem; }
.history-item {
  display: flex; align-items: center; gap: 1rem; padding: 0.8rem 1rem;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px;
}
.history-score {
  width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 0.85rem;
}
.history-topic { font-weight: 600; color: rgba(255,255,255,0.8); }
.history-meta { font-size: 0.8rem; color: rgba(255,255,255,0.45); margin-top: 0.2rem; }
.history-date { margin-left: 0.5rem; }
</style>
