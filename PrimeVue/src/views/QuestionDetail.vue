<template>
  <div class="page detail-page">
    <NavBar />
    <main class="screen narrow detail">
      <router-link to="/interview-questions" class="back"><i class="pi pi-arrow-left"></i>Назад к списку вопросов</router-link>
      <section v-if="loading" class="empty-panel glass"><div class="loader"></div></section>
      <template v-else>
        <div class="detail-head fade-up">
          <h1>{{ current.question }}</h1>
          <button class="btn small" @click="toggleBookmark"><i :class="bookmarked ? 'pi pi-bookmark-fill' : 'pi pi-bookmark'"></i>{{ bookmarked ? 'В закладках' : 'Сохранить' }}</button>
        </div>
        <div class="detail-tags">
          <span class="tag">{{ current.topic }}</span>
          <span :class="`tag ${current.difficulty}`">{{ current.difficulty }}</span>
          <span class="tag ok"><i class="pi pi-bullseye"></i>{{ Math.round(current.probability || 100) }}% вероятность</span>
        </div>

        <section class="glass block answer">
          <h2><i class="pi pi-comment"></i>Ответ</h2>
          <div class="answer-box" v-html="formatAnswer(current.answer)"></div>
        </section>

        <section class="glass block">
          <h2><i class="pi pi-youtube"></i>Видео с этим вопросом</h2>
          <div class="video-row" v-for="video in videos" :key="video.title">
            <span><i class="pi pi-play"></i>{{ video.title }}</span>
            <b :class="video.source === 'YouTube' ? 'youtube' : 'rutube'">{{ video.source === 'YouTube' ? '▶' : 'R' }}</b>
            <span>{{ video.source }}</span>
            <time>{{ video.time }}</time>
            <a :href="video.url || '#'" target="_blank">Перейти к фрагменту <i class="pi pi-external-link"></i></a>
          </div>
        </section>

        <section class="glass block note">
          <h2><i class="pi pi-pencil"></i>Моя заметка</h2>
          <textarea v-model="note" maxlength="1000" placeholder="Добавьте личную заметку или важные тезисы по этому вопросу..."></textarea>
          <span>{{ note.length }} / 1000</span>
          <button class="btn small" :disabled="savingNote" @click="saveNote">{{ savingNote ? 'Сохранение...' : 'Сохранить' }}</button>
        </section>

        <section class="glass block community">
          <h2><i class="pi pi-users"></i>Ответы сообщества</h2>
          <div class="answer-form">
            <input v-model="newAnswer" placeholder="Поделитесь своим ответом или советом для сообщества..." />
            <button class="btn small" :disabled="!newAnswer.trim()" @click="submitAnswer">Опубликовать</button>
          </div>
          <div class="community-list">
            <article v-for="answer in userAnswers" :key="answer.id">
              <header><b>{{ answer.user_name || 'Аноним' }}</b><span>{{ formatDate(answer.created_at) }}</span></header>
              <p>{{ answer.answer_text }}</p>
              <footer>
                <button @click="vote(answer, 'up')"><i class="pi pi-thumbs-up"></i>{{ answer.upvotes || 0 }}</button>
                <button @click="vote(answer, 'down')"><i class="pi pi-thumbs-down"></i>{{ answer.downvotes || 0 }}</button>
                <button v-if="answer.is_own" @click="deleteAnswer(answer.id)">Удалить</button>
              </footer>
            </article>
          </div>
        </section>

        <section class="glass block feedback">
          <h2><i class="pi pi-link"></i>Обратная связь</h2>
          <div>
            <select v-model="feedbackType">
              <option value="like">Полезно</option>
              <option value="report">Ошибка в вопросе</option>
              <option value="answer_quality">Качество ответа</option>
              <option value="suggestion">Предложение</option>
            </select>
            <input v-model="feedbackComment" maxlength="500" placeholder="Что понравилось или что улучшить?" />
            <span>{{ feedbackComment.length }} / 500</span>
            <button class="btn small" :disabled="sendingFeedback || !feedbackComment.trim()" @click="sendFeedback">Отправить</button>
          </div>
        </section>

        <section class="similar">
          <h2>Похожие вопросы</h2>
          <div class="similar-grid">
            <router-link v-for="item in similar" :key="item.id" :to="`/question/${item.id}`" class="glass">
              <span class="tag">{{ item.topic || 'General' }}</span>
              <b>{{ item.question }}</b>
            </router-link>
          </div>
        </section>
      </template>
      <div v-if="toast" class="toast">{{ toast }}</div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from '../components/NavBar.vue'
