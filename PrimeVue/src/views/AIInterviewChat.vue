<template>
  <div class="page">
    <NavBar />
    <div class="container" style="padding-top:2rem; padding-bottom:3rem;">

      <!-- Setup Mode -->
      <div v-if="mode === 'setup'" class="setup container-sm">
        <h1 class="page-heading">AI Interview Chat</h1>
        <p class="page-desc">Симуляция технического собеседования с AI-интервьюером</p>

        <div class="form-stack">
          <div class="field">
            <label>Технология</label>
            <select v-model="selectedTopic" class="input">
              <option v-for="t in topics" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div class="field">
            <label>Сложность</label>
            <select v-model="selectedDifficulty" class="input">
              <option value="junior">Junior</option>
              <option value="middle">Middle</option>
              <option value="senior">Senior</option>
            </select>
          </div>
          <button class="btn btn-primary btn-lg" @click="startChat" :disabled="starting" style="width:100%">
            {{ starting ? 'Запуск...' : 'Начать интервью' }}
          </button>
        </div>

        <!-- History -->
        <div v-if="history.length > 0" class="history-section">
          <h3>История интервью</h3>
          <div class="history-list">
            <div v-for="h in history" :key="h.id" class="history-item card card-hover" @click="viewSummary(h)">
              <div class="hi-header">
                <span class="badge badge-info">{{ h.topic }}</span>
                <span class="badge" :class="diffBadge(h.difficulty)">{{ h.difficulty }}</span>
                <span class="badge" :class="statusBadge(h.status)">{{ h.status }}</span>
              </div>
              <div class="hi-date">{{ formatDate(h.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Chat Mode -->
      <div v-if="mode === 'chat'" class="chat-mode">
        <div class="chat-header">
          <button class="btn btn-ghost btn-icon" @click="confirmEnd">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          </button>
          <div class="chat-info">
            <span class="badge badge-info">{{ selectedTopic }}</span>
            <span class="badge" :class="diffBadge(selectedDifficulty)">{{ selectedDifficulty }}</span>
          </div>
          <button class="btn btn-secondary btn-sm" @click="confirmEnd">Завершить</button>
        </div>

        <div class="chat-messages" ref="messagesContainer">
          <div v-for="(msg, i) in messages" :key="i" class="chat-message" :class="msg.role">
            <div class="msg-avatar">{{ msg.role === 'assistant' ? '🤖' : '👤' }}</div>
            <div class="msg-content">
              <div class="msg-text">{{ msg.content }}</div>
              <div class="msg-time">{{ formatTime(msg.timestamp) }}</div>
            </div>
          </div>
          <div v-if="isTyping" class="chat-message assistant typing">
            <div class="msg-avatar">🤖</div>
            <div class="msg-content">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <div class="chat-input-area">
          <textarea 
            v-model="userInput" 
            class="chat-input" 
            placeholder="Введите ваш ответ..."
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.enter.shift.exact="userInput += '\n'"
            :disabled="isTyping"
          ></textarea>
          <button class="btn btn-primary" @click="sendMessage" :disabled="!userInput.trim() || isTyping">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Summary Mode -->
      <div v-if="mode === 'summary'" class="summary-mode container-sm">
        <div class="summary-card card">
          <div class="summary-emoji">🎉</div>
          <h2>Интервью завершено!</h2>
          <div class="summary-content" v-html="formatSummary(currentSummary)"></div>
          <div class="summary-actions">
            <button class="btn btn-primary" @click="mode = 'setup'">Новое интервью</button>
            <button class="btn btn-ghost" @click="mode = 'setup'">На главную</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import NavBar from '../components/NavBar.vue'
import api from '../api/client'

const mode = ref('setup') // 'setup', 'chat', 'summary'
const selectedTopic = ref('Python')
const selectedDifficulty = ref('middle')
const starting = ref(false)
const isTyping = ref(false)
const userInput = ref('')
const messages = ref([])
const currentInterviewId = ref(null)
const currentSummary = ref('')
const history = ref([])
const messagesContainer = ref(null)

const topics = ['Python', 'JavaScript', 'Java', 'Go', 'React', 'Vue', 'Node.js', 'Django', 'Spring', 'PostgreSQL', 'Docker', 'Kubernetes', 'AWS', 'System Design']

const diffBadge = (d) => ({ junior: 'badge-ok', middle: 'badge-warn', senior: 'badge-err' }[d] || 'badge-muted')
const statusBadge = (s) => ({ active: 'badge-warn', completed: 'badge-ok', abandoned: 'badge-muted' }[s] || 'badge-muted')

const formatDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''
const formatTime = (d) => d ? new Date(d).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) : ''

const formatSummary = (text) => {
  if (!text) return ''
  return text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}

const startChat = async () => {
  starting.value = true
  try {
    const r = await api.startInterviewChat(selectedTopic.value, selectedDifficulty.value)
    currentInterviewId.value = r.data.interview_id
    messages.value = [
      { role: 'assistant', content: r.data.message, timestamp: new Date() }
    ]
    mode.value = 'chat'
    await nextTick()
    scrollToBottom()
  } catch (e) {
    console.error(e)
    alert('Не удалось начать интервью: ' + (e.response?.data?.detail || e.message))
  }
  starting.value = false
}

const sendMessage = async () => {
  if (!userInput.value.trim() || isTyping.value) return
  
  const msg = userInput.value.trim()
  messages.value.push({ role: 'user', content: msg, timestamp: new Date() })
  userInput.value = ''
  
  await nextTick()
  scrollToBottom()
  
  isTyping.value = true
  try {
    const r = await api.sendChatMessage(currentInterviewId.value, msg)
    messages.value.push({ role: 'assistant', content: r.data.message, timestamp: new Date() })
    await nextTick()
    scrollToBottom()
  } catch (e) {
    console.error(e)
    alert('Ошибка отправки сообщения: ' + (e.response?.data?.detail || e.message))
  }
  isTyping.value = false
}

const confirmEnd = () => {
  if (confirm('Вы уверены, что хотите завершить интервью?')) {
    endChat()
  }
}

const endChat = async () => {
  try {
    const r = await api.endInterviewChat(currentInterviewId.value)
    currentSummary.value = r.data.summary
    mode.value = 'summary'
    loadHistory()
  } catch (e) {
    console.error(e)
    alert('Ошибка завершения интервью: ' + (e.response?.data?.detail || e.message))
  }
}

const loadHistory = async () => {
  try {
    const r = await api.getInterviewHistory(10)
    history.value = r.data.history || []
  } catch (e) {
    console.error(e)
  }
}

const viewSummary = (h) => {
  if (h.summary) {
    currentSummary.value = h.summary
    mode.value = 'summary'
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.page-heading { font-size: 1.85rem; font-weight: 700; text-align: center; margin-bottom: .3rem; }
.page-desc { text-align: center; color: var(--c-text-3); font-size: 1rem; margin-bottom: 1.75rem; }

/* Setup */
.form-stack { display: flex; flex-direction: column; gap: 1.1rem; margin-top: 1.25rem; }
.field { display: flex; flex-direction: column; gap: .35rem; }
.field label { font-size: .85rem; color: var(--c-text-2); font-weight: 500; }

/* History */
.history-section { margin-top: 2.5rem; }
.history-section h3 { font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; }
.history-list { display: flex; flex-direction: column; gap: .5rem; }
.history-item { padding: 1rem; cursor: pointer; }
.hi-header { display: flex; gap: .4rem; margin-bottom: .5rem; flex-wrap: wrap; }
.hi-date { font-size: .85rem; color: var(--c-text-4); }

/* Chat */
.chat-mode { display: flex; flex-direction: column; height: calc(100vh - 200px); max-width: 900px; margin: 0 auto; }
.chat-header { display: flex; align-items: center; gap: 1rem; padding: 1rem; border-bottom: 1px solid var(--c-border); background: var(--c-surface); border-radius: var(--r-lg) var(--r-lg) 0 0; }
.chat-info { flex: 1; display: flex; gap: .5rem; }

.chat-messages { flex: 1; overflow-y: auto; padding: 1.5rem; background: var(--c-bg); display: flex; flex-direction: column; gap: 1rem; }
.chat-message { display: flex; gap: 1rem; align-items: flex-start; }
.chat-message.user { flex-direction: row-reverse; }
.msg-avatar { width: 40px; height: 40px; border-radius: 50%; background: var(--c-surface); display: flex; align-items: center; justify-content: center; font-size: 1.3rem; flex-shrink: 0; }
.msg-content { flex: 1; max-width: 70%; }
.chat-message.user .msg-content { text-align: right; }
.msg-text { background: var(--c-surface); padding: 1rem 1.25rem; border-radius: var(--r-lg); line-height: 1.6; white-space: pre-wrap; }
.chat-message.user .msg-text { background: var(--c-brand); color: white; }
.msg-time { font-size: .75rem; color: var(--c-text-4); margin-top: .35rem; }

.typing-indicator { display: flex; gap: .3rem; padding: 1rem; }
.typing-indicator span { width: 8px; height: 8px; border-radius: 50%; background: var(--c-text-4); animation: typing 1.4s infinite; }
.typing-indicator span:nth-child(2) { animation-delay: .2s; }
.typing-indicator span:nth-child(3) { animation-delay: .4s; }
@keyframes typing { 0%, 60%, 100% { opacity: .3; } 30% { opacity: 1; } }

.chat-input-area { display: flex; gap: .75rem; padding: 1rem; border-top: 1px solid var(--c-border); background: var(--c-surface); border-radius: 0 0 var(--r-lg) var(--r-lg); }
.chat-input { flex: 1; min-height: 60px; max-height: 150px; resize: vertical; }

/* Summary */
.summary-card { padding: 2.5rem; text-align: center; }
.summary-emoji { font-size: 3rem; margin-bottom: .75rem; }
.summary-card h2 { font-size: 1.5rem; margin-bottom: 1.5rem; }
.summary-content { text-align: left; background: var(--c-bg); padding: 1.5rem; border-radius: var(--r-md); margin-bottom: 1.5rem; line-height: 1.8; }
.summary-actions { display: flex; gap: .75rem; justify-content: center; }

@media (max-width: 640px) {
  .chat-mode { height: calc(100vh - 150px); }
  .msg-content { max-width: 85%; }
}
</style>
