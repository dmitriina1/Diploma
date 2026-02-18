<template>
  <div class="question-approval">
    <!-- Header -->
    <div class="approval-header">
      <h3>
        <i class="pi pi-check-square"></i>
        Управление вопросами
      </h3>
      <div class="header-actions">
        <Tag :value="`${unapprovedCount} ожидают`" severity="warning" class="count-tag" />
        <Tag :value="`${approvedCount} утверждено`" severity="success" class="count-tag" />
        <Button label="Обновить" icon="pi pi-refresh" @click="refresh" text :loading="loading" />
      </div>
    </div>

    <!-- Filters -->
    <div class="filters">
      <InputText v-model="searchQuery" placeholder="Поиск по тексту вопроса..." class="search-input" />

      <Dropdown v-model="filterTopic" :options="topicOptions" optionLabel="label" optionValue="value"
                placeholder="Все технологии" class="topic-filter" />

      <Dropdown v-model="filterStatus" :options="statusOptions" optionLabel="label" optionValue="value"
                placeholder="Все статусы" class="status-filter" />

      <Button :label="selectAll ? 'Снять все' : 'Выбрать все'" icon="pi pi-check" @click="toggleSelectAll" text />
    </div>

    <!-- Table -->
    <DataTable :value="filteredQuestions"
               v-model:selection="selectedQuestions"
               dataKey="id"
               :loading="loading"
               showGridlines
               stripedRows
               :paginator="true"
               :rows="15"
               :rowsPerPageOptions="[10, 15, 25, 50]"
               @rowClick="onRowClick"
               :rowClass="() => 'clickable-row'"
               class="approval-table"
               paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
               :globalFilterFields="['question', 'topic']">

      <Column selectionMode="multiple" headerStyle="width: 3rem" />

      <Column field="question" header="Вопрос" style="min-width: 300px">
        <template #body="{ data }">
          <div class="question-cell" :title="data.question">{{ data.question }}</div>
        </template>
      </Column>

      <Column field="topic" header="Технология" style="width: 140px">
        <template #body="{ data }">
          <Tag :value="data.topic || '—'" severity="info" />
        </template>
      </Column>

      <Column field="difficulty" header="Сложность" style="width: 110px">
        <template #body="{ data }">
          <Tag :value="getDifficultyLabel(data.difficulty)" :severity="getDifficultySeverity(data.difficulty)" />
        </template>
      </Column>

      <Column field="probability" header="Вероятность" style="width: 130px" sortable>
        <template #body="{ data }">
          <div class="prob-cell">
            <Tag :value="`${(data.probability || 0).toFixed(0)}%`" :severity="getProbSeverity(data.probability)" />
            <span class="prob-small" v-if="data.video_count">{{ data.video_count }}/{{ totalVideos }}</span>
          </div>
        </template>
      </Column>

      <Column field="approved" header="Статус" style="width: 120px">
        <template #body="{ data }">
          <Tag v-if="data.approved" value="Утверждён" severity="success" icon="pi pi-check" />
          <Tag v-else value="Ожидает" severity="warning" icon="pi pi-clock" />
        </template>
      </Column>

      <Column header="Действия" style="width: 130px">
        <template #body="{ data }">
          <div class="actions" @click.stop>
            <Button v-if="!data.approved"
                    icon="pi pi-check" severity="success" text rounded
                    @click="approveOne(data.id)" v-tooltip.top="'Утвердить'" />
            <Button v-else
                    icon="pi pi-undo" severity="warning" text rounded
                    @click="revokeOne(data.id)" v-tooltip.top="'Отозвать'" />
            <Button icon="pi pi-trash" severity="danger" text rounded
                    @click="deleteQuestion(data.id)" v-tooltip.top="'Удалить'" />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Question Detail Dialog -->
    <QuestionDetailDialog v-model:visible="showDetailDialog"
                          :questionId="selectedQuestionId"
                          @changed="onQuestionChanged"
                          @open-question="openQuestionCard" />

    <!-- Bulk actions -->
    <transition name="slide-up">
      <div v-if="selectedQuestions.length > 0" class="bulk-actions">
        <span class="bulk-count">Выбрано: <strong>{{ selectedQuestions.length }}</strong></span>
        <div class="bulk-buttons">
          <Button label="Утвердить" icon="pi pi-check" severity="success" @click="approveBulk" :disabled="selectedUnapproved.length === 0" />
          <Button label="Отозвать" icon="pi pi-undo" severity="warning" @click="revokeBulk" :disabled="selectedApproved.length === 0" />
          <Button label="Удалить" icon="pi pi-trash" severity="danger" @click="deleteBulk" />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useQuestionsStore, useTasksStore } from '../store'
import QuestionDetailDialog from './QuestionDetailDialog.vue'

const questionsStore = useQuestionsStore()
const tasksStore = useTasksStore()

const loading = ref(false)
const selectedQuestions = ref([])
const searchQuery = ref('')
const filterTopic = ref(null)
const filterStatus = ref(null)
const selectAll = ref(false)

// Dialog state
const showDetailDialog = ref(false)
const selectedQuestionId = ref(null)

// Counts
const unapprovedCount = computed(() => questionsStore.unapprovedQuestions.length)
const approvedCount = computed(() => questionsStore.approvedQuestions.length)
const totalVideos = computed(() => questionsStore.totalVideos || 0)

// Selected subsets
const selectedUnapproved = computed(() => selectedQuestions.value.filter(q => !q.approved))
const selectedApproved = computed(() => selectedQuestions.value.filter(q => q.approved))

// Filter options
const statusOptions = [
  { label: 'Все статусы', value: null },
  { label: 'Ожидают утверждения', value: 'unapproved' },
  { label: 'Утверждённые', value: 'approved' }
]

