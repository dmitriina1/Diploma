<template>
  <div class="questions-page">
    <NavBar />
    
    <div class="page-header">
      <div class="header-content">
        <Button icon="pi pi-arrow-left" 
                label="Назад" 
                text 
                @click="$router.push('/')" />
        <h1>{{ topic }}</h1>
        <Badge :value="filteredQuestions.length" severity="info" />
      </div>
      
      <div class="filters">
        <div class="filter-group">
          <label>Сложность:</label>
          <SelectButton v-model="selectedDifficulty" 
                        :options="difficultyOptions" 
                        optionLabel="label" 
                        optionValue="value" 
                        :allowEmpty="true" />
        </div>
        
        <div class="filter-group">
          <label>Поиск:</label>
          <InputText v-model="searchQuery" 
                     placeholder="Введите вопрос..." 
                     class="search-input" />
        </div>
        
        <div class="filter-group">
          <label>Сортировка:</label>
          <Dropdown v-model="sortBy" 
                    :options="sortOptions" 
                    optionLabel="label" 
                    optionValue="value" />
        </div>
      </div>
    </div>
    
    <div class="questions-container">
      <div v-if="loading" class="loading">
        <ProgressSpinner />
        <p>Загрузка вопросов...</p>
      </div>
      
      <div v-else-if="filteredQuestions.length === 0" class="empty-state">
        <i class="pi pi-inbox"></i>
        <h3>Вопросы не найдены</h3>
        <p>Попробуйте изменить фильтры или выбрать другую технологию</p>
      </div>
      
      <div v-else class="questions-list">
        <QuestionCard v-for="question in sortedQuestions" 
                      :key="question.id" 
                      :question="question"
                      @view-details="viewDetails" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuestionsStore } from '../store'
import NavBar from '../components/NavBar.vue'
import QuestionCard from '../components/QuestionCard.vue'

const route = useRoute()
const router = useRouter()
const questionsStore = useQuestionsStore()

const topic = computed(() => route.params.topic)
const loading = ref(true)

const selectedDifficulty = ref(null)
const searchQuery = ref('')
const sortBy = ref('probability')

const difficultyOptions = [
  { label: 'Junior', value: 'junior' },
  { label: 'Middle', value: 'middle' },
  { label: 'Senior', value: 'senior' }
]

const sortOptions = [
  { label: 'По вероятности', value: 'probability' },
  { label: 'По дате', value: 'date' },
  { label: 'По алфавиту', value: 'alphabet' }
]

const filteredQuestions = computed(() => {
  let questions = questionsStore.questions.filter(q => q.topic === topic.value)
  
  if (selectedDifficulty.value) {
    questions = questions.filter(q => q.difficulty === selectedDifficulty.value)
  }
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    questions = questions.filter(q => 
      q.question.toLowerCase().includes(query) ||
      (q.answer && q.answer.toLowerCase().includes(query))
    )
  }
  
  return questions
})

const sortedQuestions = computed(() => {
  const questions = [...filteredQuestions.value]
  
  switch (sortBy.value) {
    case 'probability':
      return questions.sort((a, b) => (b.probability || 0) - (a.probability || 0))
    case 'date':
      return questions.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    case 'alphabet':
      return questions.sort((a, b) => a.question.localeCompare(b.question))
    default:
      return questions
  }
})

const viewDetails = (questionId) => {
  router.push({ name: 'QuestionDetail', params: { id: questionId } })
}

onMounted(async () => {
  loading.value = true
  await questionsStore.fetchQuestions()
  loading.value = false
})

watch(topic, async () => {
  loading.value = true
  await questionsStore.fetchQuestions()
  loading.value = false
})
</script>

<style scoped>
.questions-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
}

.page-header {
  background: rgba(255, 255, 255, 0.05);
  padding: 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto 2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-content h1 {
  flex: 1;
  margin: 0;
  font-size: 2rem;
}

.filters {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  font-size: 0.9rem;
  color: var(--text-color-secondary);
}

.search-input {
  min-width: 300px;
}

.questions-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
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
  text-align: center;
  padding: 4rem;
  color: var(--text-color-secondary);
}

.empty-state i {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
