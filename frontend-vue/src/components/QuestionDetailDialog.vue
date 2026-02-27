<template>
  <Dialog :visible="visible" @update:visible="$emit('update:visible', $event)"
          :modal="true" :closable="true" :draggable="false"
          :style="{ width: '960px', maxHeight: '90vh' }"
          :contentStyle="{ overflow: 'auto' }"
          class="question-detail-dialog">

    <!-- Header -->
    <template #header>
      <div class="dialog-header">
        <div class="header-left">
          <span class="header-title">Карточка вопроса</span>
          <Tag v-if="question?.approved" value="Утверждён" severity="success" icon="pi pi-check" />
          <Tag v-else value="На модерации" severity="warning" icon="pi pi-clock" />
        </div>
        <div class="header-right">
          <Tag v-if="question?.probability > 0"
               :value="`${question.probability.toFixed(1)}%`"
               :severity="probSeverity" icon="pi pi-chart-bar" class="prob-tag" />
          <span v-if="question?.video_count" class="video-badge">
            <i class="pi pi-video"></i> {{ question.video_count }} из {{ totalVideos }} видео
          </span>
        </div>
      </div>
    </template>

    <div v-if="loadingDetail" class="loading-state">
      <ProgressSpinner strokeWidth="3" />
      <span>Загрузка карточки...</span>
    </div>

    <div v-else-if="detail" class="detail-body">
      <!-- Question -->
      <div class="field-group">
        <label><i class="pi pi-question-circle"></i> Вопрос</label>
        <Textarea v-if="editing" v-model="form.question" rows="3" autoResize class="w-full" />
        <div v-else class="field-value question-text">{{ detail.question }}</div>
      </div>

      <!-- Topic + Difficulty row -->
      <div class="fields-row">
        <div class="field-group flex-1">
          <label><i class="pi pi-tag"></i> Технология</label>
          <InputText v-if="editing" v-model="form.topic" class="w-full" />
          <Tag v-else :value="detail.topic || '—'" severity="info" />
        </div>
        <div class="field-group" style="width: 180px">
          <label><i class="pi pi-signal"></i> Сложность</label>
          <Dropdown v-if="editing" v-model="form.difficulty" :options="difficultyOpts"
                    optionLabel="label" optionValue="value" class="w-full" />
          <Tag v-else :value="diffLabel(detail.difficulty)" :severity="diffSeverity(detail.difficulty)" />
        </div>
        <div class="field-group" style="width: 120px">
          <label><i class="pi pi-clock"></i> Таймкод</label>
          <InputText v-if="editing" v-model="form.timecode" class="w-full" placeholder="10:30" />
          <span v-else class="field-value">{{ detail.timecode || '—' }}</span>
        </div>
      </div>

      <!-- Probability bar -->
      <div class="field-group prob-section">
        <label>
          <i class="pi pi-chart-line"></i> Вероятность на собеседовании
          <span class="prob-explain">(встречался в {{ detail.video_count }} из {{ detail.total_videos }} видео)</span>
        </label>
        <div class="prob-bar-wrapper">
          <ProgressBar :value="detail.probability" :showValue="true"
                       :class="'prob-bar-' + probLevel" />
        </div>
      </div>

      <Divider />

      <!-- Answer -->
      <div class="field-group">
        <label>
          <i class="pi pi-book"></i> Ответ
          <Button v-if="!editing" :label="detail.answer ? 'Перегенерировать' : 'Сгенерировать'"
                  icon="pi pi-sparkles" text size="small" class="gen-btn"
                  @click="generateAnswer" :loading="generating" />
        </label>
        <div v-if="editing" class="answer-edit-wrapper">
          <div class="answer-edit-toolbar">
            <Button label="Сгенерировать ответ" icon="pi pi-sparkles" size="small" severity="help"
                    @click="generateAnswerInEdit" :loading="generating" 
                    v-tooltip="'Сгенерировать ответ с помощью LLM и вставить в поле'" />
          </div>
          <Textarea v-model="form.answer" rows="8" autoResize class="w-full answer-edit" 
                    placeholder="Напишите ответ вручную или сгенерируйте с помощью кнопки выше..." />
        </div>
        <div v-else-if="detail.answer" class="field-value answer-text">{{ detail.answer }}</div>
        <div v-else class="no-answer">
          <i class="pi pi-info-circle"></i> Ответ пока не сгенерирован
        </div>
      </div>

      <Divider />

      <!-- Videos list -->
      <div v-if="detail.videos?.length" class="field-group">
        <label><i class="pi pi-video"></i> Видео, в которых встречается ({{ detail.videos.length }})</label>
        <div class="videos-list">
          <div v-for="v in detail.videos" :key="v.id" class="video-item">
            <Tag :value="v.platform || 'youtube'" size="small" severity="secondary" />
            <a :href="v.url" target="_blank" rel="noopener" class="video-link">{{ v.title || v.url }}</a>
          </div>
        </div>
      </div>

      <Divider />

      <!-- Similar questions -->
      <div v-if="detail.similar_questions?.length" class="field-group">
        <label><i class="pi pi-sitemap"></i> Похожие вопросы</label>
        <div class="similar-list">
          <div v-for="s in detail.similar_questions" :key="s.id" class="similar-item">
            <div class="similar-main">
              <span class="similar-text">{{ s.question }}</span>
              <div class="similar-meta">
                <Tag :value="s.topic" severity="info" size="small" />
                <span class="sim-score">{{ (s.similarity_score * 100).toFixed(0) }}% схожести</span>
                <span v-if="s.probability > 0" class="sim-prob">{{ s.probability.toFixed(1) }}% вероятность</span>
              </div>
            </div>
            <div class="similar-actions">
              <Button label="Объединить" icon="pi pi-arrows-h" severity="warning" text size="small"
                      @click="confirmMerge(s)" />
              <Button icon="pi pi-external-link" text size="small" v-tooltip="'Открыть'"
                      @click="openSimilar(s.id)" />
            </div>
          </div>
        </div>
      </div>

      <!-- Metadata -->
      <div v-if="detail.source_url || detail.created_at" class="meta-row">
        <span v-if="detail.created_at" class="meta-item">
          <i class="pi pi-calendar"></i> {{ formatDate(detail.created_at) }}
        </span>
        <a v-if="detail.source_url" :href="detail.source_url" target="_blank" class="meta-item link">
          <i class="pi pi-external-link"></i> Источник
        </a>
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="dialog-footer">
        <div class="footer-left">
          <Button v-if="!editing && detail"
                  :label="detail?.approved ? 'Отозвать' : 'Утвердить'"
                  :icon="detail?.approved ? 'pi pi-undo' : 'pi pi-check'"
                  :severity="detail?.approved ? 'warning' : 'success'"
                  @click="toggleApproval" :loading="saving" />
          <Button v-if="!editing && detail" label="Удалить" icon="pi pi-trash" severity="danger" text
                  @click="confirmDelete" />
        </div>
        <div class="footer-right">
          <template v-if="editing">
            <Button label="Отмена" icon="pi pi-times" text @click="cancelEdit" />
            <Button label="Сохранить" icon="pi pi-save" @click="saveEdit" :loading="saving" />
          </template>
          <template v-else>
            <Button label="Редактировать" icon="pi pi-pencil" @click="startEdit" />
          </template>
        </div>
      </div>
    </template>

    <!-- Merge confirmation dialog -->
    <Dialog v-model:visible="showMergeConfirm" header="Объединить вопросы?" :modal="true"
            :style="{ width: '550px' }" class="merge-dialog">
      <div class="merge-body">
        <div class="merge-block">
          <span class="merge-label">Текущий вопрос (будет удалён):</span>
          <p class="merge-text source">{{ detail?.question }}</p>
        </div>
        <div class="merge-arrow">
          <i class="pi pi-arrow-down" style="font-size: 1.5rem; color: #f59e0b;"></i>
        </div>
        <div class="merge-block">
          <span class="merge-label">Объединить с (останется):</span>
          <p class="merge-text target">{{ mergeTarget?.question }}</p>
          <small class="merge-hint">Все видео-связи текущего вопроса будут перенесены, вероятность пересчитана</small>
        </div>
      </div>
      <template #footer>
        <Button label="Отмена" text @click="showMergeConfirm = false" />
        <Button label="Объединить" icon="pi pi-arrows-h" severity="warning" @click="executeMerge" :loading="merging" />
      </template>
    </Dialog>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useQuestionsStore } from '../store'
