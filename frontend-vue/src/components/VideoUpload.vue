<template>
  <Dialog :visible="visible" 
          @update:visible="$emit('update:visible', $event)"
          header="Загрузить видео для обработки" 
          :modal="true" 
          :closable="!submitting"
          :style="{ width: '600px' }">
    <div class="upload-form">
      <div class="upload-mode-toggle">
        <Button :label="'По ссылке'" :icon="'pi pi-link'" size="small"
                :severity="uploadMode === 'url' ? undefined : 'secondary'"
                :outlined="uploadMode !== 'url'"
                @click="uploadMode = 'url'" />
        <Button :label="'Загрузить файл'" :icon="'pi pi-upload'" size="small"
                :severity="uploadMode === 'file' ? undefined : 'secondary'"
                :outlined="uploadMode !== 'file'"
                @click="uploadMode = 'file'" />
      </div>

      <!-- URL mode -->
      <div v-if="uploadMode === 'url'" class="form-field">
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
        
        <div v-if="detectedPlatform" class="platform-badge">
          <i class="pi pi-check-circle"></i>
          {{ detectedPlatform }}
        </div>
      </div>

      <!-- File upload mode -->
      <div v-if="uploadMode === 'file'" class="form-field">
        <label>Видеофайл или аудиофайл</label>
        <div class="file-upload-area" 
             :class="{ 'drag-over': isDragOver, 'has-file': selectedFile }"
             @dragover.prevent="isDragOver = true"
             @dragleave="isDragOver = false"
             @drop.prevent="onDrop">
          <template v-if="!selectedFile">
            <i class="pi pi-cloud-upload upload-icon"></i>
            <p>Перетащите файл сюда или</p>
            <Button label="Выберите файл" icon="pi pi-folder-open" size="small" outlined
                    @click="$refs.fileInput.click()" />
            <small class="help-text">MP4, MKV, AVI, MP3, WAV — до 2 ГБ</small>
          </template>
          <template v-else>
            <div class="selected-file">
              <i class="pi pi-file-edit"></i>
              <div class="file-info">
                <span class="file-name">{{ selectedFile.name }}</span>
                <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
              </div>
              <Button icon="pi pi-times" text severity="danger" size="small" @click="selectedFile = null" />
            </div>
          </template>
        </div>
        <input ref="fileInput" type="file" accept="video/*,audio/*,.mp4,.mkv,.avi,.mp3,.wav,.webm"
               style="display: none" @change="onFileSelect" />
      </div>
      
      <Message v-if="error" severity="error" :closable="true" @close="error = null">
        {{ error }}
      </Message>

      <ProgressBar v-if="uploadProgress > 0 && uploadProgress < 100" :value="uploadProgress" :showValue="true" />
    </div>
    
    <template #footer>
      <Button label="Отмена" icon="pi pi-times" @click="close" text :disabled="submitting" />
      <Button v-if="uploadMode === 'url'"
              label="Отправить на обработку" icon="pi pi-send" 
              @click="submitVideo" :disabled="!videoUrl.trim() || submitting" :loading="submitting" />
      <Button v-else
              label="Загрузить и обработать" icon="pi pi-upload" 
              @click="uploadFile" :disabled="!selectedFile || submitting" :loading="submitting" />
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useTasksStore } from '../store'
import api from '../api/client'

const props = defineProps({
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['update:visible', 'submitted'])

const tasksStore = useTasksStore()

const uploadMode = ref('url')
const videoUrl = ref('')
const submitting = ref(false)
const error = ref(null)
const selectedFile = ref(null)
const isDragOver = ref(false)
const uploadProgress = ref(0)

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

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' КБ'
  if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' МБ'
  return (bytes / 1073741824).toFixed(2) + ' ГБ'
}

const onFileSelect = (e) => {
  const file = e.target.files?.[0]
  if (file) selectedFile.value = file
}

const onDrop = (e) => {
  isDragOver.value = false
  const file = e.dataTransfer.files?.[0]
  if (file) selectedFile.value = file
}

const submitVideo = async () => {
  if (!videoUrl.value.trim() || submitting.value) return
  submitting.value = true
  error.value = null
  try {
    const taskId = await tasksStore.processVideo(videoUrl.value.trim())
    emit('submitted', taskId)
    close()
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Не удалось отправить видео на обработку'
  } finally {
    submitting.value = false
  }
}

const uploadFile = async () => {
  if (!selectedFile.value || submitting.value) return
  submitting.value = true
  error.value = null
  uploadProgress.value = 0
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    const response = await api.uploadVideoFile(formData, {
      onUploadProgress: (e) => {
        uploadProgress.value = Math.round((e.loaded * 100) / e.total)
      }
    })
    
    const taskId = response.data?.task_id
    if (taskId) {
      tasksStore.startPolling(taskId)
    }
    emit('submitted', taskId)
    close()
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Не удалось загрузить файл'
  } finally {
    submitting.value = false
    uploadProgress.value = 0
  }
}

const close = () => {
  videoUrl.value = ''
  error.value = null
  submitting.value = false
  selectedFile.value = null
  uploadProgress.value = 0
  emit('update:visible', false)
}

watch(() => props.visible, (val) => {
  if (val) {
    videoUrl.value = ''
    error.value = null
    submitting.value = false
    selectedFile.value = null
    uploadProgress.value = 0
  }
})
</script>

<style scoped>
.upload-form { display: flex; flex-direction: column; gap: 1rem; }
.upload-mode-toggle { display: flex; gap: 0.5rem; }
.form-field { display: flex; flex-direction: column; gap: 0.5rem; }
.form-field label { font-weight: 600; font-size: 0.95rem; }
.help-text { color: var(--text-color-secondary); font-size: 0.8rem; }
.w-full { width: 100%; }

.platform-badge {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.4rem 0.8rem; background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 6px;
  color: rgb(34, 197, 94); font-size: 0.85rem; font-weight: 600; width: fit-content;
}

.file-upload-area {
  border: 2px dashed rgba(255,255,255,0.12); border-radius: 12px;
  padding: 2rem; text-align: center; transition: all 0.2s; cursor: pointer;
  background: rgba(255,255,255,0.02);
}
.file-upload-area:hover, .file-upload-area.drag-over {
  border-color: #667eea; background: rgba(102,126,234,0.05);
}
.file-upload-area.has-file { border-style: solid; border-color: rgba(34,197,94,0.3); }
.upload-icon { font-size: 2.5rem; color: rgba(255,255,255,0.3); margin-bottom: 0.5rem; display: block; }
.file-upload-area p { color: rgba(255,255,255,0.5); margin: 0.5rem 0; }

.selected-file {
  display: flex; align-items: center; gap: 0.75rem;
}
.selected-file > i { font-size: 1.5rem; color: #667eea; }
.file-info { flex: 1; text-align: left; }
.file-name { display: block; font-weight: 600; color: rgba(255,255,255,0.85); font-size: 0.9rem; }
.file-size { display: block; color: rgba(255,255,255,0.4); font-size: 0.8rem; }
</style>