const topicOptions = computed(() => {
  return [
    { label: 'Все технологии', value: null },
    ...questionsStore.topics.map(t => ({ label: t, value: t }))
  ]
})

// Filtered questions — показывает ВСЕ вопросы (не только неутверждённые)
const filteredQuestions = computed(() => {
  let questions = [...questionsStore.adminQuestions]

  if (filterStatus.value === 'approved') {
    questions = questions.filter(q => q.approved)
  } else if (filterStatus.value === 'unapproved') {
    questions = questions.filter(q => !q.approved)
  }

  if (filterTopic.value) {
    questions = questions.filter(q => q.topic === filterTopic.value)
  }

  if (searchQuery.value) {
    const s = searchQuery.value.toLowerCase()
    questions = questions.filter(q =>
      q.question?.toLowerCase().includes(s) ||
      q.topic?.toLowerCase().includes(s)
    )
  }

  return questions
})

// Helpers
const getDifficultySeverity = (d) => ({ junior: 'success', middle: 'warning', senior: 'danger' })[d] || 'info'
const getDifficultyLabel = (d) => ({ junior: 'Junior', middle: 'Middle', senior: 'Senior' })[d] || d || '—'
const getProbSeverity = (p) => {
  if (p >= 60) return 'danger'
  if (p >= 30) return 'warning'
  return 'info'
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

// Row click handler — open detail dialog
const onRowClick = (event) => {
  // Ignore clicks on checkboxes and buttons
  if (event.originalEvent.target.closest('.p-checkbox, .actions, button')) return
  selectedQuestionId.value = event.data.id
  showDetailDialog.value = true
}

const openQuestionCard = (id) => {
  selectedQuestionId.value = id
  showDetailDialog.value = true
}

const onQuestionChanged = async () => {
  await questionsStore.fetchAdminQuestions()
}

// Actions
const refresh = async () => {
  loading.value = true
  await questionsStore.fetchAdminQuestions()
  selectedQuestions.value = []
  selectAll.value = false
  loading.value = false
}

const approveOne = async (id) => {
  loading.value = true
  await questionsStore.approveQuestions([id])
  selectedQuestions.value = selectedQuestions.value.filter(q => q.id !== id)
  loading.value = false
}

const revokeOne = async (id) => {
  loading.value = true
  await questionsStore.revokeQuestions([id])
  selectedQuestions.value = selectedQuestions.value.filter(q => q.id !== id)
  loading.value = false
}

const approveBulk = async () => {
  const ids = selectedUnapproved.value.map(q => q.id)
  if (ids.length === 0) return
  loading.value = true
  await questionsStore.approveQuestions(ids)
  selectedQuestions.value = []
  selectAll.value = false
  loading.value = false
}

const revokeBulk = async () => {
  const ids = selectedApproved.value.map(q => q.id)
  if (ids.length === 0) return
  loading.value = true
  await questionsStore.revokeQuestions(ids)
  selectedQuestions.value = []
  selectAll.value = false
  loading.value = false
}

const deleteQuestion = async (id) => {
  if (!confirm('Удалить этот вопрос?')) return
  loading.value = true
  await questionsStore.deleteQuestion(id)
  selectedQuestions.value = selectedQuestions.value.filter(q => q.id !== id)
  loading.value = false
}

const deleteBulk = async () => {
  if (!confirm(`Удалить ${selectedQuestions.value.length} вопросов?`)) return
  loading.value = true
  for (const q of selectedQuestions.value) {
    await questionsStore.deleteQuestion(q.id)
  }
  selectedQuestions.value = []
  selectAll.value = false
  loading.value = false
}

// Автообновление при завершении задачи
watch(() => tasksStore.completedTasks.length, (newVal, oldVal) => {
  if (newVal > oldVal) {
    setTimeout(() => refresh(), 2000)
  }
})

defineExpose({ refresh })
</script>

<style scoped>
.question-approval {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.approval-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.approval-header h3 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  font-size: 1.15rem;
  color: rgba(255,255,255,0.9);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.count-tag {
  font-weight: 600;
}

.filters {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 250px;
}

.topic-filter, .status-filter {
  min-width: 180px;
}

.question-cell {
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}

.prob-cell {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.prob-small {
  font-size: 0.7rem;
  color: rgba(255,255,255,0.35);
}

.video-title {
  font-size: 0.8rem;
  color: rgba(255,255,255,0.45);
}

.actions {
  display: flex;
  gap: 0.25rem;
}

.w-full {
  width: 100%;
}

/* Bulk actions */
.bulk-actions {
  position: sticky;
  bottom: 1rem;
  background: rgba(30, 30, 60, 0.95);
  backdrop-filter: blur(12px);
  padding: 1rem 1.5rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255,255,255,0.1);
  z-index: 10;
}

.bulk-count {
  font-size: 0.95rem;
  color: rgba(255,255,255,0.7);
}

.bulk-count strong {
  color: rgba(255,255,255,0.95);
}

.bulk-buttons {
  display: flex;
  gap: 0.5rem;
}

/* Slide-up transition */
.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from, .slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

/* Table overrides */
.approval-table :deep(.p-datatable-thead > tr > th) {
  background: rgba(255,255,255,0.04);
  border-color: rgba(255,255,255,0.08);
  font-weight: 700;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.approval-table :deep(.p-datatable-tbody > tr > td) {
  border-color: rgba(255,255,255,0.05);
}

.approval-table :deep(.p-datatable-tbody > tr:hover) {
  background: rgba(255,255,255,0.04) !important;
  cursor: pointer;
}

.approval-table :deep(.p-datatable-tbody > tr.clickable-row) {
  cursor: pointer;
}
</style>
