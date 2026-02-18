<template>
  <Dialog :visible="visible" 
          @update:visible="$emit('update:visible', $event)"
          header="Загрузить видео для обработки" 
          :modal="true" 
          :closable="!submitting"
          :style="{ width: '550px' }">
    <div class="upload-form">
      <div class="form-field">
        <label for="video-url">URL видео</label>
        <InputText id="video-url" 
                   v-model="videoUrl" 
                   placeholder="https://www.youtube.com/watch?v=..." 
                   class="w-full"
                   :disabled="submitting"
                   @keyup.enter="submitVideo" />
        <small class="help-text">
          YouTube, VK.video, Rutube, OK.ru, Vimeo, Dailymotion
        </small>
      </div>
      
      <div v-if="detectedPlatform" class="platform-badge">
        <i class="pi pi-check-circle"></i>
        {{ detectedPlatform }}
      </div>
      
      <Message v-if="error" severity="error" :closable="true" @close="error = null">
        {{ error }}
      </Message>
    </div>
    
    <template #footer>
      <Button label="Отмена" 
              icon="pi pi-times" 
              @click="close" 
              text 
              :disabled="submitting" />
      <Button label="Отправить на обработку" 
              icon="pi pi-send" 
              @click="submitVideo" 
              :disabled="!videoUrl.trim() || submitting" 
              :loading="submitting" />
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useTasksStore } from '../store'

const props = defineProps({
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['update:visible', 'submitted'])

const tasksStore = useTasksStore()

const videoUrl = ref('')
const submitting = ref(false)
const error = ref(null)

const detectedPlatform = computed(() => {
  if (!videoUrl.value) return null
  const url = videoUrl.value.toLowerCase()
  if (url.includes('youtube.com') || url.includes('youtu.be')) return 'YouTube'
  if (url.includes('vk.com') || url.includes('vkvideo.ru') || url.includes('vk.video')) return 'VK Video'
  if (url.includes('rutube.ru')) return 'Rutube'
  if (url.includes('ok.ru')) return 'OK.ru'
  if (url.includes('dailymotion.com')) return 'Dailymotion'
  if (url.includes('vimeo.com')) return 'Vimeo'
  return null
})

const submitVideo = async () => {
  if (!videoUrl.value.trim() || submitting.value) return
  
  submitting.value = true
  error.value = null
  
  try {
    const taskId = await tasksStore.processVideo(videoUrl.value.trim())
    
    // Закрываем модал СРАЗУ после успешной отправки
    emit('submitted', taskId)
    close()
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Не удалось отправить видео на обработку'
  } finally {
    submitting.value = false
  }
}

const close = () => {
  videoUrl.value = ''
  error.value = null
  submitting.value = false
  emit('update:visible', false)
}

watch(() => props.visible, (val) => {
  if (val) {
    videoUrl.value = ''
    error.value = null
    submitting.value = false
  }
})
</script>

<style scoped>
.upload-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-field label {
  font-weight: 600;
  font-size: 0.95rem;
}

.help-text {
  color: var(--text-color-secondary);
  font-size: 0.8rem;
}

.platform-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.8rem;
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 6px;
  color: rgb(34, 197, 94);
  font-size: 0.85rem;
  font-weight: 600;
  width: fit-content;
}

.w-full {
  width: 100%;
}
</style>
