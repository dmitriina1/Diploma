<template>
  <div class="question-approval">
    <div class="approval-header">
      <h3>
        <i class="pi pi-check-square"></i>
        Утверждение вопросов
      </h3>
      <div class="header-actions">
        <span class="count-badge">{{ unapprovedCount }} неутвержденных</span>
        <Button label="Обновить" 
                icon="pi pi-refresh" 
                @click="refresh" 
                text 
                :loading="loading" />
      </div>
    </div>
    
    <div class="filters">
      <InputText v-model="searchQuery" 
                 placeholder="Поиск..." 
                 class="search-input" />
      
      <Dropdown v-model="filterTopic" 
                :options="topicOptions" 
                optionLabel="label" 
                optionValue="value" 
                placeholder="Все технологии" />
      
      <Button :label="selectAll ? 'Снять все' : 'Выбрать все'" 
              icon="pi pi-check" 
              @click="toggleSelectAll" 
              text />
    </div>
    
    <DataTable :value="filteredQuestions" 
               v-model:selection="selectedQuestions"
               dataKey="id"
               :loading="loading"
               showGridlines
               stripedRows
               :paginator="true"
               :rows="10"
               class="approval-table">
      <Column selectionMode="multiple" headerStyle="width: 3rem"></Column>
      
      <Column field="question" header="Вопрос" style="min-width: 300px">
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
      
      <Column field="probability" header="Вероятность" style="width: 120px">
        <template #body="slotProps">
          <Tag v-if="slotProps.data.probability" 
               :value="`${slotProps.data.probability.toFixed(1)}%`" 
               :severity="getProbabilitySeverity(slotProps.data.probability)" />
        </template>
      </Column>
      
      <Column header="Действия" style="width: 150px">
        <template #body="slotProps">
          <div class="actions">
            <Button icon="pi pi-check" 
                    severity="success" 
                    text 
                    @click="approveQuestions([slotProps.data.id])" 
                    v-tooltip.top="'Утвердить'" />
            <Button icon="pi pi-times" 
                    severity="danger" 
                    text 
                    @click="deleteQuestion(slotProps.data.id)" 
                    v-tooltip.top="'Удалить'" />
          </div>
        </template>
      </Column>
    </DataTable>
    
    <div v-if="selectedQuestions.length > 0" class="bulk-actions">
      <span>Выбрано: {{ selectedQuestions.length }}</span>
      <Button label="Утвердить выбранные" 
              icon="pi pi-check" 
              severity="success" 
              @click="approveBulk" />
      <Button label="Удалить выбранные" 
              icon="pi pi-trash" 
              severity="danger" 
              @click="deleteBulk" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useQuestionsStore } from '../store'

const questionsStore = useQuestionsStore()

const loading = ref(false)
const selectedQuestions = ref([])
const searchQuery = ref('')
const filterTopic = ref(null)
const selectAll = ref(false)

const unapprovedCount = computed(() => questionsStore.unapprovedQuestions.length)

const topicOptions = computed(() => {
  return [
    { label: 'Все технологии', value: null },
    ...questionsStore.topics.map(topic => ({ label: topic, value: topic }))
  ]
})

const filteredQuestions = computed(() => {
  let questions = questionsStore.unapprovedQuestions
  
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

const getProbabilitySeverity = (probability) => {
  if (probability >= 80) return 'danger'
  if (probability >= 50) return 'warning'
  return 'success'
}

const toggleSelectAll = () => {
  if (selectAll.value) {
    selectedQuestions.value = []
    selectAll.value = false
  } else {
    selectedQuestions.value = [...filteredQuestions.value]
    selectAll.value = true
  }
}

const refresh = async () => {
  loading.value = true
  await questionsStore.fetchAdminQuestions()
  loading.value = false
}

const approveQuestions = async (questionIds) => {
  loading.value = true
  await questionsStore.approveQuestions(questionIds)
  selectedQuestions.value = []
  selectAll.value = false
  loading.value = false
}

const approveBulk = async () => {
  const ids = selectedQuestions.value.map(q => q.id)
  await approveQuestions(ids)
}

const deleteQuestion = async (questionId) => {
  if (confirm('Вы уверены, что хотите удалить этот вопрос?')) {
    loading.value = true
    await questionsStore.deleteQuestion(questionId)
    loading.value = false
  }
}

const deleteBulk = async () => {
  if (confirm(`Вы уверены, что хотите удалить ${selectedQuestions.value.length} вопросов?`)) {
    loading.value = true
    for (const question of selectedQuestions.value) {
      await questionsStore.deleteQuestion(question.id)
    }
    selectedQuestions.value = []
    selectAll.value = false
    loading.value = false
  }
}

defineExpose({ refresh })
</script>

<style scoped>
.question-approval {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.approval-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.approval-header h3 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.count-badge {
  padding: 0.5rem 1rem;
  background: rgba(255, 193, 7, 0.2);
  border-radius: 20px;
  font-weight: 600;
  color: rgb(255, 193, 7);
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

.actions {
  display: flex;
  gap: 0.5rem;
}

.bulk-actions {
  position: sticky;
  bottom: 0;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.3);
}

.bulk-actions span {
  flex: 1;
  font-weight: 600;
}
</style>
