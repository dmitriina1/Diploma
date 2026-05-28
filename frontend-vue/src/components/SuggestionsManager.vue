<template>
  <div class="suggestions-manager">
    <div class="section-header">
      <h3><i class="pi pi-lightbulb"></i> Предложения видео</h3>
      <Button icon="pi pi-refresh" @click="loadSuggestions" text rounded />
    </div>

    <div v-if="loading" class="loading"><ProgressSpinner strokeWidth="3" /></div>

    <div v-else-if="suggestions.length === 0" class="empty">
      <p>Нет предложений</p>
    </div>

    <DataTable v-else :value="suggestions" :paginator="true" :rows="10" stripedRows
               dataKey="id" class="suggestions-table" responsiveLayout="scroll">
      <Column field="url" header="URL" :style="{ maxWidth: '250px' }">
        <template #body="s">
          <a :href="s.data.url" target="_blank" class="url-link">{{ truncate(s.data.url, 40) }}</a>
          <Tag :value="s.data.platform" size="small" severity="info" class="ml-1" />
        </template>
      </Column>
      <Column field="topic" header="Тема" />
      <Column field="status" header="Статус">
        <template #body="s">
          <Tag :value="statusLabels[s.data.status]" :severity="statusSev[s.data.status]" />
        </template>
      </Column>
      <Column field="user_name" header="От кого">
        <template #body="s">{{ s.data.user_name || '—' }}</template>
      </Column>
      <Column field="comment" header="Комментарий">
        <template #body="s">
          <span class="comment-text">{{ truncate(s.data.comment, 50) }}</span>
        </template>
      </Column>
      <Column field="created_at" header="Дата">
        <template #body="s">{{ formatDate(s.data.created_at) }}</template>
      </Column>
      <Column header="Действия" :style="{ width: '200px' }">
        <template #body="s">
          <div class="action-buttons">
            <Button v-if="s.data.status === 'pending'" icon="pi pi-play" label="Обработать" 
                    size="small" severity="success" @click="processSuggestion(s.data)" :loading="processing === s.data.id" />
            <Button v-if="s.data.status === 'pending'" icon="pi pi-times" 
                    size="small" severity="danger" text @click="rejectSuggestion(s.data)" />
            <Tag v-if="s.data.status === 'processing'" value="Обрабатывается" severity="warning" />
            <Tag v-if="s.data.status === 'completed'" value="Готово" severity="success" />
          </div>
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { useToast } from 'primevue/usetoast'

const toast = useToast()
const loading = ref(false)
const suggestions = ref([])
const processing = ref(null)

const statusLabels = { pending: 'Ожидает', approved: 'Одобрено', rejected: 'Отклонено', processing: 'Обработка', completed: 'Готово' }
const statusSev = { pending: 'info', approved: 'success', rejected: 'danger', processing: 'warning', completed: 'success' }

const loadSuggestions = async () => {
  loading.value = true
  try {
    const r = await api.getAdminSuggestions()
    suggestions.value = r.data.suggestions || []
  } catch (e) { console.error(e) }
  loading.value = false
}

const processSuggestion = async (s) => {
  processing.value = s.id
  try {
    const r = await api.processSuggestion(s.id)
    toast.add({ severity: 'success', summary: 'Запущено', detail: `Task: ${r.data.task_id}`, life: 5000 })
    s.status = 'processing'
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: e.response?.data?.detail || 'Ошибка', life: 5000 })
  }
  processing.value = null
}

const rejectSuggestion = async (s) => {
  try {
    await api.updateSuggestion(s.id, { status: 'rejected', admin_comment: 'Отклонено администратором' })
    s.status = 'rejected'
  } catch (e) { console.error(e) }
}

const truncate = (s, n) => s && s.length > n ? s.slice(0, n) + '...' : (s || '—')
const formatDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : ''

onMounted(loadSuggestions)

defineExpose({ refresh: loadSuggestions })
</script>

<style scoped>
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.section-header h3 { display: flex; align-items: center; gap: 0.5rem; color: rgba(255,255,255,0.85); }
.loading { text-align: center; padding: 2rem; }
.empty { text-align: center; padding: 2rem; color: rgba(255,255,255,0.4); }
.url-link { color: #667eea; text-decoration: none; font-size: 0.85rem; }
.url-link:hover { text-decoration: underline; }
.comment-text { font-size: 0.85rem; color: rgba(255,255,255,0.6); }
.action-buttons { display: flex; gap: 0.4rem; align-items: center; }
</style>