import api from '../api/client'

const props = defineProps({
  visible: Boolean,
  questionId: Number
})

const emit = defineEmits(['update:visible', 'changed', 'open-question'])

const questionsStore = useQuestionsStore()

const loadingDetail = ref(false)
const detail = ref(null)
const editing = ref(false)
const saving = ref(false)
const generating = ref(false)
const form = ref({})
const showMergeConfirm = ref(false)
const mergeTarget = ref(null)
const merging = ref(false)

const question = computed(() => detail.value)
const totalVideos = computed(() => detail.value?.total_videos || questionsStore.totalVideos || 0)

const difficultyOpts = [
  { label: 'Junior', value: 'junior' },
  { label: 'Middle', value: 'middle' },
  { label: 'Senior', value: 'senior' }
]

const probSeverity = computed(() => {
  const p = question.value?.probability || 0
  if (p >= 60) return 'danger'
  if (p >= 30) return 'warning'
  return 'info'
})

const probLevel = computed(() => {
  const p = question.value?.probability || 0
  if (p >= 60) return 'high'
  if (p >= 30) return 'mid'
  return 'low'
})

const diffLabel = (d) => ({ junior: 'Junior', middle: 'Middle', senior: 'Senior' })[d] || d || '—'
const diffSeverity = (d) => ({ junior: 'success', middle: 'warning', senior: 'danger' })[d] || 'info'

