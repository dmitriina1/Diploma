<template>
  <Dialog :visible="visible" @update:visible="$emit('update:visible', $event)" 
          header="Обратная связь" :modal="true" :style="{ width: '500px' }">
    <div class="feedback-form">
      <div class="field">
        <label>Тип обратной связи</label>
        <Dropdown v-model="form.feedback_type" :options="typeOptions" optionLabel="label" optionValue="value" class="w-full" />
      </div>
      
      <div class="field" v-if="form.feedback_type === 'answer_quality'">
        <label>Оценка ответа</label>
        <Rating v-model="form.rating" :cancel="false" />
      </div>
      
      <div class="field">
        <label>Комментарий</label>
        <Textarea v-model="form.comment" rows="4" :placeholder="getPlaceholder()" class="w-full" />
      </div>
      
      <div class="field">
        <label>Ваше имя (необязательно)</label>
        <InputText v-model="form.user_name" placeholder="Имя" class="w-full" />
      </div>
    </div>
    
    <template #footer>
      <Button label="Отмена" severity="secondary" @click="$emit('update:visible', false)" />
      <Button label="Отправить" icon="pi pi-send" @click="submit" :loading="submitting" />
    </template>
  </Dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '../api/client'
import { useToast } from 'primevue/usetoast'

const props = defineProps({
  visible: Boolean,
  questionId: Number
})
const emit = defineEmits(['update:visible'])
const toast = useToast()
const submitting = ref(false)

const form = ref({
  feedback_type: 'suggestion',
  rating: null,
  comment: '',
  user_name: ''
})

const typeOptions = [
  { label: '💡 Предложение', value: 'suggestion' },
  { label: '👍 Нравится', value: 'like' },
  { label: '👎 Не нравится', value: 'dislike' },
  { label: '⭐ Оценка ответа', value: 'answer_quality' },
  { label: '🚩 Жалоба/ошибка', value: 'report' }
]

const getPlaceholder = () => {
  const placeholders = {
    suggestion: 'Что можно улучшить?',
    like: 'Что понравилось?',
    dislike: 'Что не понравилось?',
    answer_quality: 'Комментарий к ответу...',
    report: 'Опишите проблему...'
  }
  return placeholders[form.value.feedback_type] || 'Ваш комментарий...'
}

const userSession = localStorage.getItem('user_session') || 'anonymous'

const submit = async () => {
  submitting.value = true
  try {
    await api.createFeedback({
      ...form.value,
      question_id: props.questionId,
      user_session: userSession
    })
    toast.add({ severity: 'success', summary: 'Спасибо!', detail: 'Ваша обратная связь отправлена', life: 4000 })
    emit('update:visible', false)
    form.value = { feedback_type: 'suggestion', rating: null, comment: '', user_name: '' }
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Не удалось отправить', life: 4000 })
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.feedback-form { display: flex; flex-direction: column; gap: 1rem; }
.field label { display: block; margin-bottom: 0.4rem; font-weight: 600; font-size: 0.9rem; }
</style>
