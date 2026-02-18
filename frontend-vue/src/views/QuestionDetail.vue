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
      </div>
      
      <Card class="question-card">
        <template #title>
          <h1>{{ question.question }}</h1>
        </template>
        
        <template #content>
          <Divider />
          
          <div v-if="question.answer" class="answer-section">
            <h3><i class="pi pi-book"></i> Ответ</h3>
            <div class="answer-content">{{ question.answer }}</div>
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
              Видео, в которых встречался вопрос 
              <Tag :value="`${questionDetail.videos.length} из ${questionDetail.total_videos}`" severity="info" />
            </h3>
            <div class="videos-list">
              <a v-for="v in questionDetail.videos" :key="v.id" 
                 :href="v.url" target="_blank" rel="noopener" class="video-link-card">
                <i class="pi pi-external-link"></i>
                <span class="video-title">{{ v.title || 'Без названия' }}</span>
                <Tag :value="v.platform" size="small" severity="secondary" />
              </a>
            </div>
          </div>
          
          <Divider />
          
          <div class="metadata">
            <div class="metadata-item">
              <i class="pi pi-clock"></i>
              <span>Timecode: {{ question.timecode || 'Не указан' }}</span>
            </div>
            
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
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuestionsStore } from '../store'
import NavBar from '../components/NavBar.vue'
import api from '../api/client'

const route = useRoute()
const router = useRouter()
const questionsStore = useQuestionsStore()

const questionId = computed(() => parseInt(route.params.id))
const loading = ref(true)
const similarQuestions = ref([])
const questionDetail = ref(null)

const question = computed(() => {
  // Приоритет - детальные данные из API, иначе из стора
  return questionDetail.value || questionsStore.questions.find(q => q.id === questionId.value)
})

const difficultyLabel = computed(() => {
  if (!question.value) return ''
  const labels = {
    junior: 'Junior',
    middle: 'Middle',
    senior: 'Senior'
  }
  return labels[question.value.difficulty] || question.value.difficulty
})

const difficultySeverity = computed(() => {
  if (!question.value) return 'info'
  const severities = {
    junior: 'success',
    middle: 'warning',
    senior: 'danger'
  }
  return severities[question.value.difficulty] || 'info'
})

const probabilitySeverity = computed(() => {
  if (!question.value) return 'info'
  const prob = question.value.probability || 0
  if (prob >= 80) return 'danger'
  if (prob >= 50) return 'warning'
  return 'success'
})

const platform = computed(() => {
  if (!question.value?.platform) return 'Unknown'
  return question.value.platform
})

const formatDate = (dateString) => {
  if (!dateString) return 'Неизвестно'
  return new Date(dateString).toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const goBack = () => {
  if (question.value?.topic) {
    router.push({ name: 'Questions', params: { topic: question.value.topic } })
  } else {
    router.push('/')
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
    // Fallback на данные из стора
    await questionsStore.fetchQuestions()
  }
  
  loading.value = false
}

onMounted(loadQuestionDetail)

// При переходе на другой вопрос (клик по похожему)
watch(questionId, loadQuestionDetail)
</script>

<style scoped>
.question-detail-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  gap: 1rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  gap: 1rem;
}

.empty-state i {
  font-size: 4rem;
  color: var(--text-color-secondary);
}

.detail-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.tags {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.question-card h1 {
  font-size: 1.8rem;
  line-height: 1.4;
  margin: 0;
}

.answer-section h3,
.similar-section h3,
.videos-section h3 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  color: var(--primary-color);
}

.videos-section h3 .p-tag {
  margin-left: 0.5rem;
}

.videos-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.video-link-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.8);
  transition: all 0.2s;
}

.video-link-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--primary-color);
  transform: translateX(4px);
}

.video-link-card .video-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-link-card i {
  color: var(--primary-color);
}

.answer-content {
  background: rgba(255, 255, 255, 0.05);
  padding: 1.5rem;
  border-radius: 8px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.no-answer {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-color-secondary);
  padding: 1rem;
}

.metadata {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.metadata-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-color-secondary);
}

.metadata-item a {
  color: var(--primary-color);
  text-decoration: none;
}

.metadata-item a:hover {
  text-decoration: underline;
}

.similar-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.similar-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.similar-card:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.similar-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.similarity-score {
  font-size: 0.85rem;
  color: var(--text-color-secondary);
}
</style>