import api from '../api/client'
import { questions as fallbackQuestions } from '../data/mock'

const route = useRoute()
const loading = ref(true)
const question = ref(null)
const note = ref('')
const savingNote = ref(false)
const bookmarked = ref(false)
const userAnswers = ref([])
const newAnswer = ref('')
const similar = ref([])
const feedbackType = ref('like')
const feedbackComment = ref('')
const sendingFeedback = ref(false)
const toast = ref('')

const fallback = fallbackQuestions[0]
const current = computed(() => question.value || {
  id: route.params.id,
  question: fallback.title,
  topic: fallback.topic,
  difficulty: fallback.level,
  probability: fallback.probability,
  answer: 'Меня привлекает ваша компания тем, что вы создаёте продукты, которые решают реальные задачи пользователей и приносят ощутимую ценность.\n\nЯ разделяю ваши ценности: ориентацию на качество, постоянное развитие и открытость к новым идеям.\n\nВижу здесь возможности для профессионального роста, интересные задачи и сильную команду, у которой можно учиться и вместе достигать большего.\n\nЯ хочу внести свой вклад в развитие продуктов компании и помогать достигать амбициозных целей.'
})
const videos = computed(() => current.value.videos || [
  { title: 'Собеседование на Backend Developer', source: 'YouTube', time: '12:34' },
  { title: 'Mock interview. Java Developer', source: 'Rutube', time: '08:52' },
  { title: 'Интервью на Frontend Developer', source: 'YouTube', time: '16:41' }
])

const formatAnswer = (text) => String(text || '').split('\n').filter(Boolean).map((p) => `<p>${p}</p>`).join('')
const formatDate = (date) => date ? new Date(date).toLocaleDateString('ru-RU') : 'сегодня'
const showToast = (message) => { toast.value = message; setTimeout(() => { toast.value = '' }, 2200) }

async function loadQuestion() {
  loading.value = true
  try {
    const r = await api.getPublicQuestionDetail(route.params.id)
    question.value = r.data
  } catch {
    question.value = null
  }
  try { const n = await api.getNote(Number(route.params.id)); note.value = n.data.note || '' } catch { note.value = '' }
  try { const b = await api.getBookmarks(); bookmarked.value = (b.data.bookmarks || []).some((item) => item.question_id == route.params.id) } catch {}
  try { const a = await api.getUserAnswers(route.params.id); userAnswers.value = a.data.answers || [] } catch { userAnswers.value = [] }
  try {
    const s = await api.getSimilarQuestions(current.value.question, 4)
    similar.value = (s.data.similar_questions || s.data.similar || []).filter((item) => item.id != route.params.id)
  } catch {
    similar.value = fallbackQuestions.slice(1, 5).map((q) => ({ id: q.id, question: q.title, topic: q.topic }))
  }
  loading.value = false
}

async function toggleBookmark() {
  try {
    if (bookmarked.value) await api.removeBookmark(Number(route.params.id))
    else await api.addBookmark(Number(route.params.id))
    bookmarked.value = !bookmarked.value
    showToast(bookmarked.value ? 'Вопрос сохранён' : 'Удалено из закладок')
  } catch { showToast('Не удалось изменить закладку') }
}

async function saveNote() {
  savingNote.value = true
  try { await api.saveNote(Number(route.params.id), note.value); showToast('Заметка сохранена') }
  catch { showToast('Не удалось сохранить заметку') }
  savingNote.value = false
}

async function submitAnswer() {
  if (!newAnswer.value.trim()) return
  try {
    await api.createUserAnswer(route.params.id, newAnswer.value)
    newAnswer.value = ''
    const a = await api.getUserAnswers(route.params.id)
    userAnswers.value = a.data.answers || []
    showToast('Ответ опубликован')
  } catch { showToast('Не удалось опубликовать ответ') }
}

async function vote(answer, type) {
  try { await api.voteUserAnswer(answer.id, type); answer[type === 'up' ? 'upvotes' : 'downvotes'] = (answer[type === 'up' ? 'upvotes' : 'downvotes'] || 0) + 1 }
  catch { showToast('Голос не отправлен') }
}

