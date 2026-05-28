<template>
  <div class="admin-page">
    <NavBar />

    <div class="admin-container">
      <!-- Header -->
      <header class="admin-header">
        <div class="header-left">
          <h1><i class="pi pi-sliders-h"></i> Панель управления</h1>
          <p class="subtitle">Обработка видео, утверждение вопросов, генерация ответов и управление контентом</p>
        </div>
        <Button label="Загрузить видео" icon="pi pi-plus" @click="showUploadDialog = true" class="upload-btn" />
      </header>

      <!-- Active Tasks Panel (always visible when tasks exist) -->
      <section v-if="allTasks.length > 0" class="tasks-section">
        <div class="section-title">
          <i class="pi pi-spinner pi-spin" v-if="hasActiveTasks"></i>
          <i class="pi pi-list" v-else></i>
          <span>Обработка видео</span>
          <Badge :value="activeTasks.length" severity="warning" v-if="activeTasks.length" />
        </div>
        
        <div class="tasks-list">
          <div v-for="task in allTasks" :key="task.task_id" 
               class="task-card" :class="'status-' + task.status">
            <div class="task-header">
              <div class="task-title">
                <Tag :value="getStatusLabel(task.status)" :severity="getStatusSeverity(task.status)" :icon="getStatusIcon(task.status)" />
                <span class="task-url" :title="task.video_url">{{ truncateUrl(task.video_url) }}</span>
              </div>
              <span class="task-time">{{ formatTime(task.created_at) }}</span>
            </div>
            
            <ProgressBar :value="task.progress" :showValue="true" 
                         :class="{ 'error-bar': task.status === 'error' }" />
            
            <div class="task-step">
              <i :class="getStepIcon(task.status)"></i>
              {{ task.step || 'Ожидание...' }}
            </div>
            
            <!-- Error display -->
            <div v-if="task.status === 'error' && task.error" class="task-error">
              <i class="pi pi-exclamation-triangle"></i>
              {{ task.error }}
            </div>
            
            <!-- Result summary -->
            <div v-if="task.status === 'completed' && task.result" class="task-result">
              <i class="pi pi-check-circle"></i>
              Найдено {{ task.result.questions_count }} вопросов
            </div>
            
            <!-- Logs toggle -->
            <div class="task-logs-toggle" @click="toggleLogs(task.task_id)">
              <i :class="expandedLogs[task.task_id] ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"></i>
              <span>{{ expandedLogs[task.task_id] ? 'Скрыть логи' : 'Показать логи' }}</span>
            </div>
            
            <transition name="slide">
              <div v-if="expandedLogs[task.task_id] && task.logs?.length" class="task-logs">
                <div v-for="(log, i) in task.logs" :key="i" class="log-entry" :class="'log-' + log.status">
                  <span class="log-time">{{ formatLogTime(log.time) }}</span>
                  <span class="log-msg">{{ log.message }}</span>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </section>

      <!-- Tabs -->
      <TabView class="admin-tabs" v-model:activeIndex="activeTab">
        <TabPanel>
          <template #header>
            <i class="pi pi-check-square mr-2"></i> Вопросы
          </template>
          <div class="tab-toolbar">
            <Button label="Массовая генерация ответов" icon="pi pi-sparkles" severity="help" size="small"
                    @click="bulkGenerate" :loading="bulkGenerating" 
                    v-tooltip="'Сгенерировать ответы для всех утверждённых вопросов без ответа'" />
          </div>
          <QuestionApproval ref="approvalComponent" />
        </TabPanel>

        <TabPanel>
          <template #header>
            <i class="pi pi-lightbulb mr-2"></i> Предложения
          </template>
          <SuggestionsManager ref="suggestionsComponent" />
        </TabPanel>

        <TabPanel>
          <template #header>
            <i class="pi pi-comments mr-2"></i> Обратная связь
          </template>
          <FeedbackManager ref="feedbackComponent" />
        </TabPanel>

        <TabPanel>
          <template #header>
            <i class="pi pi-video mr-2"></i> Видео
          </template>
          <div class="videos-manager">
            <div class="vm-toolbar">
              <InputText v-model="videoSearch" placeholder="Поиск видео..." class="vm-search" />
              <span class="vm-count">{{ filteredAdminVideos.length }} видео</span>
            </div>
            <div v-if="adminVideosLoading" class="vm-loading"><ProgressSpinner strokeWidth="3" /></div>
            <div v-else-if="filteredAdminVideos.length === 0" class="vm-empty">
              <i class="pi pi-video"></i>
              <p>Видео не найдены</p>
            </div>
            <DataTable v-else :value="filteredAdminVideos" stripedRows :paginator="true" :rows="10"
                       :rowsPerPageOptions="[10, 25, 50]" responsiveLayout="scroll">
              <Column field="title" header="Название" style="min-width:200px">
                <template #body="s">
                  <div v-if="editingVideoId === s.data.id" class="vm-edit-title">
                    <InputText v-model="editingVideoTitle" class="w-full" size="small" />
                    <Button icon="pi pi-check" size="small" severity="success" text @click="saveVideoTitle(s.data)" />
                    <Button icon="pi pi-times" size="small" severity="secondary" text @click="editingVideoId = null" />
                  </div>
                  <div v-else class="vm-title-cell">
                    <span>{{ s.data.title || 'Без названия' }}</span>
                    <Button icon="pi pi-pencil" size="small" text severity="secondary" 
                            @click="startEditVideo(s.data)" v-tooltip="'Переименовать'" />
                  </div>
                </template>
              </Column>
              <Column field="platform" header="Платформа" style="width:110px">
                <template #body="s"><Tag :value="s.data.platform" severity="info" /></template>
              </Column>
              <Column field="question_count" header="Вопросов" style="width:100px">
                <template #body="s"><Badge :value="s.data.question_count || s.data.linked_questions || 0" severity="info" /></template>
              </Column>
              <Column field="processed_at" header="Обработано" style="width:130px">
                <template #body="s">{{ formatTime(s.data.processed_at) }}</template>
              </Column>
              <Column header="" style="width:120px">
                <template #body="s">
                  <div class="vm-actions">
                    <Button icon="pi pi-external-link" size="small" text severity="info"
                            @click="openVideoUrl(s.data)" v-tooltip="'Открыть'" />
                    <Button icon="pi pi-trash" size="small" text severity="danger"
                            @click="deleteVideoConfirm(s.data)" v-tooltip="'Удалить'" />
                  </div>
                </template>
              </Column>
            </DataTable>
          </div>
        </TabPanel>

        <TabPanel>
          <template #header>
            <i class="pi pi-file-edit mr-2"></i> Тестовые задания
          </template>
          <div class="ta-manager">
            <div class="ta-toolbar">
              <Button label="Добавить задание" icon="pi pi-plus" size="small" @click="openTADialog(null)" />
              <InputText v-model="taSearch" placeholder="Поиск заданий..." class="ta-search" />
              <span class="ta-count">{{ filteredTAList.length }} заданий</span>
            </div>

            <div v-if="taLoading" class="ta-loading"><ProgressSpinner strokeWidth="3" /></div>
            <DataTable v-else :value="filteredTAList" stripedRows :paginator="true" :rows="10"
                       :rowsPerPageOptions="[10, 25, 50]" responsiveLayout="scroll" class="ta-table">
              <Column field="title" header="Название" style="min-width:200px">
                <template #body="s">
                  <div class="ta-title-cell">{{ s.data.title }}</div>
                </template>
              </Column>
              <Column field="company" header="Компания" style="width: 140px">
                <template #body="s">{{ s.data.company || '—' }}</template>
              </Column>
              <Column field="profession" header="Профессия" style="width: 160px">
                <template #body="s">{{ s.data.profession || '—' }}</template>
              </Column>
              <Column field="difficulty" header="Уровень" style="width: 100px">
                <template #body="s">
                  <Tag :value="s.data.difficulty" :severity="taDiffSeverity(s.data.difficulty)" />
                </template>
              </Column>
              <Column header="Действия" style="width: 130px">
                <template #body="s">
                  <div class="ta-actions">
                    <Button icon="pi pi-pencil" size="small" text severity="info" @click="openTADialog(s.data)" />
                    <Button icon="pi pi-trash" size="small" text severity="danger" @click="deleteTAConfirm(s.data)" />
                  </div>
                </template>
              </Column>
            </DataTable>
          </div>

          <Dialog v-model:visible="showTADialog" :header="editingTA ? 'Редактировать задание' : 'Новое тестовое задание'" :modal="true" :style="{ width: '720px' }" class="ta-dialog">
            <div class="ta-form">
              <!-- Section: Basic Info -->
              <div class="ta-form-section">
                <div class="ta-section-title"><i class="pi pi-info-circle"></i> Основная информация</div>
                <div class="ta-field">
                  <label><i class="pi pi-tag"></i> Название задания *</label>
                  <InputText v-model="taForm.title" placeholder="Например: ToDo App на React + TypeScript" class="w-full ta-input" />
                </div>
                <div class="ta-field">
                  <label><i class="pi pi-align-left"></i> Описание</label>
                  <Textarea v-model="taForm.description" rows="5" autoResize placeholder="Подробное описание задания, требования, что нужно реализовать..." class="w-full ta-input" />
                </div>
              </div>

              <!-- Section: Details -->
              <div class="ta-form-section">
                <div class="ta-section-title"><i class="pi pi-sliders-h"></i> Параметры</div>
                <div class="ta-field-row">
                  <div class="ta-field">
                    <label><i class="pi pi-building"></i> Компания</label>
                    <InputText v-model="taForm.company" placeholder="Яндекс, VK, Тинькофф..." class="w-full ta-input" />
                  </div>
                  <div class="ta-field">
                    <label><i class="pi pi-user"></i> Профессия</label>
                    <InputText v-model="taForm.profession" placeholder="Frontend разработчик" class="w-full ta-input" />
                  </div>
                </div>
                <div class="ta-field-row">
                  <div class="ta-field">
                    <label><i class="pi pi-signal"></i> Уровень сложности</label>
                    <Dropdown v-model="taForm.difficulty" :options="taDiffOptions" optionLabel="label" optionValue="value" class="w-full ta-input" />
                  </div>
                  <div class="ta-field">
                    <label><i class="pi pi-globe"></i> Источник</label>
                    <InputText v-model="taForm.source" placeholder="Habr, GitHub, HR..." class="w-full ta-input" />
                  </div>
                </div>
              </div>

              <!-- Section: Skills & Link -->
              <div class="ta-form-section">
                <div class="ta-section-title"><i class="pi pi-tags"></i> Навыки и ссылка</div>
                <div class="ta-field">
                  <label><i class="pi pi-list"></i> Навыки <span class="ta-hint">(через запятую)</span></label>
                  <InputText v-model="taForm.skills" placeholder="JavaScript, React, REST API, Docker..." class="w-full ta-input" />
                  <div v-if="taForm.skills" class="ta-skills-preview">
                    <Tag v-for="s in taForm.skills.split(',').map(x => x.trim()).filter(Boolean)" :key="s" :value="s" severity="info" rounded class="ta-skill-chip" />
                  </div>
                </div>
                <div class="ta-field">
                  <label><i class="pi pi-link"></i> Ссылка на задание</label>
                  <InputText v-model="taForm.link" placeholder="https://github.com/..." class="w-full ta-input" />
                </div>
              </div>
            </div>
            <template #footer>
              <div class="ta-dialog-footer">
                <Button label="Отмена" icon="pi pi-times" text severity="secondary" @click="showTADialog = false" />
                <Button :label="editingTA ? 'Сохранить изменения' : 'Создать задание'" :icon="editingTA ? 'pi pi-save' : 'pi pi-plus'" @click="saveTA" :loading="taSaving" :disabled="!taForm.title" />
              </div>
            </template>
          </Dialog>
        </TabPanel>
        
        <TabPanel>
          <template #header>
            <i class="pi pi-chart-bar mr-2"></i> Аналитика
          </template>

          <div v-if="analyticsLoading" class="analytics-loading">
            <ProgressSpinner strokeWidth="3" />
            <p>Загрузка аналитики...</p>
          </div>

          <div v-else class="analytics-dashboard">
            <!-- Row 1: Key Metrics -->
            <div class="analytics-section">
              <div class="section-header"><i class="pi pi-th-large"></i> Ключевые метрики</div>
              <div class="metrics-grid">
                <div class="metric-card metric-purple">
                  <i class="pi pi-question-circle"></i>
                  <div class="metric-value">{{ totalQuestions }}</div>
                  <div class="metric-label">Вопросов</div>
                  <div class="metric-sub">{{ approvedCount }} одобрено</div>
                </div>
                <div class="metric-card metric-blue">
                  <i class="pi pi-users"></i>
                  <div class="metric-value">{{ anl.users?.total || 0 }}</div>
                  <div class="metric-label">Пользователей</div>
                  <div class="metric-sub">{{ anl.users?.active_30d || 0 }} активных</div>
                </div>
                <div class="metric-card metric-green">
                  <i class="pi pi-video"></i>
                  <div class="metric-value">{{ videosProcessed }}</div>
                  <div class="metric-label">Видео</div>
                  <div class="metric-sub">~{{ anl.videos?.avg_questions || 0 }} вопр/видео</div>
                </div>
                <div class="metric-card metric-orange">
                  <i class="pi pi-file-edit"></i>
                  <div class="metric-value">{{ anl.test_assignments?.total || 0 }}</div>
                  <div class="metric-label">Тестовых заданий</div>
                </div>
                <div class="metric-card metric-pink">
                  <i class="pi pi-comments"></i>
                  <div class="metric-value">{{ anl.community?.total_answers || 0 }}</div>
                  <div class="metric-label">Ответов сообщества</div>
                  <div class="metric-sub">{{ anl.community?.active_voters || 0 }} голосовали</div>
                </div>
                <div class="metric-card metric-teal">
                  <i class="pi pi-bolt"></i>
                  <div class="metric-value">{{ anl.trainer?.unique_users || 0 }}</div>
                  <div class="metric-label">Пользуются тренажёром</div>
                  <div class="metric-sub">{{ anl.trainer?.total_reviews || 0 }} повторений</div>
                </div>
              </div>
            </div>

            <!-- Row 2: Users & Activity -->
            <div class="analytics-row">
              <div class="analytics-panel">
                <div class="panel-title"><i class="pi pi-users"></i> Пользователи</div>
                <div class="user-stats-grid">
                  <div class="mini-stat">
                    <span class="mini-val">{{ anl.users?.new_week || 0 }}</span>
                    <span class="mini-lbl">за неделю</span>
                  </div>
                  <div class="mini-stat">
                    <span class="mini-val">{{ anl.users?.new_month || 0 }}</span>
                    <span class="mini-lbl">за месяц</span>
                  </div>
                  <div class="mini-stat">
                    <span class="mini-val">{{ anl.users?.active_30d || 0 }}</span>
                    <span class="mini-lbl">активных (30д)</span>
                  </div>
                </div>
                <div class="chart-bar-list">
                  <div class="chart-bar-title">Регистрации (30 дней)</div>
                  <div class="bar-chart">
                    <div v-for="d in (anl.users?.registrations_by_day || []).slice(-14)" :key="d.day" class="bar-item" :title="d.day + ': ' + d.count">
                      <div class="bar-fill" :style="{ height: barHeight(d.count, anl.users?.registrations_by_day) }"></div>
                      <div class="bar-label">{{ d.day.slice(8) }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="analytics-panel">
                <div class="panel-title"><i class="pi pi-chart-line"></i> Вопросы (30 дней)</div>
                <div class="bar-chart tall-chart">
                  <div v-for="d in (anl.questions_by_day || []).slice(-14)" :key="d.day" class="bar-item" :title="d.day + ': ' + d.count">
                    <div class="bar-fill bar-blue" :style="{ height: barHeight(d.count, anl.questions_by_day) }"></div>
                    <div class="bar-label">{{ d.day.slice(8) }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Row 3: Technology Popularity -->
            <div class="analytics-row">
              <div class="analytics-panel wide-panel">
                <div class="panel-title"><i class="pi pi-star"></i> Популярность технологий</div>
                <div class="horizontal-bars">
                  <div v-for="(t, i) in (anl.topic_popularity || []).slice(0, 12)" :key="i" class="h-bar-row">
                    <div class="h-bar-label">{{ t.topic }}</div>
                    <div class="h-bar-track">
                      <div class="h-bar-fill" :style="{ width: hBarWidth(t.views, anl.topic_popularity) }"></div>
                    </div>
                    <div class="h-bar-value">{{ t.views }}</div>
                  </div>
                </div>
              </div>

              <div class="analytics-panel">
                <div class="panel-title"><i class="pi pi-chart-pie"></i> Уровни вопросов</div>
                <div class="donut-stats">
                  <div v-for="d in (anl.difficulty_distribution || [])" :key="d.difficulty" class="donut-item">
                    <Tag :value="d.difficulty || '—'" :severity="diffSeverityMap[d.difficulty] || 'info'" />
                    <span class="donut-count">{{ d.count }}</span>
                    <div class="donut-bar">
                      <div class="donut-bar-fill" :class="'diff-' + d.difficulty" :style="{ width: diffPercent(d.count) + '%' }"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Row 4: Tech Distribution Table + HH Skills -->
            <div class="analytics-row">
              <div class="analytics-panel">
                <div class="panel-title"><i class="pi pi-list"></i> Распределение по технологиям</div>
                <DataTable :value="topicDistribution" stripedRows :rows="8" :paginator="topicDistribution.length > 8" size="small" class="analytics-table">
                  <Column field="topic" header="Технология" />
                  <Column field="count" header="Всего" style="width:80px">
                    <template #body="s"><Badge :value="s.data.count" severity="info" /></template>
                  </Column>
                  <Column field="approved" header="Одобр." style="width:80px">
                    <template #body="s"><Badge :value="s.data.approved" severity="success" /></template>
                  </Column>
                  <Column field="with_answers" header="С ответом" style="width:90px">
                    <template #body="s"><Badge :value="s.data.with_answers" /></template>
                  </Column>
                </DataTable>
              </div>

              <div class="analytics-panel">
                <div class="panel-title"><i class="pi pi-briefcase"></i> Топ HH навыков</div>
                <div v-if="(anl.hh_top_skills || []).length === 0" class="empty-panel">Нет данных</div>
                <div v-else class="horizontal-bars compact">
                  <div v-for="(s, i) in (anl.hh_top_skills || []).slice(0, 10)" :key="i" class="h-bar-row">
                    <div class="h-bar-label">{{ s.skill }}</div>
                    <div class="h-bar-track">
                      <div class="h-bar-fill hh-fill" :style="{ width: hBarWidth(s.vacancies, anl.hh_top_skills.map(x => ({ views: x.vacancies }))) }"></div>
                    </div>
                    <div class="h-bar-value">{{ s.vacancies }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Row 5: Top Bookmarked + Top Probable -->
            <div class="analytics-row">
              <div class="analytics-panel">
                <div class="panel-title"><i class="pi pi-bookmark"></i> Топ сохранённых вопросов</div>
                <div v-if="(anl.top_bookmarked || []).length === 0" class="empty-panel">Нет данных</div>
                <div v-else class="top-list">
                  <div v-for="(q, i) in (anl.top_bookmarked || [])" :key="q.id" class="top-item">
                    <span class="top-rank">#{{ i + 1 }}</span>
                    <div class="top-info">
                      <div class="top-text">{{ q.question }}</div>
                      <Tag v-if="q.topic" :value="q.topic" severity="info" rounded size="small" />
                    </div>
                    <Badge :value="q.saves" severity="warning" />
                  </div>
                </div>
              </div>

              <div class="analytics-panel">
                <div class="panel-title"><i class="pi pi-percentage"></i> Топ по вероятности</div>
                <div class="top-list">
                  <div v-for="(q, i) in (anl.top_probable || [])" :key="q.id" class="top-item">
                    <span class="top-rank">#{{ i + 1 }}</span>
                    <div class="top-info">
                      <div class="top-text">{{ q.question }}</div>
                      <Tag v-if="q.topic" :value="q.topic" severity="info" rounded size="small" />
                    </div>
                    <Badge :value="q.probability + '%'" severity="success" />
                  </div>
                </div>
              </div>
            </div>

            <!-- Row 6: Feedback + Suggestions + TA -->
            <div class="analytics-row triple">
              <div class="analytics-panel">
                <div class="panel-title"><i class="pi pi-envelope"></i> Обратная связь</div>
                <div class="kpi-row">
                  <div class="kpi"><span class="kpi-val">{{ anl.feedback?.total || 0 }}</span><span class="kpi-lbl">всего</span></div>
                  <div class="kpi"><span class="kpi-val kpi-warn">{{ anl.feedback?.unresolved || 0 }}</span><span class="kpi-lbl">открыто</span></div>
                </div>
                <div v-if="(anl.feedback?.by_type || []).length" class="fb-types">
                  <div v-for="t in anl.feedback.by_type" :key="t.type" class="fb-type-item">
                    <span>{{ t.type }}</span>
                    <Badge :value="t.count" size="small" />
                  </div>
                </div>
              </div>

              <div class="analytics-panel">
                <div class="panel-title"><i class="pi pi-send"></i> Предложения</div>
                <div class="kpi-row">
                  <div class="kpi"><span class="kpi-val">{{ anl.suggestions?.total || 0 }}</span><span class="kpi-lbl">всего</span></div>
                  <div class="kpi"><span class="kpi-val kpi-warn">{{ anl.suggestions?.pending || 0 }}</span><span class="kpi-lbl">ожидает</span></div>
                  <div class="kpi"><span class="kpi-val kpi-ok">{{ anl.suggestions?.approved || 0 }}</span><span class="kpi-lbl">одобрено</span></div>
                </div>
              </div>

              <div class="analytics-panel">
                <div class="panel-title"><i class="pi pi-file-edit"></i> Задания по компаниям</div>
                <div v-if="(anl.test_assignments?.by_company || []).length === 0" class="empty-panel">Нет данных</div>
                <div v-else class="company-list">
                  <div v-for="c in (anl.test_assignments?.by_company || [])" :key="c.company" class="company-item">
                    <span>{{ c.company }}</span>
                    <Badge :value="c.count" severity="info" />
                  </div>
                </div>
              </div>
            </div>

            <!-- System Actions -->
            <div class="system-actions">
              <Button label="Обновить аналитику" icon="pi pi-refresh" severity="secondary" text @click="loadAnalytics" />
              <Button label="Пересчитать вероятности" icon="pi pi-refresh" @click="recalculateProbabilities" :loading="recalculating" />
              <Button label="Экспорт JSON" icon="pi pi-download" @click="exportJSON" severity="secondary" />
              <Button label="Экспорт CSV" icon="pi pi-file" @click="exportCSV" severity="secondary" />
            </div>
          </div>
        </TabPanel>
      </TabView>
    </div>
    
    <VideoUpload v-model:visible="showUploadDialog" @submitted="onVideoSubmitted" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useQuestionsStore, useTasksStore } from '../store'
import NavBar from '../components/NavBar.vue'
import VideoUpload from '../components/VideoUpload.vue'
import QuestionApproval from '../components/QuestionApproval.vue'
import SuggestionsManager from '../components/SuggestionsManager.vue'
import FeedbackManager from '../components/FeedbackManager.vue'
import api from '../api/client'

const questionsStore = useQuestionsStore()
const tasksStore = useTasksStore()

const showUploadDialog = ref(false)
const recalculating = ref(false)
const approvalComponent = ref(null)
const expandedLogs = ref({})
const suggestionsComponent = ref(null)
const feedbackComponent = ref(null)
const activeTab = ref(0)
const bulkGenerating = ref(false)

// Video management
const adminVideos = ref([])
const adminVideosLoading = ref(false)
const videoSearch = ref('')
const editingVideoId = ref(null)
const editingVideoTitle = ref('')

const filteredAdminVideos = computed(() => {
  if (!videoSearch.value) return adminVideos.value
  const s = videoSearch.value.toLowerCase()
  return adminVideos.value.filter(v => (v.title || '').toLowerCase().includes(s) || (v.youtube_url || '').toLowerCase().includes(s))
})

const loadAdminVideos = async () => {
  adminVideosLoading.value = true
  try {
    const r = await api.getProcessedVideos()
    adminVideos.value = r.data?.videos || r.data || []
  } catch (e) { console.error(e) }
  adminVideosLoading.value = false
}

const startEditVideo = (video) => {
  editingVideoId.value = video.id
  editingVideoTitle.value = video.title || ''
}

const saveVideoTitle = async (video) => {
  try {
    await api.updateVideo(video.id, { title: editingVideoTitle.value })
    video.title = editingVideoTitle.value
    editingVideoId.value = null
  } catch (e) { alert('Ошибка сохранения: ' + e.message) }
}

const openVideoUrl = (video) => {
  const url = video.youtube_url || video.url
  if (url) window.open(url, '_blank')
}

const deleteVideoConfirm = async (video) => {
  if (!confirm(`Удалить видео «${video.title || video.youtube_url}»? Связи с вопросами будут удалены.`)) return
  try {
    await api.deleteVideo(video.id)
    adminVideos.value = adminVideos.value.filter(v => v.id !== video.id)
  } catch (e) { alert('Ошибка удаления: ' + e.message) }
}

// ===== Test Assignments Management =====
const taList = ref([])
const taLoading = ref(false)
const taSearch = ref('')
const showTADialog = ref(false)
const editingTA = ref(null)
const taSaving = ref(false)
const taForm = ref({ title: '', description: '', company: '', profession: '', difficulty: 'middle', skills: '', link: '', source: '' })
const taDiffOptions = [{ label: 'Junior', value: 'junior' }, { label: 'Middle', value: 'middle' }, { label: 'Senior', value: 'senior' }]
const taDiffSeverity = (d) => ({ junior: 'success', middle: 'warning', senior: 'danger' }[d] || 'info')

const filteredTAList = computed(() => {
  if (!taSearch.value) return taList.value
  const s = taSearch.value.toLowerCase()
  return taList.value.filter(a => (a.title || '').toLowerCase().includes(s) || (a.company || '').toLowerCase().includes(s) || (a.profession || '').toLowerCase().includes(s))
})

const loadTAList = async () => {
  taLoading.value = true
  try {
    const r = await api.getTestAssignments({ per_page: 500 })
    taList.value = r.data.assignments || []
  } catch (e) { console.error(e) }
  taLoading.value = false
}

const openTADialog = (item) => {
  if (item) {
    editingTA.value = item
    taForm.value = { title: item.title || '', description: item.description || '', company: item.company || '', profession: item.profession || '', difficulty: item.difficulty || 'middle', skills: item.skills || '', link: item.link || '', source: item.source || '' }
  } else {
    editingTA.value = null
    taForm.value = { title: '', description: '', company: '', profession: '', difficulty: 'middle', skills: '', link: '', source: '' }
  }
  showTADialog.value = true
}

const saveTA = async () => {
  taSaving.value = true
  try {
    if (editingTA.value) {
      await api.updateTestAssignment(editingTA.value.id, taForm.value)
    } else {
      await api.createTestAssignment(taForm.value)
    }
    showTADialog.value = false
    await loadTAList()
  } catch (e) { alert('Ошибка: ' + (e.response?.data?.detail || e.message)) }
  taSaving.value = false
}

const deleteTAConfirm = async (item) => {
  if (!confirm(`Удалить задание «${item.title}»?`)) return
  try {
    await api.deleteTestAssignment(item.id)
    taList.value = taList.value.filter(a => a.id !== item.id)
  } catch (e) { alert('Ошибка: ' + e.message) }
}

// Task getters
const allTasks = computed(() => tasksStore.tasks)
const activeTasks = computed(() => tasksStore.activeTasks)
const hasActiveTasks = computed(() => tasksStore.hasActiveTasks)

// Stats
const totalQuestions = computed(() => questionsStore.questions.length)
const approvedCount = computed(() => questionsStore.approvedQuestions.length)
const unapprovedCount = computed(() => questionsStore.unapprovedQuestions.length)
const questionsWithAnswers = computed(() => questionsStore.questions.filter(q => q.answer).length)
const topicsCount = computed(() => questionsStore.topics.length)
const videosProcessed = computed(() => {
  const v = new Set(questionsStore.questions.map(q => q.video_url))
  return v.size
})

const topicDistribution = computed(() => {
  return questionsStore.topics.map(topic => {
    const qs = questionsStore.questions.filter(q => q.topic === topic)
    return {
      topic,
      count: qs.length,
      approved: qs.filter(q => q.is_approved || q.approved).length,
      with_answers: qs.filter(q => q.answer).length
    }
  }).sort((a, b) => b.count - a.count)
})

// Analytics
const anl = ref({})
const analyticsLoading = ref(false)
const diffSeverityMap = { junior: 'success', middle: 'warning', senior: 'danger', unknown: 'secondary' }

const loadAnalytics = async () => {
  analyticsLoading.value = true
  try {
    const r = await api.getAdminAnalytics()
    anl.value = r.data
  } catch (e) { console.error('Analytics error:', e) }
  analyticsLoading.value = false
}

const barHeight = (val, arr) => {
  if (!arr || !arr.length) return '0%'
  const max = Math.max(...arr.map(x => x.count || x.views || 0))
  return max ? Math.max((val / max) * 100, 4) + '%' : '4%'
}

const hBarWidth = (val, arr) => {
  if (!arr || !arr.length) return '0%'
  const max = Math.max(...arr.map(x => x.views || 0))
  return max ? Math.max((val / max) * 100, 3) + '%' : '3%'
}

const diffPercent = (count) => {
  const total = (anl.value.difficulty_distribution || []).reduce((s, d) => s + d.count, 0)
  return total ? Math.max((count / total) * 100, 2) : 0
}

// Helpers
const getStatusSeverity = (s) => ({
  pending: 'info', downloading: 'info', downloaded: 'info',
  transcribing: 'warning', transcribed: 'warning',
  extracting: 'warning', extracted: 'warning',
  saving: 'warning', completed: 'success', error: 'danger'
})[s] || 'info'

const getStatusIcon = (s) => ({
  pending: 'pi pi-clock', downloading: 'pi pi-download', downloaded: 'pi pi-check',
  transcribing: 'pi pi-spin pi-spinner', transcribed: 'pi pi-check',
  extracting: 'pi pi-spin pi-spinner', extracted: 'pi pi-check',
  saving: 'pi pi-spin pi-spinner', completed: 'pi pi-check-circle', error: 'pi pi-times-circle'
})[s] || 'pi pi-circle'

const getStatusLabel = (s) => ({
  pending: 'Ожидание', downloading: 'Скачивание', downloaded: 'Скачано',
  transcribing: 'Транскрибация', transcribed: 'Транскрибировано',
  extracting: 'Извлечение', extracted: 'Извлечено',
  saving: 'Сохранение', completed: 'Готово', error: 'Ошибка'
})[s] || s

const getStepIcon = (s) => {
  if (s === 'error') return 'pi pi-exclamation-triangle'
  if (s === 'completed') return 'pi pi-check'
  return 'pi pi-info-circle'
}

const truncateUrl = (url) => {
  if (!url) return '—'
  if (url.length > 60) return url.substring(0, 57) + '...'
  return url
}

const formatTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleString('ru-RU', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
}

const formatLogTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const toggleLogs = (taskId) => {
  expandedLogs.value[taskId] = !expandedLogs.value[taskId]
}

// Actions
const bulkGenerate = async () => {
  const toGenerate = questionsStore.approvedQuestions.filter(q => !q.answer)
  if (toGenerate.length === 0) {
    alert('Все утверждённые вопросы уже имеют ответы!')
    return
  }
  if (!confirm(`Сгенерировать ответы для ${toGenerate.length} вопросов? Это может занять некоторое время.`)) return
  bulkGenerating.value = true
  let success = 0, fail = 0
  for (const q of toGenerate) {
    try {
      await questionsStore.generateAnswer(q.id)
      success++
    } catch { fail++ }
  }
  bulkGenerating.value = false
  alert(`Готово! Успешно: ${success}, ошибки: ${fail}`)
  await questionsStore.fetchQuestions()
}

const onVideoSubmitted = async (taskId) => {
  // Task is already added to the store — just refresh UI
  if (approvalComponent.value) {
    setTimeout(() => approvalComponent.value.refresh?.(), 5000)
  }
}

const recalculateProbabilities = async () => {
  if (!confirm('Пересчитать вероятности?')) return
  recalculating.value = true
  try {
    await api.recalculateProbabilities()
    await questionsStore.fetchQuestions()
  } catch (e) {
    alert('Ошибка: ' + e.message)
  } finally {
    recalculating.value = false
  }
}

const exportJSON = async () => {
  try {
    const r = await api.getAdminQuestions()
    const blob = new Blob([JSON.stringify(r.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `questions-${Date.now()}.json`; a.click()
    URL.revokeObjectURL(url)
  } catch (e) { alert('Ошибка экспорта') }
}

const exportCSV = async () => {
  try {
    const r = await api.exportCSV()
    const blob = new Blob([r.data], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `questions-${Date.now()}.csv`; a.click()
    URL.revokeObjectURL(url)
  } catch (e) { alert('Ошибка экспорта CSV') }
}

onMounted(async () => {
  await Promise.all([
    questionsStore.fetchQuestions(),
    questionsStore.fetchAdminQuestions(),
    tasksStore.fetchAllTasks(),
    loadAdminVideos(),
    loadTAList(),
    loadAnalytics()
  ])
  tasksStore.startGlobalPolling()
  
  // Start polling for active tasks
  for (const t of tasksStore.activeTasks) {
    tasksStore.startPolling(t.task_id)
  }
})

onUnmounted(() => {
  tasksStore.stopGlobalPolling()
})
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #0f0f1e 0%, #1a1a2e 50%, #16213e 100%);
}

.admin-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.5rem 2rem 3rem;
}

/* Header */
.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.admin-header h1 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
  font-size: 1.8rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea, #f093fb);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  margin: 0.3rem 0 0;
  color: rgba(255,255,255,0.45);
  font-size: 0.9rem;
}

.upload-btn {
  font-weight: 600;
  padding: 0.7rem 1.5rem;
}

/* Tasks Section */
.tasks-section {
  margin-bottom: 2rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: rgba(255,255,255,0.85);
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.task-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 1rem 1.25rem;
  transition: border-color 0.3s;
}

.task-card.status-error {
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.04);
}

.task-card.status-completed {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.03);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.6rem;
}

.task-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.task-url {
  font-size: 0.85rem;
  color: rgba(255,255,255,0.55);
  font-family: 'Fira Code', monospace;
}

.task-time {
  font-size: 0.75rem;
  color: rgba(255,255,255,0.35);
}

.task-step {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: rgba(255,255,255,0.6);
}

.task-error {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  color: #f87171;
  font-size: 0.85rem;
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
}

.task-result {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 6px;
  color: #4ade80;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.error-bar :deep(.p-progressbar-value) {
  background: linear-gradient(135deg, #ef4444, #dc2626) !important;
}

/* Logs */
.task-logs-toggle {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: rgba(255,255,255,0.35);
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
}

.task-logs-toggle:hover {
  color: rgba(255,255,255,0.6);
}

.task-logs {
  margin-top: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
  background: rgba(0,0,0,0.3);
  border-radius: 6px;
  padding: 0.5rem;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 0.75rem;
}

.log-entry {
  display: flex;
  gap: 0.6rem;
  padding: 0.15rem 0;
  color: rgba(255,255,255,0.5);
}

.log-entry.log-error {
  color: #f87171;
}

.log-entry.log-completed {
  color: #4ade80;
}

.log-time {
  color: rgba(255,255,255,0.3);
  flex-shrink: 0;
}

/* Slide transition */
.slide-enter-active, .slide-leave-active {
  transition: all 0.25s ease;
}

.slide-enter-from, .slide-leave-to {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
}

/* Stats - see analytics dashboard below */

.mt-3 {
  margin-top: 1.5rem;
}

/* Admin tabs override */
.admin-tabs :deep(.p-tabview-panels) {
  background: transparent;
  padding: 1.5rem 0;
}

.admin-tabs :deep(.p-tabview-nav) {
  background: transparent;
  border-color: rgba(255,255,255,0.08);
}

.admin-tabs :deep(.p-tabview-nav li .p-tabview-nav-link) {
  padding: 0.85rem 1.5rem;
  font-weight: 600;
  font-size: 0.92rem;
  border-radius: 8px 8px 0 0;
  font-family: 'Inter', sans-serif;
}

/* Consistent fonts across all admin sub-components */
.admin-page :deep(h3),
.admin-page :deep(h4) {
  font-family: 'Inter', sans-serif;
  font-weight: 700;
}

.admin-page :deep(.p-datatable .p-datatable-thead > tr > th) {
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: rgba(255,255,255,0.6);
}

.admin-page :deep(.p-datatable .p-datatable-tbody > tr > td) {
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
}

.admin-page :deep(.p-card .p-card-title) {
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 1.1rem;
}

.admin-page :deep(.p-tag) {
  font-family: 'Inter', sans-serif;
  font-weight: 600;
}

.admin-page :deep(.p-button .p-button-label) {
  font-family: 'Inter', sans-serif;
  font-weight: 600;
}

.admin-page :deep(.p-dropdown .p-dropdown-label) {
  font-family: 'Inter', sans-serif;
}

.admin-page :deep(.p-inputtext) {
  font-family: 'Inter', sans-serif;
}

/* Fix Paginator dropdown alignment & spacing */
.admin-page :deep(.p-paginator) {
  font-family: 'Inter', sans-serif;
  background: transparent;
  border: none;
  padding: 0.75rem 0;
}

.admin-page :deep(.p-paginator .p-dropdown) {
  display: inline-flex;
  align-items: center;
  margin-left: 0.5rem;
}

.admin-page :deep(.p-paginator .p-dropdown .p-dropdown-label) {
  display: flex;
  align-items: center;
  padding: 0.35rem 0.5rem;
  min-width: 2.5rem;
  text-align: center;
}

.admin-page :deep(.p-paginator .p-dropdown .p-dropdown-trigger) {
  width: 2rem;
}

.admin-page :deep(.p-paginator .p-paginator-rpp-options) {
  margin-left: 0.5rem;
}

.tab-toolbar {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
}

.mr-2 { margin-right: 0.5rem; }

/* Video Manager */
.videos-manager { padding: 0.5rem 0; }
.vm-toolbar { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
.vm-search { min-width: 250px; }
.vm-count { color: rgba(255,255,255,0.45); font-size: 0.85rem; margin-left: auto; }
.vm-loading { display: flex; justify-content: center; padding: 2rem; }
.vm-empty { text-align: center; padding: 3rem; color: rgba(255,255,255,0.4); }
.vm-empty i { font-size: 2.5rem; display: block; margin-bottom: 0.5rem; }
.vm-title-cell { display: flex; align-items: center; gap: 0.25rem; }
.vm-edit-title { display: flex; align-items: center; gap: 0.25rem; }
.vm-actions { display: flex; gap: 0.25rem; }

/* Test Assignments Manager */
.ta-manager { padding: 0.5rem 0; }
.ta-toolbar { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
.ta-search { min-width: 250px; }
.ta-count { color: rgba(255,255,255,0.45); font-size: 0.85rem; margin-left: auto; }
.ta-loading { display: flex; justify-content: center; padding: 2rem; }
.ta-title-cell { font-weight: 500; }
.ta-actions { display: flex; gap: 0.25rem; }

/* TA Dialog Form */
.ta-form { display: flex; flex-direction: column; gap: 0.25rem; }
.ta-form-section {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 0.75rem;
}
.ta-section-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255,255,255,0.7);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.ta-section-title i { color: #60a5fa; font-size: 0.85rem; }
.ta-field { margin-bottom: 0.75rem; }
.ta-field:last-child { margin-bottom: 0; }
.ta-field label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.4rem;
  font-size: 0.85rem;
  color: rgba(255,255,255,0.6);
  font-weight: 500;
}
.ta-field label i { font-size: 0.8rem; color: rgba(255,255,255,0.35); }
.ta-hint { font-weight: 400; color: rgba(255,255,255,0.35); font-size: 0.8rem; }
.ta-field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.ta-skills-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(255,255,255,0.02);
  border-radius: 8px;
  border: 1px dashed rgba(255,255,255,0.08);
}
.ta-skill-chip { font-size: 0.75rem; }
.ta-dialog-footer { display: flex; justify-content: flex-end; gap: 0.5rem; }

/* ====== Analytics Dashboard ====== */
.analytics-loading { display: flex; flex-direction: column; align-items: center; padding: 3rem; gap: 1rem; color: rgba(255,255,255,0.5); }
.analytics-dashboard { display: flex; flex-direction: column; gap: 1.5rem; }

.analytics-section { margin-bottom: 0.5rem; }
.section-header {
  font-size: 1.1rem; font-weight: 600; color: rgba(255,255,255,0.8);
  display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;
}
.section-header i { color: #60a5fa; }

/* Metric Cards */
.metrics-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
.metric-card {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px; padding: 1.25rem; position: relative; overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.3); }
.metric-card i { font-size: 1.8rem; margin-bottom: 0.75rem; display: block; }
.metric-value { font-size: 2rem; font-weight: 700; color: white; line-height: 1; }
.metric-label { font-size: 0.85rem; color: rgba(255,255,255,0.5); margin-top: 0.25rem; }
.metric-sub { font-size: 0.75rem; color: rgba(255,255,255,0.35); margin-top: 0.15rem; }
.metric-purple i { color: #a78bfa; }
.metric-purple { border-left: 3px solid #a78bfa; }
.metric-blue i { color: #60a5fa; }
.metric-blue { border-left: 3px solid #60a5fa; }
.metric-green i { color: #34d399; }
.metric-green { border-left: 3px solid #34d399; }
.metric-orange i { color: #fb923c; }
.metric-orange { border-left: 3px solid #fb923c; }
.metric-pink i { color: #f472b6; }
.metric-pink { border-left: 3px solid #f472b6; }
.metric-teal i { color: #2dd4bf; }
.metric-teal { border-left: 3px solid #2dd4bf; }

/* Panel Layout */
.analytics-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }
.analytics-row.triple { grid-template-columns: 1fr 1fr 1fr; }
.analytics-panel {
  background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px; padding: 1.25rem;
}
.analytics-panel.wide-panel { grid-column: span 1; }
.panel-title {
  font-size: 0.95rem; font-weight: 600; color: rgba(255,255,255,0.75);
  display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;
  padding-bottom: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.06);
}
.panel-title i { color: #60a5fa; font-size: 0.9rem; }
.empty-panel { color: rgba(255,255,255,0.3); text-align: center; padding: 2rem; font-size: 0.9rem; }

/* User Stats */
.user-stats-grid { display: flex; gap: 1.5rem; margin-bottom: 1rem; }
.mini-stat { display: flex; flex-direction: column; align-items: center; }
.mini-val { font-size: 1.5rem; font-weight: 700; color: white; }
.mini-lbl { font-size: 0.75rem; color: rgba(255,255,255,0.4); }

/* Bar Charts */
.chart-bar-title { font-size: 0.8rem; color: rgba(255,255,255,0.4); margin-bottom: 0.5rem; }
.bar-chart { display: flex; align-items: flex-end; gap: 3px; height: 80px; }
.bar-chart.tall-chart { height: 120px; }
.bar-item { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }
.bar-fill {
  width: 100%; min-width: 8px; border-radius: 3px 3px 0 0;
  background: linear-gradient(180deg, #a78bfa, #6d28d9); transition: height 0.3s;
}
.bar-fill.bar-blue { background: linear-gradient(180deg, #60a5fa, #2563eb); }
.bar-label { font-size: 0.6rem; color: rgba(255,255,255,0.3); margin-top: 2px; }

/* Horizontal Bars */
.horizontal-bars { display: flex; flex-direction: column; gap: 0.5rem; }
.horizontal-bars.compact { gap: 0.35rem; }
.h-bar-row { display: grid; grid-template-columns: 120px 1fr 50px; gap: 0.5rem; align-items: center; }
.h-bar-label { font-size: 0.8rem; color: rgba(255,255,255,0.7); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.h-bar-track { height: 18px; background: rgba(255,255,255,0.04); border-radius: 9px; overflow: hidden; }
.h-bar-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 9px; transition: width 0.5s; }
.h-bar-fill.hh-fill { background: linear-gradient(90deg, #f59e0b, #d97706); }
.h-bar-value { font-size: 0.8rem; color: rgba(255,255,255,0.5); text-align: right; }

/* Donut/Difficulty Stats */
.donut-stats { display: flex; flex-direction: column; gap: 0.75rem; }
.donut-item { display: grid; grid-template-columns: 80px 50px 1fr; gap: 0.5rem; align-items: center; }
.donut-count { font-size: 0.9rem; font-weight: 600; color: rgba(255,255,255,0.7); text-align: center; }
.donut-bar { height: 14px; background: rgba(255,255,255,0.04); border-radius: 7px; overflow: hidden; }
.donut-bar-fill { height: 100%; border-radius: 7px; transition: width 0.5s; }
.diff-junior { background: linear-gradient(90deg, #22c55e, #16a34a); }
.diff-middle { background: linear-gradient(90deg, #f59e0b, #d97706); }
.diff-senior { background: linear-gradient(90deg, #ef4444, #dc2626); }
.diff-unknown { background: rgba(255,255,255,0.15); }

/* Top Lists */
.top-list { display: flex; flex-direction: column; gap: 0.5rem; max-height: 350px; overflow-y: auto; }
.top-item {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.5rem 0.65rem; background: rgba(255,255,255,0.02);
  border-radius: 8px; border: 1px solid rgba(255,255,255,0.04);
}
.top-rank { font-size: 0.8rem; font-weight: 700; color: rgba(255,255,255,0.3); min-width: 24px; }
.top-info { flex: 1; min-width: 0; }
.top-text { font-size: 0.82rem; color: rgba(255,255,255,0.7); overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 0.2rem; }

/* KPI */
.kpi-row { display: flex; gap: 1.5rem; margin-bottom: 1rem; }
.kpi { display: flex; flex-direction: column; align-items: center; }
.kpi-val { font-size: 1.5rem; font-weight: 700; color: white; }
.kpi-val.kpi-warn { color: #fb923c; }
.kpi-val.kpi-ok { color: #34d399; }
.kpi-lbl { font-size: 0.75rem; color: rgba(255,255,255,0.4); }

/* Feedback Types */
.fb-types { display: flex; flex-direction: column; gap: 0.35rem; }
.fb-type-item { display: flex; justify-content: space-between; align-items: center; font-size: 0.82rem; color: rgba(255,255,255,0.6); padding: 0.25rem 0; }

/* Company List */
.company-list { display: flex; flex-direction: column; gap: 0.35rem; }
.company-item { display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; color: rgba(255,255,255,0.6); padding: 0.25rem 0; }

/* Analytics Table */
.analytics-table { font-size: 0.85rem; }

/* System Actions */
.system-actions {
  display: flex; gap: 0.75rem; flex-wrap: wrap;
  padding: 1rem; background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06); border-radius: 12px;
}

@media (max-width: 1024px) {
  .analytics-row { grid-template-columns: 1fr; }
  .analytics-row.triple { grid-template-columns: 1fr; }
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .metrics-grid { grid-template-columns: 1fr; }
  .h-bar-row { grid-template-columns: 80px 1fr 40px; }
}
</style>
