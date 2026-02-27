<template>
  <div class="bookmarks-page">
    <NavBar />
    
    <div class="page-container">
      <header class="page-header">
        <h1><i class="pi pi-bookmark"></i> Мои закладки</h1>
        <p class="subtitle">Сохранённые вопросы для повторения</p>
      </header>

      <div v-if="loading" class="loading-state">
        <ProgressSpinner strokeWidth="3" />
        <p>Загрузка...</p>
      </div>

      <div v-else-if="bookmarks.length === 0" class="empty-state">
        <i class="pi pi-bookmark" style="font-size: 3rem; color: rgba(255,255,255,0.2)"></i>
        <h3>Нет закладок</h3>
        <p>Добавляйте вопросы в закладки при просмотре, чтобы вернуться к ним позже</p>
        <Button label="Перейти к вопросам" icon="pi pi-arrow-right" @click="$router.push('/')" />
      </div>

      <div v-else class="bookmarks-list">
        <div class="bookmark-controls">
          <span class="count">{{ bookmarks.length }} вопросов в закладках</span>
          <InputText v-model="searchQuery" placeholder="Поиск..." class="search-input" />
        </div>

        <div v-for="b in filteredBookmarks" :key="b.id" class="bookmark-card" @click="$router.push(`/question/${b.question_id}`)">
          <div class="bookmark-header">
            <Tag :value="b.topic || 'General'" severity="info" />
            <Tag :value="b.difficulty || 'middle'" :severity="diffSev(b.difficulty)" />
            <span v-if="b.probability > 0" class="probability">{{ b.probability.toFixed(1) }}%</span>
          </div>
          <h3 class="bookmark-question">{{ b.question }}</h3>
          <p v-if="b.answer" class="bookmark-answer">{{ truncate(b.answer, 150) }}</p>
          <div class="bookmark-footer">
            <span class="bookmark-date"><i class="pi pi-calendar"></i> {{ formatDate(b.created_at) }}</span>
            <Button icon="pi pi-trash" severity="danger" text rounded @click.stop="removeBookmark(b.question_id)" />
          </div>
        </div>
      </div>

      <!-- Notes Section -->
      <section v-if="notes.length > 0" class="notes-section">
        <h2><i class="pi pi-pencil"></i> Мои заметки</h2>
        <div v-for="n in notes" :key="n.id" class="note-card">
          <div class="note-header">
            <span class="note-topic">{{ n.topic }}</span>
            <span class="note-date">{{ formatDate(n.updated_at) }}</span>
          </div>
          <p class="note-question">{{ n.question }}</p>
          <p class="note-text">{{ n.note }}</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import NavBar from '../components/NavBar.vue'
import api from '../api/client'

const loading = ref(true)
const bookmarks = ref([])
const notes = ref([])
const searchQuery = ref('')

// Ensure user session is initialized
api.getUserSession()

const filteredBookmarks = computed(() => {
  if (!searchQuery.value) return bookmarks.value
  const q = searchQuery.value.toLowerCase()
  return bookmarks.value.filter(b => 
    b.question?.toLowerCase().includes(q) || b.topic?.toLowerCase().includes(q) || b.answer?.toLowerCase().includes(q)
  )
})

const loadBookmarks = async () => {
  loading.value = true
  try {
    const r = await api.getBookmarks()
    bookmarks.value = r.data.bookmarks || []
  } catch (e) { console.error(e) }
  
  try {
    const r = await api.getAllNotes()
    notes.value = r.data.notes || []
  } catch (e) { console.error(e) }
  
  loading.value = false
}

const removeBookmark = async (questionId) => {
  try {
    await api.removeBookmark(questionId)
    bookmarks.value = bookmarks.value.filter(b => b.question_id !== questionId)
  } catch (e) { console.error(e) }
}

const truncate = (s, n) => s && s.length > n ? s.slice(0, n) + '...' : s
const formatDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : ''
const diffSev = (d) => ({ junior: 'success', middle: 'warning', senior: 'danger' }[d] || 'info')

onMounted(loadBookmarks)
</script>

<style scoped>
.bookmarks-page { min-height: 100vh; background: linear-gradient(180deg, #0f0f1e 0%, #1a1a2e 50%, #16213e 100%); }
.page-container { max-width: 900px; margin: 0 auto; padding: 1.5rem 2rem 3rem; }
.page-header { margin-bottom: 2rem; }
.page-header h1 {
  display: flex; align-items: center; gap: 0.75rem; font-size: 1.8rem; font-weight: 800;
  background: linear-gradient(135deg, #f59e0b, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.subtitle { color: rgba(255,255,255,0.5); margin-top: 0.3rem; }
.loading-state, .empty-state {
  text-align: center; padding: 3rem; color: rgba(255,255,255,0.5);
}
.empty-state h3 { margin: 1rem 0 0.5rem; color: rgba(255,255,255,0.7); }
.bookmark-controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.count { color: rgba(255,255,255,0.5); font-size: 0.9rem; }
.search-input { max-width: 250px; }
.bookmarks-list { display: flex; flex-direction: column; gap: 0.75rem; }
.bookmark-card {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px; padding: 1rem 1.25rem; cursor: pointer; transition: all 0.2s;
}
.bookmark-card:hover { border-color: rgba(102,126,234,0.4); transform: translateY(-1px); }
.bookmark-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.6rem; }
.probability { color: #f59e0b; font-weight: 700; font-size: 0.85rem; margin-left: auto; }
.bookmark-question { font-size: 1.05rem; font-weight: 600; color: #e4e4e7; margin-bottom: 0.4rem; line-height: 1.4; }
.bookmark-answer { font-size: 0.85rem; color: rgba(255,255,255,0.5); line-height: 1.4; }
.bookmark-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem; }
.bookmark-date { font-size: 0.8rem; color: rgba(255,255,255,0.35); display: flex; align-items: center; gap: 0.3rem; }
.notes-section { margin-top: 2.5rem; }
.notes-section h2 { display: flex; align-items: center; gap: 0.5rem; font-size: 1.3rem; margin-bottom: 1rem; color: rgba(255,255,255,0.85); }
.note-card {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 0.5rem;
}
.note-header { display: flex; justify-content: space-between; font-size: 0.8rem; color: rgba(255,255,255,0.4); margin-bottom: 0.3rem; }
.note-question { font-weight: 600; color: rgba(255,255,255,0.7); font-size: 0.9rem; margin-bottom: 0.3rem; }
.note-text { font-size: 0.85rem; color: rgba(255,255,255,0.55); white-space: pre-wrap; }
</style>