async function deleteAnswer(id) {
  try { await api.deleteUserAnswer(id); userAnswers.value = userAnswers.value.filter((a) => a.id !== id) }
  catch { showToast('Не удалось удалить') }
}

async function sendFeedback() {
  sendingFeedback.value = true
  try {
    await api.createFeedback({ question_id: Number(route.params.id), feedback_type: feedbackType.value, comment: feedbackComment.value, user_session: api.getUserSession() })
    feedbackComment.value = ''
    showToast('Спасибо за обратную связь')
  } catch { showToast('Не удалось отправить feedback') }
  sendingFeedback.value = false
}

onMounted(loadQuestion)
watch(() => route.params.id, loadQuestion)
</script>

<style scoped>
.detail { padding-top: 16px; max-width: 1570px; padding-bottom: 80px; }
.back { display: inline-flex; gap: 10px; color: var(--muted); font-weight: 700; margin: 0 0 10px; }
.detail-head { display: flex; justify-content: space-between; align-items: center; gap: 18px; }
h1 { margin: 0; font-size: 32px; letter-spacing: -.03em; }
.detail-tags { display: flex; gap: 12px; margin: 18px 0 24px; }
.block { padding: 16px 18px 20px; margin-bottom: 12px; }
.block h2 { margin: 0 0 14px; display: flex; gap: 12px; align-items: center; font-size: 21px; }
.block h2 i { color: var(--cyan); }
.answer-box { border: 1px solid rgba(91, 132, 159, .13); border-left: 3px solid var(--cyan); border-radius: 8px; padding: 16px 22px; background: rgba(3, 20, 36, .42); color: #fff; line-height: 1.6; }
.answer-box :deep(p) { margin: 0 0 18px; }
.answer-box :deep(p:last-child) { margin-bottom: 0; }
.video-row { min-height: 48px; display: grid; grid-template-columns: 1fr 24px 140px 100px 220px; align-items: center; border-bottom: 1px solid rgba(91, 132, 159, .1); color: #d7dee8; }
.video-row:last-child { border-bottom: 0; }
.video-row span:first-child { display: flex; gap: 12px; align-items: center; }
.video-row span:first-child i { color: var(--muted); }
.youtube { color: red; }
.rutube { color: #d1b377; }
.video-row a { color: var(--cyan); font-weight: 700; }
textarea, input, select { width: 100%; border: 1px solid rgba(91, 132, 159, .15); border-radius: 8px; background: rgba(4, 20, 37, .62); color: var(--text); outline: none; }
textarea { height: 62px; padding: 16px; resize: vertical; }
.note { position: relative; display: grid; gap: 12px; }
.note > span { position: absolute; right: 26px; bottom: 68px; color: var(--muted); }
.note button { justify-self: end; }
.answer-form, .feedback div { display: grid; gap: 12px; align-items: center; }
.answer-form { grid-template-columns: 1fr 160px; }
.feedback div { grid-template-columns: 230px 1fr 80px 160px; }
input, select { height: 48px; padding: 0 16px; }
.feedback span { color: var(--muted); }
.community-list { display: grid; gap: 10px; margin-top: 14px; }
.community-list article { border: 1px solid rgba(91, 132, 159, .12); border-radius: 10px; padding: 16px; background: rgba(3, 20, 36, .35); }
.community-list header, .community-list footer { display: flex; justify-content: space-between; gap: 10px; align-items: center; }
.community-list header span { color: var(--muted); }
.community-list p { color: #dbe5f0; line-height: 1.5; }
.community-list footer { justify-content: flex-start; }
.community-list button { border: 1px solid rgba(83, 137, 174, .2); background: rgba(4, 20, 37, .62); color: var(--text); border-radius: 8px; padding: 8px 12px; }
.similar { margin-top: 32px; }
.similar h2 { font-size: 28px; }
.similar-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.similar a { min-height: 150px; padding: 20px; display: grid; align-content: start; gap: 16px; transition: .18s ease; }
.similar a:hover { transform: translateY(-4px); border-color: var(--line-strong); }
@media (max-width: 1000px) { .video-row, .answer-form, .feedback div, .similar-grid { grid-template-columns: 1fr; gap: 10px; padding: 12px 0; } .detail-head { display: block; } }
</style>
