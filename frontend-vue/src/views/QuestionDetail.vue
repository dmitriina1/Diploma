<template>
  <div class="question-detail-page">
    <NavBar />
    
    <div v-if="loading" class="loading">
      <ProgressSpinner />
      <p>Загрузка...</p>
    </div>
    
    <div v-else-if="!question" class="empty-state">
      <i class="pi pi-exclamation-triangle"></i>
      <h3>Вопрос не найден</h3>
      <Button label="Вернуться" icon="pi pi-arrow-left" @click="$router.push('/')" />
    </div>
    
    <div v-else class="detail-container">
      <div class="detail-header">
        <Button icon="pi pi-arrow-left" 
                label="Назад" 
                text 
                @click="goBack" />
        
        <div class="tags">
          <Tag :value="question.topic" severity="info" />
          <Tag :value="difficultyLabel" :severity="difficultySeverity" />
          <Tag :value="`Вероятность: ${(question.probability || 0).toFixed(0)}%`" 
               :severity="probabilitySeverity" 
               icon="pi pi-chart-line" />
        </div>

        <div class="header-actions">
          <Button icon="pi pi-comment" label="Отзыв" size="small" severity="help"
                  @click="showFeedback = true" />
        </div>
      </div>
      
      <Card class="question-card">
        <template #title>
          <h1>{{ question.question }}</h1>
        </template>
        
        <template #content>
          <Divider />
          
          <div v-if="question.answer" class="answer-section">
            <h3><i class="pi pi-book"></i> Ответ</h3>
            <div class="answer-content" v-html="formatAnswer(question.answer)"></div>
          </div>
          
          <div v-else class="no-answer">
            <i class="pi pi-info-circle"></i>
            <p>Ответ пока не сгенерирован</p>
          </div>
          
          <Divider />

          <!-- Видео, в которых встречался вопрос -->
          <div v-if="questionDetail?.videos?.length > 0" class="videos-section">
            <h3>
              <i class="pi pi-video"></i> 
              Видео с этим вопросом
              <Tag :value="`${questionDetail.videos.length}`" severity="info" />
            </h3>

            <!-- Embedded video player -->
            <div v-if="activeVideoEmbed" class="video-embed">
              <iframe :src="activeVideoEmbed" frameborder="0" allowfullscreen
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      class="embed-iframe"></iframe>
            </div>

            <div class="videos-list">
              <div v-for="v in questionDetail.videos" :key="v.id" class="video-link-card"
                   @click="playVideo(v)">
                <i class="pi pi-play"></i>
                <span class="video-title">{{ v.title || 'Без названия' }}</span>
                <Tag :value="v.platform" size="small" severity="secondary" />
                <span v-if="getVideoTimecode(v)" class="timecode-badge">
                  <i class="pi pi-clock"></i> {{ getVideoTimecode(v) }}
                </span>
                <a :href="buildVideoUrl(v.url, getVideoTimecode(v))" target="_blank" rel="noopener"
                   @click.stop class="external-link">
                  <i class="pi pi-external-link"></i>
                </a>
              </div>
            </div>
          </div>
          
          <Divider />

          <!-- UGC: Ответы пользователей -->
          <div class="ugc-section">
            <h3>
              <i class="pi pi-users"></i> Ответы сообщества
              <Tag :value="`${userAnswers.length}`" severity="secondary" />
            </h3>

            <!-- Форма нового ответа -->
            <div class="ugc-form">
              <Textarea v-model="newAnswerText" placeholder="Напишите свой вариант ответа..." 
                        :autoResize="true" rows="3" class="w-full" />
              <div class="ugc-form-actions">
                <InputText v-model="userName" placeholder="Ваше имя (необязательно)" class="name-input" />
                <Button label="Отправить" icon="pi pi-send" size="small"
                        @click="submitAnswer" :loading="submittingAnswer"
                        :disabled="!newAnswerText || newAnswerText.length < 10" />
              </div>
            </div>

            <!-- Список ответов -->
            <div v-if="userAnswers.length > 0" class="ugc-answers">
              <div v-for="ans in userAnswers" :key="ans.id" class="ugc-answer-card">
                <div class="ugc-vote">
                  <Button icon="pi pi-chevron-up" text size="small" 
                          :severity="ans.my_vote === 'up' ? 'success' : 'secondary'"
                          @click="voteAnswer(ans.id, 'up')" />
                  <span class="vote-count" :class="{ positive: ans.votes > 0, negative: ans.votes < 0 }">
                    {{ ans.votes }}
                  </span>
                  <Button icon="pi pi-chevron-down" text size="small"
                          :severity="ans.my_vote === 'down' ? 'danger' : 'secondary'"
                          @click="voteAnswer(ans.id, 'down')" />
                </div>
                <div class="ugc-content">
                  <div class="ugc-meta">
                    <span class="ugc-author">{{ ans.user_name || 'Аноним' }}</span>
                    <span class="ugc-date">{{ formatDate(ans.created_at) }}</span>
                    <Tag v-if="ans.is_selected" value="Лучший" severity="success" size="small" />
                  </div>
                  <div class="ugc-text" v-html="formatAnswer(ans.answer_text)"></div>
                </div>
              </div>
            </div>
            <div v-else class="ugc-empty">
              <i class="pi pi-comment"></i>
              <p>Пока никто не оставил свой ответ. Будьте первым!</p>
            </div>
          </div>
          
          <Divider />
          
          <div class="metadata">
            <div class="metadata-item">
              <i class="pi pi-calendar"></i>
              <span>Добавлено: {{ formatDate(question.created_at) }}</span>
            </div>
          </div>
          
          <Divider />
          
          <div v-if="similarQuestions.length > 0" class="similar-section">
            <h3><i class="pi pi-sitemap"></i> Похожие вопросы</h3>
            <div class="similar-list">
              <Card v-for="similar in similarQuestions" 
                    :key="similar.id" 
                    class="similar-card"
                    @click="navigateToQuestion(similar.id)">
                <template #title>
                  {{ similar.question }}
                </template>
                <template #content>
                  <div class="similar-meta">
                    <Tag :value="similar.topic" severity="info" size="small" />
                    <span v-if="similar.similarity_score" class="similarity-score">
                      {{ (similar.similarity_score * 100).toFixed(0) }}% схожести
                    </span>
                  </div>
                </template>
              </Card>
            </div>
          </div>
        </template>
      </Card>

      <FeedbackDialog v-model:visible="showFeedback" :questionId="questionId" />
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuestionsStore } from '../store'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import FeedbackDialog from '../components/FeedbackDialog.vue'
import api from '../api/client'