const formatDate = (s) => {
  if (!s) return '—'
  return new Date(s).toLocaleDateString('ru-RU', { year: 'numeric', month: 'long', day: 'numeric' })
}

// Load question detail when dialog opens or questionId changes
watch(() => [props.visible, props.questionId], async ([vis, id]) => {
  if (vis && id) {
    loadingDetail.value = true
    editing.value = false
    detail.value = null
    try {
      const res = await api.getQuestionDetail(id)
      detail.value = res.data
    } catch (e) {
      console.error('Failed to load question detail:', e)
    } finally {
      loadingDetail.value = false
    }
  }
}, { immediate: true })

// Edit mode
const startEdit = () => {
  form.value = {
    question: detail.value.question,
    answer: detail.value.answer || '',
    topic: detail.value.topic || '',
    difficulty: detail.value.difficulty || 'middle',
    timecode: detail.value.timecode || '',
    approved: detail.value.approved
  }
  editing.value = true
}

const cancelEdit = () => { editing.value = false }

const saveEdit = async () => {
  saving.value = true
  try {
    await questionsStore.updateQuestion(detail.value.id, form.value)
    // Reload detail
    const res = await api.getQuestionDetail(detail.value.id)
    detail.value = res.data
    editing.value = false
    emit('changed')
  } catch (e) {
    alert('Ошибка сохранения: ' + e.message)
  } finally {
    saving.value = false
  }
}

// Approve / Revoke
const toggleApproval = async () => {
  saving.value = true
  try {
    if (detail.value.approved) {
      await questionsStore.revokeQuestions([detail.value.id])
    } else {
      await questionsStore.approveQuestions([detail.value.id])
    }
    const res = await api.getQuestionDetail(detail.value.id)
    detail.value = res.data
    emit('changed')
  } finally {
    saving.value = false
  }
}

// Delete
const confirmDelete = async () => {
  if (!confirm('Удалить этот вопрос безвозвратно?')) return
  saving.value = true
  try {
    await questionsStore.deleteQuestion(detail.value.id)
    emit('changed')
    emit('update:visible', false)
  } finally {
    saving.value = false
  }
}

// Generate answer
const generateAnswer = async () => {
  generating.value = true
  try {
    await questionsStore.generateAnswer(detail.value.id)
    const res = await api.getQuestionDetail(detail.value.id)
    detail.value = res.data
    emit('changed')
  } catch (e) {
    alert('Ошибка генерации ответа: ' + e.message)
  } finally {
    generating.value = false
  }
}

// Generate answer while in edit mode — inserts generated text into the form
const generateAnswerInEdit = async () => {
  generating.value = true
  try {
    await questionsStore.generateAnswer(detail.value.id)
    const res = await api.getQuestionDetail(detail.value.id)
    form.value.answer = res.data.answer || form.value.answer
    detail.value = res.data
  } catch (e) {
    alert('Ошибка генерации ответа: ' + e.message)
  } finally {
    generating.value = false
  }
}

// Merge
const confirmMerge = (similar) => {
  mergeTarget.value = similar
  showMergeConfirm.value = true
}

const executeMerge = async () => {
  merging.value = true
  try {
    const result = await questionsStore.mergeQuestions(detail.value.id, mergeTarget.value.id)
    showMergeConfirm.value = false
    emit('changed')
    // Open the target question card
    emit('update:visible', false)
    setTimeout(() => emit('open-question', mergeTarget.value.id), 300)
  } catch (e) {
    alert('Ошибка объединения: ' + e.message)
  } finally {
    merging.value = false
  }
}

