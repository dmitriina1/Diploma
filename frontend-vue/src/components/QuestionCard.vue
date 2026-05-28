<template>
  <Card class="question-card">
    <template #header>
      <div class="card-header">
        <div class="tags">
          <Tag :value="question.topic" severity="info" />
          <Tag :value="difficultyLabel" :severity="difficultySeverity" />
          <Tag :value="`${(question.probability || 0).toFixed(0)}%`" 
               :severity="probabilitySeverity" icon="pi pi-chart-line" 
               v-tooltip.top="'Вероятность на собеседовании'" />
        </div>
      </div>
    </template>
    
    <template #title>
      {{ question.question }}
    </template>
    
    <template #content>
      <div v-if="question.answer" class="answer">
        <strong>Ответ:</strong>
        <p>{{ truncatedAnswer }}</p>
        <Button v-if="question.answer.length > 200" 
                label="Читать полностью" 
                link 
                @click="$emit('view-details', question.id)" />
      </div>
      
      <div v-if="question.timecode" class="timecode">
        <i class="pi pi-clock"></i>
        <span>{{ question.timecode }}</span>
      </div>
    </template>
    
    <template #footer>
      <div class="card-actions">
        <Button label="Подробнее" 
                icon="pi pi-arrow-right" 
                @click="$emit('view-details', question.id)" 
                text />
      </div>
    </template>
  </Card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  question: {
    type: Object,
    required: true
  }
})

defineEmits(['view-details'])

const difficultyLabel = computed(() => {
  const labels = {
    junior: 'Junior',
    middle: 'Middle',
    senior: 'Senior'
  }
  return labels[props.question.difficulty] || props.question.difficulty
})

const difficultySeverity = computed(() => {
  const severities = {
    junior: 'success',
    middle: 'warning',
    senior: 'danger'
  }
  return severities[props.question.difficulty] || 'info'
})

const probabilitySeverity = computed(() => {
  const prob = props.question.probability || 0
  if (prob >= 80) return 'danger'
  if (prob >= 50) return 'warning'
  return 'success'
})

const truncatedAnswer = computed(() => {
  if (!props.question.answer) return ''
  if (props.question.answer.length <= 200) return props.question.answer
  return props.question.answer.substring(0, 200) + '...'
})
</script>

<style scoped>
.question-card {
  margin-bottom: 1.5rem;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.question-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #667eea, #764ba2, transparent);
  transition: left 0.6s;
}

.question-card:hover::before {
  left: 100%;
}

.question-card:hover {
  transform: translateY(-6px) scale(1.01);
  box-shadow: 0 16px 40px rgba(102, 126, 234, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.15);
  border-color: rgba(102, 126, 234, 0.3);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.05) 100%);
}

.card-header {
  padding: 1.2rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.tags {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.answer {
  margin-top: 1.2rem;
  padding: 1.2rem;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.05) 100%);
  border-radius: 10px;
  border: 1px solid rgba(102, 126, 234, 0.15);
  transition: all 0.3s ease;
}

.question-card:hover .answer {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.12) 0%, rgba(118, 75, 162, 0.08) 100%);
  border-color: rgba(102, 126, 234, 0.25);
}

.answer strong {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.answer p {
  margin: 0.8rem 0 0 0;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.9);
}

.timecode {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-top: 1rem;
  color: var(--text-color-secondary);
  font-size: 0.95rem;
  padding: 0.5rem 0.8rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
  width: fit-content;
  transition: all 0.3s ease;
}

.timecode i {
  color: #667eea;
}

.question-card:hover .timecode {
  background: rgba(102, 126, 234, 0.1);
  color: rgba(255, 255, 255, 0.95);
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 0.5rem;
}
</style>