const route = useRoute()
const router = useRouter()
const questionsStore = useQuestionsStore()

const questionId = computed(() => parseInt(route.params.id))
const loading = ref(true)
const similarQuestions = ref([])
const questionDetail = ref(null)
const showFeedback = ref(false)

// UGC
const userAnswers = ref([])
const newAnswerText = ref('')
const userName = ref('')
const submittingAnswer = ref(false)

// Video embed
const activeVideoEmbed = ref(null)

const question = computed(() => {
  return questionDetail.value || questionsStore.questions.find(q => q.id === questionId.value)
})

const difficultyLabel = computed(() => {
  if (!question.value) return ''
  const labels = { junior: 'Junior', middle: 'Middle', senior: 'Senior' }
  return labels[question.value.difficulty] || question.value.difficulty
})

const difficultySeverity = computed(() => {
  if (!question.value) return 'info'
  return { junior: 'success', middle: 'warning', senior: 'danger' }[question.value.difficulty] || 'info'
})

const probabilitySeverity = computed(() => {
  if (!question.value) return 'info'
  const prob = question.value.probability || 0
  if (prob >= 80) return 'danger'
  if (prob >= 50) return 'warning'
  return 'success'
})

const formatDate = (dateString) => {
  if (!dateString) return 'Неизвестно'
  return new Date(dateString).toLocaleDateString('ru-RU', { year: 'numeric', month: 'long', day: 'numeric' })
}

const formatAnswer = (text) => {
  if (!text) return ''
  return text.replace(/\n/g, '<br>')
}

