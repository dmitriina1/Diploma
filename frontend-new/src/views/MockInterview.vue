<template>
  <div class="page">
    <NavBar />
    <div class="container" style="padding-top:2rem;padding-bottom:3rem">
      <div class="mi-head">
        <h1>Mock Interview</h1>
        <p>Проверь себя в режиме имитации собеседования.</p>
      </div>

      <section v-if="mode === 'setup'" class="card mi-setup">
        <div class="field-row">
          <div class="field">
            <label>Технология</label>
            <select v-model="topic" class="input">
              <option value="">Любая</option>
              <option v-for="t in topics" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div class="field">
            <label>Сложность</label>
            <select v-model="difficulty" class="input">
              <option value="">Любая</option>
              <option value="junior">Junior</option>
              <option value="middle">Middle</option>
              <option value="senior">Senior</option>
            </select>
          </div>
          <div class="field">
            <label>Вопросов</label>
            <input v-model.number="count" type="number" min="3" max="30" class="input" />
          </div>
        </div>
        <button class="btn btn-primary" @click="start" :disabled="loading">{{ loading ? 'Запуск...' : 'Начать интервью' }}</button>
      </section>

      <section v-if="mode === 'session'" class="mi-session">
        <div class="card mi-q">
          <div class="mi-top">
            <span class="badge badge-info">{{ currentIndex + 1 }} / {{ questions.length }}</span>
            <span class="badge" :class="diffBadge(currentQuestion?.difficulty)">{{ currentQuestion?.difficulty || 'mixed' }}</span>
          </div>
          <h2>{{ currentQuestion?.question }}</h2>
          <textarea v-model="draftAnswer" class="input" rows="5" placeholder="Напишите ваш ответ..."></textarea>
          <div class="mi-actions">
            <button class="btn btn-err" @click="mark(false)">Не ответил</button>
            <button class="btn btn-ok" @click="mark(true)">Ответил</button>
          </div>
        </div>
      </section>

      <section v-if="mode === 'result'" class="card mi-result">
        <h2>Результат</h2>
        <div class="result-score">{{ result?.score ?? 0 }}%</div>
        <p>Правильных: {{ result?.correct ?? 0 }} из {{ result?.total ?? 0 }}</p>
        <div class="mi-actions">
          <button class="btn btn-secondary" @click="mode = 'setup'">Новая попытка</button>
          <button class="btn btn-ghost" @click="loadHistory">Обновить историю</button>
        </div>
      </section>

      <section class="mi-history card" v-if="history.length">
        <h3>История</h3>
        <div class="hist-row" v-for="h in history" :key="h.id">
          <span>{{ formatDate(h.created_at) }}</span>
          <span>{{ h.topic || 'Любая' }}</span>
          <span>{{ h.difficulty || 'mixed' }}</span>
          <span class="badge badge-brand">{{ h.score }}%</span>
        </div>
      </section>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import api from '../api/client'

const mode = ref('setup')
const loading = ref(false)
const topic = ref('')
const difficulty = ref('')
const count = ref(10)

const questions = ref([])
const topics = ref([])
const currentIndex = ref(0)
const answers = ref([])
const draftAnswer = ref('')
const interviewId = ref(null)
const startedAt = ref(0)
const result = ref(null)
const history = ref([])

const currentQuestion = computed(() => questions.value[currentIndex.value])

const diffBadge = (d) => ({ junior: 'badge-ok', middle: 'badge-warn', senior: 'badge-err' }[d] || 'badge-muted')
const formatDate = (d) => d ? new Date(d).toLocaleString('ru-RU') : ''

async function start() {
  loading.value = true
  try {
    const r = await api.startMockInterview({
      topic: topic.value || null,
      difficulty: difficulty.value || null,
      count: Math.max(3, Math.min(30, count.value || 10))
    })
    interviewId.value = r.data.interview_id
    questions.value = r.data.questions || []
    currentIndex.value = 0
    answers.value = []
    draftAnswer.value = ''
    startedAt.value = Date.now()
    mode.value = questions.value.length ? 'session' : 'setup'
  } finally {
    loading.value = false
  }
}

async function mark(isCorrect) {
  if (!currentQuestion.value) return
  answers.value.push({
    question_id: currentQuestion.value.id,
    is_correct: isCorrect,
    answer_text: draftAnswer.value
  })
  draftAnswer.value = ''

  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value += 1
    return
  }

  const duration_seconds = Math.round((Date.now() - startedAt.value) / 1000)
  const r = await api.submitMockInterview(interviewId.value, { answers: answers.value, duration_seconds })
  result.value = r.data
  mode.value = 'result'
  await loadHistory()
}

async function loadHistory() {
  try {
    const r = await api.getMockInterviewHistory()
    history.value = r.data.interviews || []
  } catch {
    history.value = []
  }
}

onMounted(async () => {
  try {
    const r = await api.getQuestions({ status: 'approved', limit: 500 })
    const qs = r.data.questions || []
    topics.value = [...new Set(qs.map((q) => q.topic).filter(Boolean))].sort()
  } catch {}
  await loadHistory()
})
</script>

<style scoped>
.mi-head { margin-bottom: 1rem; }
.mi-head h1 { font-size: 1.8rem; }
.mi-head p { color: var(--c-text-3); margin-top: .25rem; }
.mi-setup { padding: 1rem; margin-bottom: 1rem; }
.field-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: .75rem; margin-bottom: .75rem; }
.field { display: flex; flex-direction: column; gap: .3rem; }
.field label { font-size: .85rem; color: var(--c-text-3); }
.mi-session { margin-bottom: 1rem; }
.mi-q { padding: 1.25rem; }
.mi-top { display: flex; justify-content: space-between; margin-bottom: .75rem; }
.mi-q h2 { margin-bottom: .75rem; line-height: 1.45; }
.mi-actions { display: flex; gap: .5rem; margin-top: .75rem; }
.mi-result { padding: 1.25rem; margin-bottom: 1rem; }
.result-score { font-size: 3rem; font-weight: 800; color: var(--c-brand); }
.mi-history { padding: 1rem; }
.mi-history h3 { margin-bottom: .75rem; }
.hist-row { display: grid; grid-template-columns: 1.2fr 1fr 1fr .6fr; gap: .5rem; padding: .45rem 0; border-bottom: 1px solid var(--c-border); align-items: center; }
@media (max-width: 860px) {
  .field-row { grid-template-columns: 1fr; }
  .hist-row { grid-template-columns: 1fr 1fr; }
}
</style>
