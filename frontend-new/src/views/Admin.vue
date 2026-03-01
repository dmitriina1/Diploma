<template>
  <div class="page">
    <NavBar />
    <div class="admin-wrap">
      <!-- Header -->
      <header class="admin-header">
        <div>
          <h1>⚙️ Панель управления</h1>
          <p class="sub">Обработка видео, утверждение вопросов, генерация ответов</p>
        </div>
        <button class="btn btn-primary" @click="showUpload = true">+ Загрузить видео</button>
      </header>

      <!-- Active Tasks -->
      <section v-if="allTasks.length > 0" class="tasks-section">
        <div class="sec-title"><span v-if="hasActive" class="spinner spinner-sm"></span> Обработка видео <span v-if="activeTasks.length" class="badge badge-warn">{{ activeTasks.length }}</span></div>
        <div class="tasks-list">
          <div v-for="t in allTasks" :key="t.task_id" class="task-card card" :class="'st-' + t.status">
            <div class="task-top">
              <div class="task-title">
                <span class="badge" :class="taskBadge(t.status)">{{ statusLabel(t.status) }}</span>
                <span class="task-url">{{ trunc(t.video_url, 55) }}</span>
              </div>
              <span class="task-time">{{ fmtTime(t.created_at) }}</span>
            </div>
            <div class="progress"><div class="progress-fill" :style="{ width: (t.progress || 0) + '%' }"></div></div>
            <div class="task-step">{{ t.step || 'Ожидание...' }}</div>
            <div v-if="t.status === 'error' && t.error" class="task-err">⚠ {{ t.error }}</div>
            <div v-if="t.status === 'completed' && t.result" class="task-ok">✅ Найдено {{ t.result.questions_count }} вопросов</div>
            <div class="logs-toggle" @click="toggleLogs(t.task_id)">{{ expandedLogs[t.task_id] ? '▲ Скрыть' : '▼ Показать' }} логи</div>
            <div v-if="expandedLogs[t.task_id] && t.logs?.length" class="task-logs">
              <div v-for="(l, i) in t.logs" :key="i" class="log-row" :class="'log-' + l.status">
                <span class="log-t">{{ fmtLogTime(l.time) }}</span>
                <span>{{ l.message }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Tabs -->
      <div class="tab-bar">
        <button v-for="(t, i) in tabs" :key="i" class="tab-btn" :class="{ active: activeTab === i }" @click="activeTab = i">{{ t }}</button>
      </div>

      <!-- Tab: Questions -->
      <div v-show="activeTab === 0" class="tab-panel">
        <div class="tp-toolbar">
          <button class="btn btn-secondary btn-sm" @click="bulkGenerate" :disabled="bulkGenerating">{{ bulkGenerating ? 'Генерация...' : '✨ Массовая генерация ответов' }}</button>
        </div>
        <div class="tp-filters">
          <input v-model="qSearch" class="input" placeholder="Поиск..." style="max-width:260px" />
          <select v-model="qTopic" class="input" style="max-width:180px"><option value="">Все темы</option><option v-for="t in topics" :key="t" :value="t">{{ t }}</option></select>
          <select v-model="qStatus" class="input" style="max-width:160px"><option value="">Все статусы</option><option value="approved">Одобренные</option><option value="unapproved">Не одобренные</option></select>
        </div>
        <!-- Bulk actions -->
        <div v-if="selectedQIds.length" class="bulk-bar">
          <span>Выбрано: {{ selectedQIds.length }}</span>
          <button class="btn btn-ok btn-sm" @click="bulkApprove">Одобрить</button>
          <button class="btn btn-warn btn-sm" @click="bulkRevoke">Отозвать</button>
          <button class="btn btn-err btn-sm" @click="bulkDelete">Удалить</button>
        </div>
        <div class="table-wrap">
          <table class="tbl">
            <thead><tr>
              <th style="width:36px"><input type="checkbox" :checked="allQSelected" @change="toggleAllQ" /></th>
              <th>Вопрос</th><th style="width:110px">Тема</th><th style="width:90px">Сложность</th><th style="width:70px">%</th><th style="width:90px">Статус</th><th style="width:120px"></th>
            </tr></thead>
            <tbody>
              <tr v-for="q in filteredAdminQ" :key="q.id" @click="openQDetail(q)">
                <td @click.stop><input type="checkbox" :checked="selectedQIds.includes(q.id)" @change="toggleQ(q.id)" /></td>
                <td class="q-cell">{{ trunc(q.question, 80) }}</td>
                <td><span class="badge badge-info">{{ q.topic }}</span></td>
                <td><span class="badge" :class="diffBadge(q.difficulty)">{{ q.difficulty }}</span></td>
                <td>{{ q.probability ? q.probability + '%' : '—' }}</td>
                <td><span class="badge" :class="q.approved ? 'badge-ok' : 'badge-warn'">{{ q.approved ? 'Да' : 'Нет' }}</span></td>
                <td @click.stop>
                  <button v-if="!q.approved" class="btn btn-ok btn-sm btn-icon" title="Одобрить" @click="approveOne(q.id)">✓</button>
                  <button v-else class="btn btn-warn btn-sm btn-icon" title="Отозвать" @click="revokeOne(q.id)">↩</button>
                  <button class="btn btn-err btn-sm btn-icon" title="Удалить" @click="deleteOne(q.id)">✕</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Tab: Suggestions -->
      <div v-show="activeTab === 1" class="tab-panel">
        <div v-if="sugLoading" class="center-block"><div class="spinner"></div></div>
        <table v-else class="tbl">
          <thead><tr><th>URL</th><th style="width:90px">Платформа</th><th style="width:100px">Статус</th><th style="width:120px">Отправитель</th><th style="width:150px">Комментарий</th><th style="width:100px"></th></tr></thead>
          <tbody>
            <tr v-for="s in sugList" :key="s.id">
              <td><a :href="s.url" target="_blank" class="link">{{ trunc(s.url, 50) }}</a></td>
              <td><span class="badge badge-info">{{ s.platform || '—' }}</span></td>
              <td><span class="badge" :class="sugBadge(s.status)">{{ sugLabel(s.status) }}</span></td>
              <td>{{ s.user_name || '—' }}</td>
              <td class="comment-cell">{{ trunc(s.comment, 60) }}</td>
              <td>
                <template v-if="s.status === 'pending'">
                  <button class="btn btn-ok btn-sm btn-icon" @click="processSug(s)" title="Обработать">▶</button>
                  <button class="btn btn-err btn-sm btn-icon" @click="rejectSug(s)" title="Отклонить">✕</button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Tab: Feedback -->
      <div v-show="activeTab === 2" class="tab-panel">
        <div v-if="fbLoading" class="center-block"><div class="spinner"></div></div>
        <table v-else class="tbl">
          <thead><tr><th style="width:80px">Тип</th><th>Комментарий</th><th style="width:100px">Рейтинг</th><th style="width:100px">Пользователь</th><th style="width:80px">Решено</th><th style="width:80px"></th></tr></thead>
          <tbody>
            <tr v-for="f in fbList" :key="f.id">
              <td><span class="badge badge-muted">{{ f.type || '—' }}</span></td>
              <td class="comment-cell">{{ trunc(f.comment, 80) }}</td>
              <td>{{ f.rating ? '⭐'.repeat(f.rating) : '—' }}</td>
              <td>{{ f.user_name || '—' }}</td>
              <td><span class="badge" :class="f.is_resolved ? 'badge-ok' : 'badge-warn'">{{ f.is_resolved ? 'Да' : 'Нет' }}</span></td>
              <td><button v-if="!f.is_resolved" class="btn btn-ok btn-sm btn-icon" @click="resolveFb(f)" title="Решено">✓</button></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Tab: Videos -->
      <div v-show="activeTab === 3" class="tab-panel">
        <div class="tp-toolbar">
          <input v-model="vidSearch" class="input" placeholder="Поиск видео..." style="max-width:260px" />
          <span class="muted">{{ filteredVids.length }} видео</span>
        </div>
        <div v-if="vidLoading" class="center-block"><div class="spinner"></div></div>
        <table v-else class="tbl">
          <thead><tr><th>Название</th><th style="width:100px">Платформа</th><th style="width:80px">Вопросов</th><th style="width:120px">Обработано</th><th style="width:100px"></th></tr></thead>
          <tbody>
            <tr v-for="v in filteredVids" :key="v.id">
              <td>
                <div v-if="editVidId === v.id" class="edit-inline">
                  <input v-model="editVidTitle" class="input" />
                  <button class="btn btn-ok btn-sm btn-icon" @click="saveVidTitle(v)">✓</button>
                  <button class="btn btn-ghost btn-sm btn-icon" @click="editVidId = null">✕</button>
                </div>
                <div v-else class="title-cell">
                  <span>{{ v.title || 'Без названия' }}</span>
                  <button class="btn btn-ghost btn-sm btn-icon" @click="editVidId = v.id; editVidTitle = v.title || ''" title="Переименовать">✏</button>
                </div>
              </td>
              <td><span class="badge badge-info">{{ v.platform }}</span></td>
              <td>{{ v.question_count || v.linked_questions || 0 }}</td>
              <td>{{ fmtTime(v.processed_at) }}</td>
              <td>
                <a v-if="v.youtube_url || v.url" :href="v.youtube_url || v.url" target="_blank" class="btn btn-ghost btn-sm btn-icon" title="Открыть">↗</a>
                <button class="btn btn-err btn-sm btn-icon" @click="deleteVid(v)" title="Удалить">🗑</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Tab: Test Assignments -->
      <div v-show="activeTab === 4" class="tab-panel">
        <div class="tp-toolbar">
          <button class="btn btn-primary btn-sm" @click="openTADialog(null)">+ Добавить</button>
          <input v-model="taSearchQ" class="input" placeholder="Поиск..." style="max-width:220px" />
          <span class="muted">{{ filteredTA.length }} заданий</span>
        </div>
        <table class="tbl">
          <thead><tr><th>Название</th><th style="width:120px">Компания</th><th style="width:140px">Профессия</th><th style="width:80px">Уровень</th><th style="width:80px"></th></tr></thead>
          <tbody>
            <tr v-for="a in filteredTA" :key="a.id">
              <td>{{ a.title }}</td>
              <td>{{ a.company || '—' }}</td>
              <td>{{ a.profession || '—' }}</td>
              <td><span class="badge" :class="diffBadge(a.difficulty)">{{ a.difficulty }}</span></td>
              <td>
                <button class="btn btn-ghost btn-sm btn-icon" @click="openTADialog(a)" title="Редактировать">✏</button>
                <button class="btn btn-err btn-sm btn-icon" @click="deleteTA(a)" title="Удалить">🗑</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Tab: Analytics -->
      <div v-show="activeTab === 5" class="tab-panel">
        <div v-if="anlLoading" class="center-block"><div class="spinner"></div></div>
        <template v-else>
          <div class="metrics-grid">
            <div class="metric-card"><div class="mv">{{ questionsStore.questions.length }}</div><div class="ml">Вопросов</div><div class="ms">{{ questionsStore.approvedQuestions.length }} одобрено</div></div>
            <div class="metric-card"><div class="mv">{{ anl.users?.total || 0 }}</div><div class="ml">Пользователей</div><div class="ms">{{ anl.users?.active_30d || 0 }} активных</div></div>
            <div class="metric-card"><div class="mv">{{ videosProcessed }}</div><div class="ml">Видео</div><div class="ms">~{{ anl.videos?.avg_questions || 0 }} вопр/видео</div></div>
            <div class="metric-card"><div class="mv">{{ anl.test_assignments?.total || 0 }}</div><div class="ml">Тестовых заданий</div></div>
            <div class="metric-card"><div class="mv">{{ anl.community?.total_answers || 0 }}</div><div class="ml">Ответов сообщества</div><div class="ms">{{ anl.community?.active_voters || 0 }} голосовали</div></div>
            <div class="metric-card"><div class="mv">{{ anl.trainer?.unique_users || 0 }}</div><div class="ml">Тренажёр</div><div class="ms">{{ anl.trainer?.total_reviews || 0 }} повторений</div></div>
          </div>

          <!-- Topic distribution -->
          <div class="anl-panel card" v-if="topicDist.length">
            <h4>Распределение по технологиям</h4>
            <table class="tbl tbl-sm">
              <thead><tr><th>Технология</th><th style="width:70px">Всего</th><th style="width:70px">Одобр.</th><th style="width:80px">С ответом</th></tr></thead>
              <tbody><tr v-for="t in topicDist" :key="t.topic"><td>{{ t.topic }}</td><td>{{ t.count }}</td><td>{{ t.approved }}</td><td>{{ t.with_answers }}</td></tr></tbody>
            </table>
          </div>

          <!-- Top bookmarked -->
          <div class="anl-row">
            <div class="anl-panel card" v-if="anl.top_bookmarked?.length">
              <h4>🔖 Топ сохранённых</h4>
              <div class="top-list"><div v-for="(q, i) in anl.top_bookmarked" :key="q.id" class="top-item"><span class="top-rank">#{{ i+1 }}</span><div class="top-txt">{{ trunc(q.question, 60) }}</div><span class="badge badge-warn">{{ q.saves }}</span></div></div>
            </div>
            <div class="anl-panel card" v-if="anl.top_probable?.length">
              <h4>📈 Топ по вероятности</h4>
              <div class="top-list"><div v-for="(q, i) in anl.top_probable" :key="q.id" class="top-item"><span class="top-rank">#{{ i+1 }}</span><div class="top-txt">{{ trunc(q.question, 60) }}</div><span class="badge badge-ok">{{ q.probability }}%</span></div></div>
            </div>
          </div>

          <div class="sys-actions">
            <button class="btn btn-ghost btn-sm" @click="loadAnalytics">🔄 Обновить</button>
            <button class="btn btn-secondary btn-sm" @click="recalcProb" :disabled="recalculating">{{ recalculating ? '...' : '📊 Пересчитать вероятности' }}</button>
            <button class="btn btn-ghost btn-sm" @click="exportJSON">📥 JSON</button>
            <button class="btn btn-ghost btn-sm" @click="exportCSV">📥 CSV</button>
          </div>
        </template>
      </div>
    </div>

    <!-- Upload Dialog -->
    <Teleport to="body">
      <div v-if="showUpload" class="overlay" @click.self="showUpload = false">
        <div class="dialog card" style="max-width:520px">
          <div class="dialog-head"><h3>Загрузить видео</h3><button class="btn btn-ghost btn-icon btn-sm" @click="showUpload = false">✕</button></div>
          <div class="dialog-body">
            <div class="mode-toggle">
              <button class="btn btn-sm" :class="uploadMode === 'url' ? 'btn-primary' : 'btn-secondary'" @click="uploadMode = 'url'">🔗 Ссылка</button>
              <button class="btn btn-sm" :class="uploadMode === 'file' ? 'btn-primary' : 'btn-secondary'" @click="uploadMode = 'file'">📁 Файл</button>
            </div>
            <div v-if="uploadMode === 'url'" class="field" style="margin-top:1rem">
              <label>Ссылка на видео</label>
              <input v-model="uploadUrl" class="input" placeholder="https://youtube.com/watch?v=..." />
            </div>
            <div v-if="uploadMode === 'file'" class="field" style="margin-top:1rem">
              <label>Видеофайл</label>
              <div class="drop-zone" @dragover.prevent @drop.prevent="onUploadDrop">
                <template v-if="!uploadFile">
                  <p>Перетащите или <a href="#" @click.prevent="$refs.uf.click()">выберите</a></p>
                </template>
                <template v-else>
                  <span>{{ uploadFile.name }} ({{ (uploadFile.size/1024/1024).toFixed(1) }} MB)</span>
                  <button class="btn btn-ghost btn-sm btn-icon" @click="uploadFile = null">✕</button>
                </template>
              </div>
              <input ref="uf" type="file" accept="video/*" style="display:none" @change="uploadFile = $event.target.files[0]" />
            </div>
            <div v-if="uploadPct > 0 && uploadPct < 100" class="progress" style="margin-top:.5rem"><div class="progress-fill" :style="{ width: uploadPct + '%' }"></div></div>
            <button class="btn btn-primary" style="width:100%;margin-top:1rem" @click="submitUpload" :disabled="uploadBusy || (uploadMode === 'url' ? !uploadUrl : !uploadFile)">
              {{ uploadBusy ? 'Обработка...' : 'Отправить' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- TA Dialog -->
    <Teleport to="body">
      <div v-if="showTA" class="overlay" @click.self="showTA = false">
        <div class="dialog card" style="max-width:640px">
          <div class="dialog-head"><h3>{{ editingTA ? 'Редактировать' : 'Новое задание' }}</h3><button class="btn btn-ghost btn-icon btn-sm" @click="showTA = false">✕</button></div>
          <div class="dialog-body ta-form">
            <div class="field"><label>Название *</label><input v-model="taForm.title" class="input" /></div>
            <div class="field"><label>Описание</label><textarea v-model="taForm.description" class="input" rows="4"></textarea></div>
            <div class="field-row-2">
              <div class="field"><label>Компания</label><input v-model="taForm.company" class="input" /></div>
              <div class="field"><label>Профессия</label><input v-model="taForm.profession" class="input" /></div>
            </div>
            <div class="field-row-2">
              <div class="field"><label>Уровень</label><select v-model="taForm.difficulty" class="input"><option value="junior">Junior</option><option value="middle">Middle</option><option value="senior">Senior</option></select></div>
              <div class="field"><label>Источник</label><input v-model="taForm.source" class="input" /></div>
            </div>
            <div class="field"><label>Навыки (через запятую)</label><input v-model="taForm.skills" class="input" /></div>
            <div class="field"><label>Ссылка</label><input v-model="taForm.link" class="input" /></div>
            <div style="display:flex;gap:.5rem;justify-content:flex-end;margin-top:.5rem">
              <button class="btn btn-ghost" @click="showTA = false">Отмена</button>
              <button class="btn btn-primary" @click="saveTA" :disabled="taSaving || !taForm.title">{{ taSaving ? '...' : editingTA ? 'Сохранить' : 'Создать' }}</button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Question Detail Dialog -->
    <Teleport to="body">
      <div v-if="qDetailId" class="overlay" @click.self="qDetailId = null">
        <div class="dialog card" style="max-width:700px;max-height:80vh;overflow-y:auto">
          <div class="dialog-head"><h3>Вопрос #{{ qDetailId }}</h3><button class="btn btn-ghost btn-icon btn-sm" @click="qDetailId = null">✕</button></div>
          <div v-if="qDetail" class="dialog-body">
            <div class="qd-badges" style="margin-bottom:.75rem">
              <span class="badge badge-info">{{ qDetail.topic }}</span>
              <span class="badge" :class="diffBadge(qDetail.difficulty)">{{ qDetail.difficulty }}</span>
              <span class="badge" :class="qDetail.approved ? 'badge-ok' : 'badge-warn'">{{ qDetail.approved ? 'Одобрен' : 'Не одобрен' }}</span>
            </div>
            <h4 style="margin-bottom:.75rem">{{ qDetail.question }}</h4>
            <div v-if="qDetail.answer" class="qd-answer" v-html="qDetail.answer.replace(/\n/g, '<br>')"></div>
            <div v-else class="qd-no-answer">Ответ не сгенерирован</div>
            <div style="display:flex;gap:.5rem;margin-top:1rem">
              <button v-if="!qDetail.approved" class="btn btn-ok btn-sm" @click="approveOne(qDetail.id); qDetailId = null">Одобрить</button>
              <button v-else class="btn btn-warn btn-sm" @click="revokeOne(qDetail.id); qDetailId = null">Отозвать</button>
              <button class="btn btn-secondary btn-sm" @click="generateOne(qDetail.id)">✨ Генерировать ответ</button>
              <button class="btn btn-err btn-sm" @click="deleteOne(qDetail.id); qDetailId = null">Удалить</button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useQuestionsStore, useTasksStore } from '../store'
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'
import api from '../api/client'

const questionsStore = useQuestionsStore()
const tasksStore = useTasksStore()

const tabs = ['Вопросы', 'Предложения', 'Обратная связь', 'Видео', 'Тестовые задания', 'Аналитика']
const activeTab = ref(0)
const expandedLogs = ref({})

// Tasks
const allTasks = computed(() => tasksStore.tasks)
const activeTasks = computed(() => tasksStore.activeTasks)
const hasActive = computed(() => tasksStore.hasActiveTasks)
const taskBadge = (s) => ({ completed: 'badge-ok', error: 'badge-err' }[s] || 'badge-info')
const statusLabel = (s) => ({ pending: 'Ожидание', downloading: 'Скачивание', transcribing: 'Транскрибация', extracting: 'Извлечение', saving: 'Сохранение', completed: 'Готово', error: 'Ошибка' }[s] || s)
const toggleLogs = (id) => { expandedLogs.value[id] = !expandedLogs.value[id] }

// Questions tab
const qSearch = ref('')
const qTopic = ref('')
const qStatus = ref('')
const selectedQIds = ref([])
const qDetailId = ref(null)
const qDetail = computed(() => questionsStore.adminQuestions.find(q => q.id === qDetailId.value))
const topics = computed(() => questionsStore.topics)

const filteredAdminQ = computed(() => {
  let qs = questionsStore.adminQuestions
  if (qTopic.value) qs = qs.filter(q => q.topic === qTopic.value)
  if (qStatus.value === 'approved') qs = qs.filter(q => q.approved)
  if (qStatus.value === 'unapproved') qs = qs.filter(q => !q.approved)
  if (qSearch.value) { const s = qSearch.value.toLowerCase(); qs = qs.filter(q => q.question?.toLowerCase().includes(s) || q.topic?.toLowerCase().includes(s)) }
  return qs
})
const allQSelected = computed(() => filteredAdminQ.value.length > 0 && filteredAdminQ.value.every(q => selectedQIds.value.includes(q.id)))
const toggleAllQ = () => { if (allQSelected.value) selectedQIds.value = []; else selectedQIds.value = filteredAdminQ.value.map(q => q.id) }
const toggleQ = (id) => { const i = selectedQIds.value.indexOf(id); if (i >= 0) selectedQIds.value.splice(i, 1); else selectedQIds.value.push(id) }
const openQDetail = (q) => { qDetailId.value = q.id }

const approveOne = async (id) => { await questionsStore.approveQuestions([id]) }
const revokeOne = async (id) => { await questionsStore.revokeQuestions([id]) }
const deleteOne = async (id) => { if (confirm('Удалить вопрос?')) await questionsStore.deleteQuestion(id) }
const generateOne = async (id) => { try { await questionsStore.generateAnswer(id) } catch {} }
const bulkApprove = async () => { await questionsStore.approveQuestions(selectedQIds.value); selectedQIds.value = [] }
const bulkRevoke = async () => { await questionsStore.revokeQuestions(selectedQIds.value); selectedQIds.value = [] }
const bulkDelete = async () => { if (!confirm(`Удалить ${selectedQIds.value.length} вопросов?`)) return; for (const id of selectedQIds.value) await questionsStore.deleteQuestion(id); selectedQIds.value = [] }

const bulkGenerating = ref(false)
const bulkGenerate = async () => {
  const toGen = questionsStore.approvedQuestions.filter(q => !q.answer)
  if (!toGen.length) { alert('Все утверждённые вопросы уже имеют ответы!'); return }
  if (!confirm(`Сгенерировать ответы для ${toGen.length} вопросов?`)) return
  bulkGenerating.value = true; let ok = 0, fail = 0
  for (const q of toGen) { try { await questionsStore.generateAnswer(q.id); ok++ } catch { fail++ } }
  bulkGenerating.value = false; alert(`Готово! Успешно: ${ok}, ошибки: ${fail}`)
  await questionsStore.fetchQuestions()
}

// Suggestions tab
const sugList = ref([]); const sugLoading = ref(false)
const sugBadge = (s) => ({ pending: 'badge-info', approved: 'badge-ok', rejected: 'badge-err', processing: 'badge-warn', completed: 'badge-ok' }[s] || 'badge-muted')
const sugLabel = (s) => ({ pending: 'Ожидает', approved: 'Одобрено', rejected: 'Отклонено', processing: 'В обработке', completed: 'Обработано' }[s] || s)
const loadSuggestions = async () => { sugLoading.value = true; try { const r = await api.getAdminSuggestions(); sugList.value = r.data.suggestions || [] } catch {} sugLoading.value = false }
const processSug = async (s) => { try { await api.processSuggestion(s.id); s.status = 'processing'; await loadSuggestions() } catch (e) { alert('Ошибка: ' + (e.response?.data?.detail || e.message)) } }
const rejectSug = async (s) => { try { await api.updateSuggestion(s.id, { status: 'rejected' }); await loadSuggestions() } catch {} }

// Feedback tab
const fbList = ref([]); const fbLoading = ref(false)
const loadFeedback = async () => { fbLoading.value = true; try { const r = await api.getAdminFeedback(); fbList.value = r.data.feedback || r.data || [] } catch {} fbLoading.value = false }
const resolveFb = async (f) => { try { await api.updateFeedback(f.id, { is_resolved: true }); f.is_resolved = true } catch {} }

// Videos tab
const adminVids = ref([]); const vidLoading = ref(false); const vidSearch = ref('')
const editVidId = ref(null); const editVidTitle = ref('')
const filteredVids = computed(() => { if (!vidSearch.value) return adminVids.value; const s = vidSearch.value.toLowerCase(); return adminVids.value.filter(v => (v.title || '').toLowerCase().includes(s)) })
const loadVids = async () => { vidLoading.value = true; try { const r = await api.getProcessedVideos(); adminVids.value = r.data?.videos || [] } catch {} vidLoading.value = false }
const saveVidTitle = async (v) => { try { await api.updateVideo(v.id, { title: editVidTitle.value }); v.title = editVidTitle.value; editVidId.value = null } catch (e) { alert('Ошибка') } }
const deleteVid = async (v) => { if (!confirm(`Удалить видео «${v.title || v.youtube_url}»?`)) return; try { await api.deleteVideo(v.id); adminVids.value = adminVids.value.filter(x => x.id !== v.id) } catch (e) { alert('Ошибка') } }

// TA tab
const taList = ref([]); const taSearchQ = ref(''); const showTA = ref(false); const editingTA = ref(null); const taSaving = ref(false)
const taForm = ref({ title: '', description: '', company: '', profession: '', difficulty: 'middle', skills: '', link: '', source: '' })
const filteredTA = computed(() => { if (!taSearchQ.value) return taList.value; const s = taSearchQ.value.toLowerCase(); return taList.value.filter(a => (a.title || '').toLowerCase().includes(s) || (a.company || '').toLowerCase().includes(s)) })
const loadTA = async () => { try { const r = await api.getTestAssignments({ per_page: 500 }); taList.value = r.data.assignments || [] } catch {} }
const openTADialog = (item) => {
  if (item) { editingTA.value = item; taForm.value = { title: item.title || '', description: item.description || '', company: item.company || '', profession: item.profession || '', difficulty: item.difficulty || 'middle', skills: item.skills || '', link: item.link || '', source: item.source || '' } }
  else { editingTA.value = null; taForm.value = { title: '', description: '', company: '', profession: '', difficulty: 'middle', skills: '', link: '', source: '' } }
  showTA.value = true
}
const saveTA = async () => {
  taSaving.value = true
  try { if (editingTA.value) await api.updateTestAssignment(editingTA.value.id, taForm.value); else await api.createTestAssignment(taForm.value); showTA.value = false; await loadTA() }
  catch (e) { alert('Ошибка: ' + (e.response?.data?.detail || e.message)) }
  taSaving.value = false
}
const deleteTA = async (a) => { if (!confirm(`Удалить «${a.title}»?`)) return; try { await api.deleteTestAssignment(a.id); taList.value = taList.value.filter(x => x.id !== a.id) } catch {} }

// Analytics tab
const anl = ref({}); const anlLoading = ref(false); const recalculating = ref(false)
const videosProcessed = computed(() => new Set(questionsStore.questions.map(q => q.video_url)).size)
const topicDist = computed(() => questionsStore.topics.map(topic => {
  const qs = questionsStore.questions.filter(q => q.topic === topic)
  return { topic, count: qs.length, approved: qs.filter(q => q.is_approved || q.approved).length, with_answers: qs.filter(q => q.answer).length }
}).sort((a, b) => b.count - a.count))

const loadAnalytics = async () => { anlLoading.value = true; try { const r = await api.getAdminAnalytics(); anl.value = r.data } catch {} anlLoading.value = false }
const recalcProb = async () => { if (!confirm('Пересчитать?')) return; recalculating.value = true; try { await api.recalculateProbabilities(); await questionsStore.fetchQuestions() } catch {} recalculating.value = false }
const exportJSON = async () => { try { const r = await api.getAdminQuestions(); const b = new Blob([JSON.stringify(r.data, null, 2)], { type: 'application/json' }); const u = URL.createObjectURL(b); const a = document.createElement('a'); a.href = u; a.download = 'questions.json'; a.click(); URL.revokeObjectURL(u) } catch {} }
const exportCSV = async () => { try { const r = await api.exportCSV(); const b = new Blob([r.data], { type: 'text/csv' }); const u = URL.createObjectURL(b); const a = document.createElement('a'); a.href = u; a.download = 'questions.csv'; a.click(); URL.revokeObjectURL(u) } catch {} }

// Upload Dialog
const showUpload = ref(false); const uploadMode = ref('url'); const uploadUrl = ref(''); const uploadFile = ref(null); const uploadPct = ref(0); const uploadBusy = ref(false)
const onUploadDrop = (e) => { const f = e.dataTransfer?.files?.[0]; if (f?.type.startsWith('video/')) uploadFile.value = f }
const submitUpload = async () => {
  uploadBusy.value = true
  try {
    if (uploadMode.value === 'url') { await tasksStore.processVideo(uploadUrl.value); uploadUrl.value = '' }
    else if (uploadFile.value) {
      const fd = new FormData(); fd.append('file', uploadFile.value); fd.append('topic', 'General'); fd.append('difficulty', 'middle')
      const r = await api.uploadVideoFile(fd, { onUploadProgress: (e) => { uploadPct.value = Math.round((e.loaded * 100) / e.total) } })
      if (r.data?.task_id) tasksStore.startPolling(r.data.task_id)
      uploadFile.value = null; uploadPct.value = 0
    }
    showUpload.value = false
  } catch (e) { alert('Ошибка: ' + (e.response?.data?.detail || e.message)) }
  uploadBusy.value = false
}

// Helpers
const diffBadge = (d) => ({ junior: 'badge-ok', middle: 'badge-warn', senior: 'badge-err' }[d] || 'badge-muted')
const trunc = (s, n) => { if (!s) return '—'; return s.length > n ? s.substring(0, n - 3) + '...' : s }
const fmtTime = (t) => t ? new Date(t).toLocaleString('ru-RU', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' }) : ''
const fmtLogTime = (t) => t ? new Date(t).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''

onMounted(async () => {
  await Promise.all([
    questionsStore.fetchQuestions(),
    questionsStore.fetchAdminQuestions(),
    tasksStore.fetchAllTasks(),
    loadVids(), loadTA(),
    loadSuggestions(), loadFeedback(),
    loadAnalytics()
  ])
  tasksStore.startGlobalPolling()
  for (const t of tasksStore.activeTasks) tasksStore.startPolling(t.task_id)
})
onUnmounted(() => tasksStore.stopGlobalPolling())
</script>

<style scoped>
.admin-wrap { max-width: 1400px; margin: 0 auto; padding: 1.5rem 2rem 3rem; }
.admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--c-border); }
.admin-header h1 { font-size: 1.5rem; font-weight: 700; margin-bottom: .15rem; }
.sub { color: var(--c-text-3); font-size: .85rem; }

/* Tasks */
.tasks-section { margin-bottom: 1.5rem; }
.tasks-list { display: flex; flex-direction: column; gap: .5rem; }
.task-card { padding: 1rem 1.15rem; }
.task-card.st-error { border-color: rgba(239,68,68,.35); }
.task-card.st-completed { border-color: rgba(34,197,94,.3); }
.task-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: .5rem; }
.task-title { display: flex; align-items: center; gap: .5rem; }
.task-url { font-size: .82rem; color: var(--c-text-4); font-family: monospace; }
.task-time { font-size: .72rem; color: var(--c-text-4); }
.task-step { font-size: .82rem; color: var(--c-text-3); margin-top: .35rem; }
.task-err { margin-top: .4rem; padding: .4rem .6rem; background: var(--c-err-bg); color: var(--c-err); border-radius: var(--r-sm); font-size: .82rem; }
.task-ok { margin-top: .4rem; padding: .4rem .6rem; background: var(--c-ok-bg); color: var(--c-ok); border-radius: var(--r-sm); font-size: .82rem; }
.logs-toggle { margin-top: .35rem; font-size: .72rem; color: var(--c-text-4); cursor: pointer; user-select: none; }
.logs-toggle:hover { color: var(--c-text-2); }
.task-logs { margin-top: .35rem; max-height: 180px; overflow-y: auto; background: var(--c-bg); border-radius: var(--r-sm); padding: .4rem; font-family: monospace; font-size: .72rem; }
.log-row { display: flex; gap: .5rem; padding: .1rem 0; color: var(--c-text-4); }
.log-row.log-error { color: var(--c-err); }
.log-row.log-completed { color: var(--c-ok); }
.log-t { color: var(--c-text-4); flex-shrink: 0; }

