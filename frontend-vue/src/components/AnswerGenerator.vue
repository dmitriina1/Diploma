<template>
  <div class="answer-generator">
    <div class="generator-header">
      <h3>
        <i class="pi pi-sparkles"></i>
        Генерация ответов
      </h3>
      <p class="help-text">
        Используйте LLM API для автоматической генерации ответов на вопросы
      </p>
    </div>
    
    <div class="filters">
      <InputText v-model="searchQuery" 
                 placeholder="Поиск вопросов без ответа..." 
                 class="search-input" />
      
      <Dropdown v-model="filterTopic" 
                :options="topicOptions" 
                optionLabel="label" 
                optionValue="value" 
                placeholder="Все технологии" />
    </div>
    
    <DataTable :value="filteredQuestions" 
               :loading="loading"
               showGridlines
               stripedRows
               :paginator="true"
               :rows="5"
               class="generator-table">
      <Column field="question" header="Вопрос" style="min-width: 350px">
        <template #body="slotProps">
          <div class="question-cell">
            {{ slotProps.data.question }}
          </div>
        </template>
      </Column>
      
      <Column field="topic" header="Технология" style="width: 150px">
        <template #body="slotProps">
          <Tag :value="slotProps.data.topic" severity="info" />
        </template>
      </Column>
      
      <Column field="difficulty" header="Сложность" style="width: 120px">
        <template #body="slotProps">
          <Tag :value="slotProps.data.difficulty" 
               :severity="getDifficultySeverity(slotProps.data.difficulty)" />
        </template>
      </Column>
      
      <Column header="Ответ" style="width: 120px">
        <template #body="slotProps">
          <Tag v-if="slotProps.data.answer" 
               value="Есть" 
               severity="success" 
               icon="pi pi-check" />
          <Tag v-else 
               value="Нет" 
               severity="warning" 
               icon="pi pi-times" />
        </template>
      </Column>
      
      <Column header="Действия" style="width: 150px">
        <template #body="slotProps">
          <Button :label="slotProps.data.answer ? 'Перегенерировать' : 'Сгенерировать'" 
                  :icon="generatingIds.has(slotProps.data.id) ? 'pi pi-spin pi-spinner' : 'pi pi-sparkles'" 
                  severity="info" 
                  text 
                  @click="generateAnswer(slotProps.data.id)" 
                  :disabled="generatingIds.has(slotProps.data.id)" />
        </template>
      </Column>
    </DataTable>
    
    <div class="bulk-generate">
      <Button label="Сгенерировать для всех без ответа" 
              icon="pi pi-bolt" 
              severity="info" 
              @click="generateBulk" 
              :disabled="bulkGenerating || questionsWithoutAnswers === 0"
              :loading="bulkGenerating" />
      <span v-if="questionsWithoutAnswers > 0" class="count-info">
        {{ questionsWithoutAnswers }} вопросов без ответа
      </span>
    </div>
    
    <Dialog v-model:visible="showResultDialog" 
            header="Результат генерации" 
            :modal="true"
            :style="{ width: '700px' }">
      <div v-if="generatedAnswer" class="answer-result">
        <h4>Вопрос:</h4>
        <p class="question-text">{{ currentQuestion?.question }}</p>
        
        <Divider />
        
        <h4>Сгенерированный ответ:</h4>
        <div class="answer-text">{{ generatedAnswer }}</div>
        
        <Message severity="info" :closable="false">
          <small>Ответ был автоматически сохранен</small>
        </Message>
      </div>
      
      <template #footer>
        <Button label="Закрыть" icon="pi pi-times" @click="showResultDialog = false" text />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuestionsStore } from '../store'

const questionsStore = useQuestionsStore()

const loading = ref(false)
const searchQuery = ref('')
const filterTopic = ref(null)
const generatingIds = ref(new Set())
const bulkGenerating = ref(false)
const showResultDialog = ref(false)
const generatedAnswer = ref(null)
const currentQuestion = ref(null)

const topicOptions = computed(() => {
  return [
    { label: 'Все технологии', value: null },
    ...questionsStore.topics.map(topic => ({ label: topic, value: topic }))
  ]
})

const questionsWithoutAnswers = computed(() => {
  return questionsStore.approvedQuestions.filter(q => !q.answer).length
})

const filteredQuestions = computed(() => {
  let questions = questionsStore.approvedQuestions
  
  if (filterTopic.value) {
    questions = questions.filter(q => q.topic === filterTopic.value)
  }
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    questions = questions.filter(q => q.question.toLowerCase().includes(query))
  }
  
  return questions
})

const getDifficultySeverity = (difficulty) => {
  const severities = {
    junior: 'success',
    middle: 'warning',
    senior: 'danger'
  }
  return severities[difficulty] || 'info'
}

const generateAnswer = async (questionId) => {
  generatingIds.value.add(questionId)
  
  try {
    const response = await questionsStore.generateAnswer(questionId)
    
    // Show result dialog
    currentQuestion.value = questionsStore.questions.find(q => q.id === questionId)
    generatedAnswer.value = response.answer
    showResultDialog.value = true
    
    // Refresh questions to get updated answer
    await questionsStore.fetchQuestions()
  } catch (error) {
    console.error('Failed to generate answer:', error)
    alert('Не удалось сгенерировать ответ. Проверьте настройки LLM API.')
  } finally {
    generatingIds.value.delete(questionId)
  }
}

const generateBulk = async () => {
  if (!confirm(`Начать генерацию ответов для ${questionsWithoutAnswers.value} вопросов? Это может занять некоторое время.`)) {
    return
  }
  
  bulkGenerating.value = true
  
  const questionsToGenerate = questionsStore.approvedQuestions.filter(q => !q.answer)
  
  let successCount = 0
  let failCount = 0
  
  for (const question of questionsToGenerate) {
    try {
      await questionsStore.generateAnswer(question.id)
      successCount++
    } catch (error) {
      console.error(`Failed to generate answer for question ${question.id}:`, error)
      failCount++
    }
    
    // Small delay to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
  
  bulkGenerating.value = false
  
  alert(`Генерация завершена!\nУспешно: ${successCount}\nОшибок: ${failCount}`)
  
  await questionsStore.fetchQuestions()
}

onMounted(async () => {
  loading.value = true
  await questionsStore.fetchQuestions()
  loading.value = false
})
</script>

<style scoped>
.answer-generator {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.generator-header h3 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.5rem 0;
}

.help-text {
  margin: 0;
  color: var(--text-color-secondary);
  font-size: 0.9rem;
}

.filters {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-input {
  flex: 1;
  min-width: 300px;
}

.question-cell {
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bulk-generate {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.count-info {
  color: var(--text-color-secondary);
  font-size: 0.9rem;
}

.answer-result {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.question-text {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
}

.answer-text {
  background: rgba(255, 255, 255, 0.05);
  padding: 1rem;
  border-radius: 8px;
  line-height: 1.6;
  white-space: pre-wrap;
}

h4 {
  margin: 0;
  color: var(--primary-color);
}
</style>
