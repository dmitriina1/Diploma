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
            <div class="videos-list">
              <a v-for="v in questionDetail.videos" :key="v.id" 
                 :href="buildVideoUrl(v.url, question.timecode)" target="_blank" rel="noopener" class="video-link-card">
                <i class="pi pi-play"></i>
                <span class="video-title">{{ v.title || 'Без названия' }}</span>
                <Tag :value="v.platform" size="small" severity="secondary" />
                <span v-if="question.timecode" class="timecode-badge">
                  <i class="pi pi-clock"></i> {{ question.timecode }}
                </span>
              </a>
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
  // Use browser history to go back to whichever page the user came from
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/interview-questions')
  }
}

const navigateToQuestion = (id) => {
  router.push({ name: 'QuestionDetail', params: { id } })
}

const loadQuestionDetail = async () => {
  loading.value = true
  questionDetail.value = null
  similarQuestions.value = []
  
  try {
    const response = await api.getPublicQuestionDetail(questionId.value)
    questionDetail.value = response.data
    similarQuestions.value = response.data.similar_questions || []
  } catch (error) {
    console.error('Failed to load question detail:', error)
    await questionsStore.fetchQuestions()
  }
  
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
.video-link-card {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px; text-decoration: none; color: rgba(255, 255, 255, 0.8); transition: all 0.2s;
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
</style>
