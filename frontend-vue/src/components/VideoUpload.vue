<template>
  <Dialog :visible="visible" 
          @update:visible="$emit('update:visible', $event)"
          header="Загрузить видео" 
          :modal="true" 
          :closable="true"
          :style="{ width: '600px' }">
    <div class="upload-form">
      <div class="form-field">
        <label for="video-url">URL видео:</label>
        <InputText id="video-url" 
                   v-model="videoUrl" 
                   placeholder="https://www.youtube.com/watch?v=..." 
                   class="w-full"
                   :disabled="processing" />
        <small class="help-text">
          Поддерживаются: YouTube, VK.video, Rutube, OK.ru, Dailymotion, Vimeo
        </small>
      </div>
      
      <div v-if="detectedPlatform" class="platform-info">
        <i class="pi pi-check-circle"></i>
        <span>Обнаружена платформа: <strong>{{ detectedPlatform }}</strong></span>
      </div>
      
      <div v-if="processing" class="progress-section">
        <ProgressBar :value="progress" :showValue="true" />
        <p class="progress-text">{{ statusText }}</p>
        
        <div v-if="taskId" class="task-info">
          <small>Task ID: {{ taskId }}</small>
        </div>
      </div>
      
      <Message v-if="error" severity="error" :closable="false">
        {{ error }}
      </Message>
      
      <Message v-if="success" severity="success" :closable="false">
        Видео успешно обработано! Найдено {{ questionsCount }} вопросов.
      </Message>
    </div>
    
    <template #footer>
      <Button label="Отмена" 
              icon="pi pi-times" 
              @click="close" 
              text 
              :disabled="processing" />
      <Button label="Загрузить" 
              icon="pi pi-upload" 
              @click="uploadVideo" 
              :disabled="!videoUrl || processing" 
              :loading="processing" />
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useTasksStore } from '../store'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'success'])

const tasksStore = useTasksStore()

const videoUrl = ref('')
const processing = ref(false)
const error = ref(null)
const success = ref(false)
const taskId = ref(null)
const progress = ref(0)
const statusText = ref('')
const questionsCount = ref(0)

const detectedPlatform = computed(() => {
  if (!videoUrl.value) return null
  
  const url = videoUrl.value.toLowerCase()
  if (url.includes('youtube.com') || url.includes('youtu.be')) return 'YouTube'
  if (url.includes('vk.com') || url.includes('vk.video')) return 'VK.video'
  if (url.includes('rutube.ru')) return 'Rutube'
  if (url.includes('ok.ru')) return 'OK.ru'
  if (url.includes('dailymotion.com')) return 'Dailymotion'
  if (url.includes('vimeo.com')) return 'Vimeo'
  
  return null
})

const uploadVideo = async () => {
  if (!videoUrl.value) return
  
  processing.value = true
  error.value = null
  success.value = false
  progress.value = 0
  statusText.value = 'Начинается обработка...'
  
  try {
    const result = await tasksStore.processVideo(videoUrl.value)
    taskId.value = result.task_id
    
    // Poll task status
    const pollInterval = setInterval(async () => {
      const task = tasksStore.tasks.find(t => t.task_id === taskId.value)
      
      if (task) {
        statusText.value = task.status_message || task.status
        
        // Simulate progress based on status
        if (task.status === 'downloading') progress.value = 20
        else if (task.status === 'transcribing') progress.value = 50
        else if (task.status === 'processing') progress.value = 80
        else if (task.status === 'completed') {
          progress.value = 100
          questionsCount.value = task.questions_count || 0
          success.value = true
          processing.value = false
          clearInterval(pollInterval)
          
          emit('success')
          
          // Auto-close after 3 seconds
          setTimeout(() => {
            close()
          }, 3000)
        } else if (task.status === 'failed') {
          error.value = task.error || 'Произошла ошибка при обработке видео'
          processing.value = false
          clearInterval(pollInterval)
        }
      }
    }, 2000)
    
    // Timeout after 30 minutes
    setTimeout(() => {
      clearInterval(pollInterval)
      if (processing.value) {
        error.value = 'Превышено время ожидания обработки'
        processing.value = false
      }
    }, 30 * 60 * 1000)
    
  } catch (err) {
    error.value = err.response?.data?.detail || 'Не удалось загрузить видео'
    processing.value = false
  }
}

const close = () => {
  if (!processing.value) {
    videoUrl.value = ''
    error.value = null
    success.value = false
    progress.value = 0
    taskId.value = null
    emit('update:visible', false)
  }
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    // Reset state when dialog opens
    videoUrl.value = ''
    error.value = null
    success.value = false
    processing.value = false
    progress.value = 0
    taskId.value = null
  }
})
</script>

<style scoped>
.upload-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-field label {
  font-weight: 600;
}

.help-text {
  color: var(--text-color-secondary);
  font-size: 0.85rem;
}

.platform-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 6px;
  color: rgb(34, 197, 94);
}

.progress-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.progress-text {
  text-align: center;
  font-size: 0.9rem;
  color: var(--text-color-secondary);
}

.task-info {
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-color-secondary);
}

.w-full {
  width: 100%;
}
</style>