const openSimilar = (id) => {
  emit('update:visible', false)
  setTimeout(() => emit('open-question', id), 300)
}
</script>

<style scoped>
.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  gap: 1rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.header-title {
  font-weight: 700;
  font-size: 1.1rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.prob-tag {
  font-weight: 700;
  font-size: 1rem;
}

.video-badge {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: rgba(255,255,255,0.5);
}

/* body */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field-group {
  margin-bottom: 0.5rem;
}

.field-group > label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 600;
  font-size: 0.85rem;
  color: rgba(255,255,255,0.6);
  margin-bottom: 0.4rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.field-value {
  color: rgba(255,255,255,0.85);
}

.question-text {
  font-size: 1.15rem;
  font-weight: 600;
  line-height: 1.5;
}

.fields-row {
  display: flex;
  gap: 1rem;
}

.flex-1 { flex: 1; }
.w-full { width: 100%; }

/* Probability */
.prob-section {
  margin-top: 0.25rem;
}

.prob-explain {
  font-weight: 400;
  font-size: 0.8rem;
  color: rgba(255,255,255,0.35);
  text-transform: none;
}

.prob-bar-wrapper {
  max-width: 400px;
}

:deep(.prob-bar-high .p-progressbar-value) {
  background: linear-gradient(90deg, #ef4444, #dc2626) !important;
}

:deep(.prob-bar-mid .p-progressbar-value) {
  background: linear-gradient(90deg, #f59e0b, #d97706) !important;
}

:deep(.prob-bar-low .p-progressbar-value) {
  background: linear-gradient(90deg, #22c55e, #16a34a) !important;
}

/* Answer */
.gen-btn {
  margin-left: 0.5rem;
}

.answer-text {
  background: rgba(255,255,255,0.04);
  padding: 1rem 1.25rem;
  border-radius: 8px;
  line-height: 1.8;
  white-space: pre-wrap;
  color: rgba(255,255,255,0.8);
  font-size: 0.95rem;
  border: 1px solid rgba(255,255,255,0.06);
}

.answer-edit {
  font-size: 0.95rem;
  line-height: 1.7;
}

.answer-edit-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.answer-edit-toolbar {
  display: flex;
  gap: 0.5rem;
}

.no-answer {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: rgba(255,255,255,0.35);
  padding: 0.75rem 0;
}

/* Videos */
.videos-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  max-height: 150px;
  overflow-y: auto;
}

.video-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0;
}

.video-link {
  color: rgba(255,255,255,0.6);
  text-decoration: none;
  font-size: 0.85rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-link:hover {
  color: #667eea;
  text-decoration: underline;
}

/* Similar */
.similar-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.similar-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0.75rem 1rem;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  gap: 1rem;
}

.similar-main {
  flex: 1;
  min-width: 0;
}

.similar-text {
  display: block;
  font-size: 0.9rem;
  color: rgba(255,255,255,0.8);
  margin-bottom: 0.4rem;
}

.similar-meta {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.sim-score {
  font-size: 0.75rem;
  color: rgba(255,255,255,0.4);
}

.sim-prob {
  font-size: 0.75rem;
  color: #f59e0b;
  font-weight: 600;
}

.similar-actions {
  display: flex;
  gap: 0.25rem;
  flex-shrink: 0;
}

/* Meta */
.meta-row {
  display: flex;
  gap: 1.5rem;
  padding-top: 0.5rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.8rem;
  color: rgba(255,255,255,0.35);
}

.meta-item.link {
  color: rgba(255,255,255,0.5);
  text-decoration: none;
}

.meta-item.link:hover {
  color: #667eea;
}

/* Footer */
.dialog-footer {
  display: flex;
  justify-content: space-between;
  width: 100%;
}

.footer-left, .footer-right {
  display: flex;
  gap: 0.5rem;
}

/* Merge dialog */
.merge-body {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.merge-block {
  padding: 0.75rem;
  background: rgba(255,255,255,0.03);
  border-radius: 8px;
}

.merge-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(255,255,255,0.5);
  text-transform: uppercase;
}

.merge-text {
  margin: 0.4rem 0 0;
  font-size: 0.95rem;
  line-height: 1.4;
}

.merge-text.source {
  color: rgba(255,255,255,0.5);
  text-decoration: line-through;
}

.merge-text.target {
  color: rgba(255,255,255,0.9);
  font-weight: 600;
}

.merge-hint {
  color: rgba(255,255,255,0.35);
  font-size: 0.8rem;
}

.merge-arrow {
  text-align: center;
}
</style>