/** Embed timecode into video URL for direct playback at the right moment */
const buildVideoUrl = (url, timecode) => {
  if (!url || !timecode) return url || '#'
  const seconds = parseTimecodeToSeconds(timecode)
  if (seconds <= 0) return url
  try {
    const u = new URL(url)
    // YouTube
    if (u.hostname.includes('youtube.com') || u.hostname.includes('youtu.be')) {
      u.searchParams.set('t', seconds + 's')
      return u.toString()
    }
    // Rutube
    if (u.hostname.includes('rutube.ru')) {
      u.searchParams.set('t', seconds)
      return u.toString()
    }
    // VK
    if (u.hostname.includes('vk.com') || u.hostname.includes('vkvideo.ru')) {
      u.searchParams.set('t', seconds + 's')
      return u.toString()
    }
    // Vimeo
    if (u.hostname.includes('vimeo.com')) {
      u.hash = `t=${seconds}s`
      return u.toString()
    }
    return url
  } catch { return url }
}

const parseTimecodeToSeconds = (tc) => {
  if (!tc) return 0
  // Handle HH:MM:SS or MM:SS or SS
  const parts = tc.toString().split(':').map(Number)
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2]
  if (parts.length === 2) return parts[0] * 60 + parts[1]
  return parseInt(tc) || 0
}

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/interview-questions')
  }
}

/** Build an embeddable video URL (YouTube/VK) with timecode */
const buildEmbedUrl = (url, timecode) => {
  if (!url) return null
  const seconds = parseTimecodeToSeconds(timecode)
  try {
    const u = new URL(url)
    // YouTube
    if (u.hostname.includes('youtube.com') || u.hostname.includes('youtu.be')) {
      let videoId = ''
      if (u.hostname.includes('youtu.be')) {
        videoId = u.pathname.replace('/', '')
      } else {
        videoId = u.searchParams.get('v') || ''
      }
      if (videoId) {
        const start = seconds > 0 ? `?start=${seconds}` : ''
        return `https://www.youtube.com/embed/${videoId}${start}`
      }
    }
  } catch {}
  return null
}

/** Get the timecode for a specific video — prefer per-video timecode, fall back to question timecode */
const getVideoTimecode = (video) => {
  return video.timecode || question.value?.timecode || null
}

const playVideo = (video) => {
  const tc = getVideoTimecode(video)
  const embedUrl = buildEmbedUrl(video.url, tc)
  if (embedUrl) {
    activeVideoEmbed.value = embedUrl
  } else {
    // Fallback: open in new tab
    window.open(buildVideoUrl(video.url, tc), '_blank')
  }
}

// UGC methods
const loadUserAnswers = async () => {
  try {
    const r = await api.getUserAnswers(questionId.value)
    userAnswers.value = r.data.answers || []
  } catch (e) { console.error('Failed to load user answers:', e) }
}

const submitAnswer = async () => {
  if (!newAnswerText.value || newAnswerText.value.length < 10) return
  submittingAnswer.value = true
  try {
    await api.createUserAnswer(questionId.value, newAnswerText.value, userName.value || 'Аноним')
    newAnswerText.value = ''
    await loadUserAnswers()
  } catch (e) {
    console.error('Failed to submit answer:', e)
  }
  submittingAnswer.value = false
}

const voteAnswer = async (answerId, voteType) => {
  try {
    await api.voteUserAnswer(answerId, voteType)
    await loadUserAnswers()
  } catch (e) { console.error('Vote error:', e) }
}

const navigateToQuestion = (id) => {
  router.push({ name: 'QuestionDetail', params: { id } })
}

const loadQuestionDetail = async () => {
  loading.value = true
  questionDetail.value = null
  similarQuestions.value = []
  activeVideoEmbed.value = null
  userAnswers.value = []
  
  try {
    const response = await api.getPublicQuestionDetail(questionId.value)
    questionDetail.value = response.data
    similarQuestions.value = response.data.similar_questions || []
  } catch (error) {
    console.error('Failed to load question detail:', error)
    await questionsStore.fetchQuestions()
  }
  
  // Load UGC answers
  await loadUserAnswers()
  
  loading.value = false
}

