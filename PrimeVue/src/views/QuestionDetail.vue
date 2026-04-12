<template>
  <div class="page">
    <NavBar />
    <div class="container" style="padding-top:1.5rem; padding-bottom:3rem;">

      <!-- Top bar -->
      <div class="top-bar">
        <router-link to="/interview-questions" class="btn btn-ghost btn-sm btn-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        </router-link>
        <div class="top-actions">
          <button class="btn btn-secondary btn-sm" @click="toggleBookmark">
            <svg width="16" height="16" viewBox="0 0 24 24" :fill="isBookmarked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
            {{ isBookmarked ? 'В закладках' : 'Сохранить' }}
          </button>
        </div>
      </div>

      <div v-if="loading" class="center-block"><div class="spinner"></div></div>

      <template v-else-if="question">
        <!-- Question Header -->
        <div class="q-header">
          <h1>{{ question.question }}</h1>
          <div class="q-meta">
            <span class="badge badge-info">{{ question.topic }}</span>
            <span class="badge" :class="diffBadge(question.difficulty)">{{ question.difficulty }}</span>
            <span v-if="question.probability" class="meta-prob">{{ question.probability.toFixed(0) }}% вероятность</span>
            <span v-for="tag in (question.tags || [])" :key="tag" class="badge badge-muted">{{ tag }}</span>
          </div>
        </div>

        <!-- AI Answer -->
        <section class="section" v-if="question.answer">
          <h2 class="sec-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--c-brand)" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v4a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>
            Ответ
          </h2>
          <div class="answer-body" v-html="formatAnswer(question.answer)"></div>
        </section>

        <section class="section">
          <h2 class="sec-title">Моя заметка</h2>
          <textarea v-model="note" class="input" rows="3" placeholder="Ваши короткие заметки по вопросу"></textarea>
          <div class="inline-actions">
            <button class="btn btn-secondary btn-sm" @click="saveNote" :disabled="savingNote">{{ savingNote ? 'Сохранение...' : 'Сохранить заметку' }}</button>
            <span v-if="noteMsg" class="meta-prob">{{ noteMsg }}</span>
          </div>
        </section>

        <!-- Community Answers -->
        <section class="section">
          <h2 class="sec-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--c-brand)" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            Ответы сообщества
            <span class="sec-count">{{ userAnswers.length }}</span>
          </h2>

          <!-- Add answer -->
          <div class="add-answer">
            <textarea v-model="newAnswer" class="input" placeholder="Напишите свой ответ..." rows="3"></textarea>
            <button class="btn btn-primary btn-sm" @click="submitAnswer" :disabled="!newAnswer.trim()">Отправить</button>
          </div>

          <div v-if="userAnswers.length" class="answers-list">
            <div v-for="a in userAnswers" :key="a.id" class="ua-card card">
              <div class="ua-top">
                <span class="ua-author">{{ a.user_name || 'Аноним' }}</span>
                <span class="ua-date">{{ formatDate(a.created_at) }}</span>
              </div>
              <div class="ua-text" v-html="formatAnswer(a.answer_text)"></div>
              <div class="ua-bottom">
                <div class="vote-group">
                  <button class="vote-btn" :class="{ active: a.user_vote === 'up' }" @click="vote(a, 'up')">▲ {{ a.upvotes || 0 }}</button>
                  <button class="vote-btn down" :class="{ active: a.user_vote === 'down' }" @click="vote(a, 'down')">▼ {{ a.downvotes || 0 }}</button>
                </div>
                <button v-if="a.is_own" class="btn btn-ghost btn-sm" @click="deleteAnswer(a.id)" style="color:var(--c-err)">Удалить</button>
              </div>
            </div>
          </div>
        </section>

        <section class="section">
          <h2 class="sec-title">Обратная связь</h2>
          <div class="feedback-wrap card">
            <div class="feedback-row">
              <select v-model="feedbackType" class="input">
                <option value="suggestion">Предложение</option>
                <option value="report">Ошибка в вопросе</option>
                <option value="answer_quality">Качество ответа</option>
                <option value="like">Понравилось</option>
                <option value="dislike">Не понравилось</option>
              </select>
              <select v-model.number="feedbackRating" class="input">
                <option :value="null">Без рейтинга</option>
                <option :value="5">5</option>
                <option :value="4">4</option>
                <option :value="3">3</option>
                <option :value="2">2</option>
                <option :value="1">1</option>
              </select>
            </div>
            <textarea v-model="feedbackComment" class="input" rows="3" placeholder="Что улучшить?" />
            <div class="inline-actions">
              <button class="btn btn-primary btn-sm" @click="sendFeedback" :disabled="sendingFeedback || !feedbackComment.trim()">{{ sendingFeedback ? 'Отправка...' : 'Отправить' }}</button>
              <span v-if="feedbackMsg" class="meta-prob">{{ feedbackMsg }}</span>
            </div>
          </div>
        </section>

        <!-- Similar questions -->
        <section class="section" v-if="similar.length">
          <h2 class="sec-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--c-brand)" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" x2="12.01" y1="17" y2="17"/></svg>
            Похожие вопросы
          </h2>
          <div class="similar-list">
            <router-link v-for="s in similar" :key="s.id" :to="`/question/${s.id}`" class="sim-row card card-hover">
              <span class="sim-text">{{ s.question }}</span>
              <span class="badge badge-info" style="flex-shrink:0">{{ s.topic }}</span>
            </router-link>
          </div>
        </section>
      </template>

      <div v-else class="empty-state"><p>Вопрос не найден</p></div>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import api from '../api/client'