/* Tabs */
.tab-bar { display: flex; gap: 0; border-bottom: 1px solid var(--c-border); margin-bottom: 0; overflow-x: auto; }
.tab-btn {
  padding: .7rem 1.2rem; border: none; background: none; color: var(--c-text-3);
  font-size: .88rem; font-weight: 600; cursor: pointer; white-space: nowrap;
  border-bottom: 2px solid transparent; transition: all var(--dur);
}
.tab-btn.active { color: var(--c-brand); border-bottom-color: var(--c-brand); }
.tab-btn:hover:not(.active) { color: var(--c-text); }
.tab-panel { padding: 1.25rem 0; }

.tp-toolbar { display: flex; align-items: center; gap: .75rem; margin-bottom: 1rem; flex-wrap: wrap; }
.tp-filters { display: flex; gap: .5rem; margin-bottom: .75rem; flex-wrap: wrap; }
.bulk-bar { display: flex; align-items: center; gap: .5rem; padding: .6rem .8rem; background: var(--c-brand-bg); border-radius: var(--r-sm); margin-bottom: .75rem; font-size: .85rem; color: var(--c-brand-h); }
.muted { color: var(--c-text-4); font-size: .82rem; margin-left: auto; }

/* Table */
.table-wrap { overflow-x: auto; }
.tbl { width: 100%; border-collapse: collapse; font-size: .88rem; }
.tbl th { text-align: left; padding: .6rem .5rem; color: var(--c-text-3); font-weight: 600; font-size: .78rem; text-transform: uppercase; letter-spacing: .03em; border-bottom: 1px solid var(--c-border); }
.tbl td { padding: .55rem .5rem; border-bottom: 1px solid var(--c-border); color: var(--c-text-2); vertical-align: middle; }
.tbl tbody tr { cursor: pointer; transition: background var(--dur); }
.tbl tbody tr:hover { background: var(--c-bg-2); }
.tbl.tbl-sm { font-size: .82rem; }
.tbl.tbl-sm td, .tbl.tbl-sm th { padding: .4rem .35rem; }
.q-cell { max-width: 350px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.comment-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.link { color: var(--c-brand); text-decoration: none; }
.link:hover { text-decoration: underline; }

.title-cell { display: flex; align-items: center; gap: .25rem; }
.edit-inline { display: flex; align-items: center; gap: .25rem; }

.center-block { display: flex; justify-content: center; padding: 2rem; }
.spinner-sm { width: 16px; height: 16px; }

/* Analytics */
.metrics-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: .75rem; margin-bottom: 1.5rem; }
.metric-card { background: var(--c-surface); border: 1px solid var(--c-border); border-radius: var(--r-md); padding: 1.15rem; }
.mv { font-size: 1.75rem; font-weight: 800; color: var(--c-text); }
.ml { font-size: .82rem; color: var(--c-text-3); margin-top: .1rem; }
.ms { font-size: .72rem; color: var(--c-text-4); }
.anl-panel { padding: 1.15rem; margin-bottom: 1rem; }
.anl-panel h4 { font-size: .95rem; font-weight: 600; margin-bottom: .75rem; }
.anl-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.top-list { display: flex; flex-direction: column; gap: .35rem; max-height: 300px; overflow-y: auto; }
.top-item { display: flex; align-items: center; gap: .5rem; padding: .35rem .5rem; background: var(--c-bg-2); border-radius: var(--r-sm); }
.top-rank { font-size: .78rem; font-weight: 700; color: var(--c-text-4); min-width: 22px; }
.top-txt { flex: 1; font-size: .82rem; color: var(--c-text-2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sys-actions { display: flex; gap: .5rem; flex-wrap: wrap; padding: .75rem; background: var(--c-surface); border: 1px solid var(--c-border); border-radius: var(--r-md); }

/* Dialogs */
.overlay { position: fixed; inset: 0; z-index: 1000; background: rgba(0,0,0,.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; padding: 1.5rem; }
.dialog { width: 100%; }
.dialog-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.dialog-head h3 { font-size: 1.1rem; font-weight: 600; }
.dialog-body { display: flex; flex-direction: column; gap: .9rem; }
.mode-toggle { display: flex; gap: .4rem; }
.field { display: flex; flex-direction: column; gap: .3rem; }
.field label { font-size: .82rem; color: var(--c-text-3); font-weight: 500; }
.field textarea { resize: vertical; font-family: inherit; }
.field-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: .75rem; }
.drop-zone { border: 2px dashed var(--c-border); border-radius: var(--r-md); padding: 1.5rem; text-align: center; }
.drop-zone p { color: var(--c-text-3); font-size: .88rem; }
.drop-zone a { color: var(--c-brand); text-decoration: underline; cursor: pointer; }

.qd-answer { background: var(--c-bg-2); border-radius: var(--r-md); padding: 1rem; font-size: .88rem; color: var(--c-text-2); line-height: 1.6; }
.qd-no-answer { color: var(--c-text-4); font-style: italic; }

@media (max-width: 768px) {
  .admin-wrap { padding: 1rem; }
  .admin-header { flex-direction: column; gap: .75rem; align-items: flex-start; }
  .anl-row { grid-template-columns: 1fr; }
  .field-row-2 { grid-template-columns: 1fr; }
  .tab-btn { padding: .6rem .8rem; font-size: .82rem; }
}
</style>