onMounted(loadQuestionDetail)
watch(questionId, loadQuestionDetail)
</script>

<style scoped>
.question-detail-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
}
.loading {
  display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem; gap: 1rem;
}
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem; gap: 1rem;
}
.empty-state i { font-size: 4rem; color: var(--text-color-secondary); }
.detail-container { max-width: 1000px; margin: 0 auto; padding: 2rem; }
.detail-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;
}
.tags { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.header-actions { display: flex; gap: 0.5rem; }
.question-card h1 { font-size: 1.8rem; line-height: 1.4; margin: 0; }

.answer-section h3, .similar-section h3, .videos-section h3 {
  display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; color: var(--primary-color);
}
.videos-list { display: flex; flex-direction: column; gap: 0.5rem; }
.answer-content {
  background: rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 8px; line-height: 1.8;
}
.no-answer {
  display: flex; align-items: center; gap: 0.5rem; color: var(--text-color-secondary); padding: 1rem;
}
.metadata { display: flex; flex-direction: column; gap: 1rem; }
.metadata-item { display: flex; align-items: center; gap: 0.5rem; color: var(--text-color-secondary); }
.similar-list { display: flex; flex-direction: column; gap: 1rem; }
.similar-card { cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
.similar-card:hover { transform: translateX(4px); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4); }
.similar-meta { display: flex; align-items: center; gap: 1rem; }
.similarity-score { font-size: 0.85rem; color: var(--text-color-secondary); }

/* Video embed */
.video-embed {
  margin-bottom: 1rem;
  border-radius: 12px;
  overflow: hidden;
  aspect-ratio: 16/9;
  background: #000;
}
.embed-iframe { width: 100%; height: 100%; border: none; }
.video-link-card {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px; color: rgba(255, 255, 255, 0.8); transition: all 0.2s; cursor: pointer;
}
.video-link-card:hover {
  background: rgba(255, 255, 255, 0.08); border-color: var(--primary-color); transform: translateX(4px);
}
.video-link-card .video-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.video-link-card i.pi-play { color: var(--primary-color); }
.timecode-badge {
  display: inline-flex; align-items: center; gap: 0.3rem;
  background: rgba(102, 126, 234, 0.15); border: 1px solid rgba(102, 126, 234, 0.3); border-radius: 6px;
  padding: 0.2rem 0.6rem; font-size: 0.8rem; color: #667eea; font-weight: 600; white-space: nowrap;
}
.external-link { color: rgba(255,255,255,0.4); transition: color 0.2s; }
.external-link:hover { color: var(--primary-color); }

/* UGC Section */
.ugc-section h3 {
  display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; color: var(--primary-color);
}
.ugc-form {
  background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px; padding: 1rem; margin-bottom: 1.5rem;
}
.ugc-form-actions {
  display: flex; gap: 0.75rem; margin-top: 0.75rem; align-items: center;
}
.name-input { flex: 1; max-width: 250px; }
.ugc-answers { display: flex; flex-direction: column; gap: 1rem; }
.ugc-answer-card {
  display: flex; gap: 1rem;
  background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px; padding: 1rem; transition: all 0.2s;
}
.ugc-answer-card:hover { border-color: rgba(255, 255, 255, 0.15); }
.ugc-vote {
  display: flex; flex-direction: column; align-items: center; min-width: 40px;
}
.vote-count { font-weight: 700; font-size: 1rem; color: rgba(255,255,255,0.7); }
.vote-count.positive { color: #22c55e; }
.vote-count.negative { color: #ef4444; }
.ugc-content { flex: 1; }
.ugc-meta {
  display: flex; gap: 0.75rem; align-items: center; margin-bottom: 0.5rem;
  font-size: 0.85rem;
}
.ugc-author { color: var(--primary-color); font-weight: 600; }
.ugc-date { color: rgba(255,255,255,0.4); }
.ugc-text { color: rgba(255,255,255,0.85); line-height: 1.7; }
.ugc-empty {
  text-align: center; padding: 2rem; color: rgba(255,255,255,0.4);
}
.ugc-empty i { font-size: 2rem; display: block; margin-bottom: 0.5rem; }
</style>