import { trackMetrikaGoal } from '../utils/metrika'

const route = useRoute()
const loading = ref(true)
const question = ref(null)
const similar = ref([])
const userAnswers = ref([])
const newAnswer = ref('')
const isBookmarked = ref(false)
const note = ref('')
const noteMsg = ref('')
const savingNote = ref(false)

const feedbackType = ref('suggestion')
const feedbackRating = ref(null)
const feedbackComment = ref('')
const feedbackMsg = ref('')
const sendingFeedback = ref(false)

const diffBadge = (d) => ({ junior: 'badge-ok', middle: 'badge-warn', senior: 'badge-err' }[d] || 'badge-muted')
const formatAnswer = (t) => t ? t.replace(/\n/g, '<br>') : ''
const formatDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' }) : ''

async function loadQuestion() {
  loading.value = true
  try {
    const r = await api.getPublicQuestionDetail(route.params.id)
    question.value = r.data
    if (question.value?.id) {
      trackMetrikaGoal('open_question', {
        question_id: Number(question.value.id) || Number(route.params.id) || 0,
        topic: question.value.topic || 'unknown'
      })
    }

    // check bookmark
    try { const bk = await api.getBookmarks(); isBookmarked.value = (bk.data.bookmarks || []).some(b => b.question_id == route.params.id) } catch {}

    // similar
    if (question.value?.question) {
      try { const s = await api.getSimilarQuestions(question.value.question, 5); similar.value = (s.data.similar || []).filter(q => q.id != route.params.id) } catch {}
    }

    // user answers
    try { const ua = await api.getUserAnswers(route.params.id); userAnswers.value = ua.data.answers || [] } catch {}

    // personal note
    try { const n = await api.getNote(parseInt(route.params.id)); note.value = n.data.note || '' } catch { note.value = '' }
  } catch (e) { console.error(e) }
  loading.value = false
}

async function toggleBookmark() {
  try {
    if (isBookmarked.value) { await api.removeBookmark(parseInt(route.params.id)); isBookmarked.value = false }
    else { await api.addBookmark(parseInt(route.params.id)); isBookmarked.value = true }
  } catch {}
}

async function submitAnswer() {
  if (!newAnswer.value.trim()) return
  try {
    const authUser = JSON.parse(localStorage.getItem('auth_user') || 'null')
    await api.createUserAnswer(route.params.id, newAnswer.value, authUser?.display_name || authUser?.username || 'Аноним')
    newAnswer.value = ''
    const ua = await api.getUserAnswers(route.params.id); userAnswers.value = ua.data.answers || []
  } catch {}
}

async function vote(answer, type) {
  try { await api.voteUserAnswer(answer.id, type); const ua = await api.getUserAnswers(route.params.id); userAnswers.value = ua.data.answers || [] } catch {}
}

async function deleteAnswer(id) {
  try { await api.deleteUserAnswer(id); const ua = await api.getUserAnswers(route.params.id); userAnswers.value = ua.data.answers || [] } catch {}
}

async function saveNote() {
  savingNote.value = true
  noteMsg.value = ''
  try {
    await api.saveNote(parseInt(route.params.id), note.value)
    noteMsg.value = 'Сохранено'
  } catch {
    noteMsg.value = 'Ошибка сохранения'
  } finally {
    savingNote.value = false
    setTimeout(() => { noteMsg.value = '' }, 2000)
  }
}

