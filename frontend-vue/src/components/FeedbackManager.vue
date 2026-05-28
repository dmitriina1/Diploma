<template>
  <div class="feedback-manager">
    <div class="section-header">
      <h3><i class="pi pi-comments"></i> Обратная связь</h3>
      <div class="header-actions">
        <Dropdown v-model="statusFilter" :options="statusOptions" optionLabel="label" optionValue="value"
                  placeholder="Все статусы" showClear class="w-12rem" @change="loadFeedback" />
        <Button icon="pi pi-refresh" @click="loadFeedback" text rounded />
      </div>
    </div>

    <div v-if="loading" class="loading"><ProgressSpinner strokeWidth="3" /></div>
    <div v-else-if="items.length === 0" class="empty"><p>Нет отзывов</p></div>

    <DataTable v-else :value="items" :paginator="true" :rows="10" stripedRows
               dataKey="id" responsiveLayout="scroll">
      <Column field="feedback_type" header="Тип">
        <template #body="s">
          <Tag :value="typeLabels[s.data.feedback_type]" :severity="typeSev[s.data.feedback_type]" />
        </template>
      </Column>
      <Column field="question_id" header="Вопрос" :style="{ width: '80px' }">
        <template #body="s">
          <span v-if="s.data.question_id">#{{ s.data.question_id }}</span>
          <span v-else>—</span>
        </template>
      </Column>
      <Column field="rating" header="Оценка">
        <template #body="s">
          <Rating v-if="s.data.rating" :modelValue="s.data.rating" :readonly="true" :cancel="false" :stars="5" />
          <span v-else>—</span>
        </template>
      </Column>
      <Column field="comment" header="Комментарий">
        <template #body="s">
          <span class="comment-text">{{ truncate(s.data.comment, 80) }}</span>
        </template>
      </Column>
      <Column field="user_name" header="Пользователь">
        <template #body="s">{{ s.data.user_name || 'Аноним' }}</template>
      </Column>
      <Column field="is_resolved" header="Статус">
        <template #body="s">
          <Tag :value="s.data.is_resolved ? 'Решено' : 'Новое'" 
               :severity="s.data.is_resolved ? 'success' : 'info'" />
        </template>
      </Column>
      <Column field="created_at" header="Дата">
        <template #body="s">{{ formatDate(s.data.created_at) }}</template>
      </Column>
      <Column header="Действия" :style="{ width: '150px' }">
        <template #body="s">
          <div class="action-buttons">
            <Button v-if="!s.data.is_resolved" icon="pi pi-check" label="Решено" 
                    size="small" severity="success" @click="resolve(s.data)" />
            <Button icon="pi pi-eye" size="small" text rounded @click="showDetail(s.data)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="detailVisible" header="Детали отзыва" :modal="true" :style="{ width: '500px' }">
      <div v-if="selected" class="detail-content">
        <div class="detail-row"><span class="label">Тип:</span> <Tag :value="typeLabels[selected.feedback_type]" :severity="typeSev[selected.feedback_type]" /></div>
        <div class="detail-row" v-if="selected.question_id"><span class="label">Вопрос:</span> #{{ selected.question_id }}</div>
        <div class="detail-row" v-if="selected.rating"><span class="label">Оценка:</span> <Rating :modelValue="selected.rating" :readonly="true" :cancel="false" :stars="5" /></div>
        <div class="detail-row"><span class="label">Комментарий:</span></div>
        <p class="detail-comment">{{ selected.comment || '—' }}</p>
        <div class="detail-row"><span class="label">Пользователь:</span> {{ selected.user_name || 'Аноним' }} ({{ selected.user_email || '—' }})</div>
        <div class="detail-row"><span class="label">Дата:</span> {{ formatDate(selected.created_at) }}</div>
        <div class="detail-row" v-if="selected.admin_response"><span class="label">Ответ админа:</span> {{ selected.admin_response }}</div>

        <Divider />
        <div class="admin-response-form">
          <label>Ответ администратора:</label>
          <Textarea v-model="adminResponse" rows="3" class="w-full" />
          <Button label="Сохранить ответ" icon="pi pi-send" class="mt-2" @click="saveResponse" :loading="saving" />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { useToast } from 'primevue/usetoast'

const toast = useToast()
const loading = ref(false)
const items = ref([])
const statusFilter = ref(null)
const detailVisible = ref(false)
const selected = ref(null)
const adminResponse = ref('')
const saving = ref(false)

const statusOptions = [
  { label: 'Новые', value: 'false' },
  { label: 'Решённые', value: 'true' }
]
const typeLabels = { like: 'Лайк', dislike: 'Дизлайк', suggestion: 'Предложение', report: 'Жалоба', answer_quality: 'Качество ответа' }
const typeSev = { like: 'success', dislike: 'danger', suggestion: 'info', report: 'warning', answer_quality: 'secondary' }

const loadFeedback = async () => {
  loading.value = true
  try {
    const params = {}
    if (statusFilter.value !== null) params.is_resolved = statusFilter.value
    const r = await api.getAdminFeedback(params)
    items.value = r.data.feedbacks || []
  } catch (e) { console.error(e) }
  loading.value = false
}

const resolve = async (item) => {
  try {
    await api.updateFeedback(item.id, { is_resolved: true })
    item.is_resolved = true
    toast.add({ severity: 'success', summary: 'Решено', life: 3000 })
  } catch (e) { console.error(e) }
}

const showDetail = (item) => {
  selected.value = item
  adminResponse.value = item.admin_response || ''
  detailVisible.value = true
}

const saveResponse = async () => {
  if (!selected.value) return
  saving.value = true
  try {
    await api.updateFeedback(selected.value.id, { is_resolved: true, admin_response: adminResponse.value })
    selected.value.is_resolved = true
    selected.value.admin_response = adminResponse.value
    toast.add({ severity: 'success', summary: 'Ответ сохранён', life: 3000 })
    detailVisible.value = false
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: e.response?.data?.detail || 'Ошибка', life: 5000 })
  }
  saving.value = false
}

const truncate = (s, n) => s && s.length > n ? s.slice(0, n) + '...' : (s || '—')
const formatDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : ''

onMounted(loadFeedback)

defineExpose({ refresh: loadFeedback })
</script>

<style scoped>
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.section-header h3 { display: flex; align-items: center; gap: 0.5rem; color: rgba(255,255,255,0.85); }
.header-actions { display: flex; align-items: center; gap: 0.5rem; }
.loading { text-align: center; padding: 2rem; }
.empty { text-align: center; padding: 2rem; color: rgba(255,255,255,0.4); }
.comment-text { font-size: 0.85rem; color: rgba(255,255,255,0.6); }
.action-buttons { display: flex; gap: 0.4rem; align-items: center; }
.detail-content { display: flex; flex-direction: column; gap: 0.5rem; }
.detail-row { display: flex; align-items: center; gap: 0.5rem; }
.detail-row .label { font-weight: 600; color: rgba(255,255,255,0.7); min-width: 110px; }
.detail-comment { background: rgba(255,255,255,0.05); border-radius: 8px; padding: 0.8rem; white-space: pre-wrap; }
.admin-response-form label { font-weight: 600; color: rgba(255,255,255,0.7); margin-bottom: 0.3rem; }
</style>