async function sendFeedback() {
  if (!feedbackComment.value.trim()) return
  sendingFeedback.value = true
  feedbackMsg.value = ''
  try {
    await api.createFeedback({
      question_id: parseInt(route.params.id),
      feedback_type: feedbackType.value,
      rating: feedbackRating.value,
      comment: feedbackComment.value,
      user_session: api.getUserSession()
    })
    feedbackComment.value = ''
    feedbackRating.value = null
    feedbackMsg.value = 'Спасибо, отправили!'
  } catch {
    feedbackMsg.value = 'Не удалось отправить'
  } finally {
    sendingFeedback.value = false
    setTimeout(() => { feedbackMsg.value = '' }, 2500)
  }
}

onMounted(loadQuestion)
watch(() => route.params.id, loadQuestion)
</script>

<style scoped>
.top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.top-actions { display: flex; gap: .5rem; }

.center-block { display: flex; justify-content: center; padding: 3rem; }
.empty-state { text-align: center; padding: 4rem; color: var(--c-text-3); }

.q-header { margin-bottom: 2rem; }
.q-header h1 { font-size: 1.9rem; font-weight: 700; line-height: 1.35; margin-bottom: .85rem; }
.q-meta { display: flex; align-items: center; gap: .4rem; flex-wrap: wrap; }
.meta-prob { font-size: .78rem; color: var(--c-text-3); }

/* Sections */
.section { margin-bottom: 2rem; }
.sec-title {
  display: flex;
  align-items: center;
  gap: .45rem;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--c-text);
  padding-bottom: .6rem;
  border-bottom: 1px solid var(--c-border);
  margin-bottom: 1rem;
}
.sec-count {
  font-size: .7rem;
  background: var(--c-surface-a);
  padding: .1rem .45rem;
  border-radius: var(--r-full);
  color: var(--c-text-2);
  font-weight: 600;
}

.answer-body {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  padding: 1.5rem 1.75rem;
  color: var(--c-text-2);
  line-height: 1.75;
  font-size: 1.05rem;
}

.inline-actions { display: flex; align-items: center; gap: .6rem; margin-top: .5rem; }

.feedback-wrap { padding: .9rem; display: flex; flex-direction: column; gap: .5rem; }
.feedback-row { display: grid; grid-template-columns: 1.2fr .8fr; gap: .5rem; }

/* Community Answers */
.add-answer { display: flex; flex-direction: column; gap: .5rem; margin-bottom: 1.25rem; }
.add-answer .btn { align-self: flex-end; }

.answers-list { display: flex; flex-direction: column; gap: .6rem; }
.ua-card { padding: 1rem 1.15rem; }
.ua-top { display: flex; justify-content: space-between; margin-bottom: .4rem; }
.ua-author { font-size: .9rem; font-weight: 600; color: var(--c-text); }
.ua-date { font-size: .75rem; color: var(--c-text-4); }
.ua-text { font-size: .94rem; color: var(--c-text-2); line-height: 1.65; margin-bottom: .5rem; }
.ua-bottom { display: flex; justify-content: space-between; align-items: center; }
.vote-group { display: flex; gap: .3rem; }
.vote-btn {
  background: var(--c-bg-2);
  border: 1px solid var(--c-border);
  border-radius: var(--r-sm);
  padding: .2rem .5rem;
  font-size: .78rem;
  color: var(--c-text-3);
  cursor: pointer;
  transition: all var(--dur) var(--ease);
}
.vote-btn:hover { border-color: var(--c-ok); color: var(--c-ok); }
.vote-btn.down:hover { border-color: var(--c-err); color: var(--c-err); }
.vote-btn.active { background: var(--c-ok-bg); border-color: var(--c-ok); color: var(--c-ok); }
.vote-btn.down.active { background: var(--c-err-bg); border-color: var(--c-err); color: var(--c-err); }

/* Similar */
.similar-list { display: flex; flex-direction: column; gap: .4rem; }
.sim-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: .75rem;
  padding: .7rem 1rem;
  text-decoration: none;
}
.sim-text { font-size: .94rem; color: var(--c-text-2); }
.sim-row:hover .sim-text { color: var(--c-text); }

@media (max-width: 640px) {
  .q-header h1 { font-size: 1.25rem; }
  .feedback-row { grid-template-columns: 1fr; }
}
</style>
