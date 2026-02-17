<template>
  <div class="home">
    <NavBar />
    
    <section class="hero">
      <div class="hero-content">
        <h1 class="hero-title">
          <i class="pi pi-bookmark"></i>
          Подготовка к собеседованию
        </h1>
        <p class="hero-subtitle">
          Реальные вопросы с собеседований из видео на YouTube, VK.video, Rutube и других платформах
        </p>
        <div class="hero-stats">
          <div class="stat-item">
            <i class="pi pi-question-circle"></i>
            <div class="stat-content">
              <div class="stat-value">{{ totalQuestions }}</div>
              <div class="stat-label">Вопросов</div>
            </div>
          </div>
          <div class="stat-item">
            <i class="pi pi-bookmark"></i>
            <div class="stat-content">
              <div class="stat-value">{{ topicsCount }}</div>
              <div class="stat-label">Технологий</div>
            </div>
          </div>
          <div class="stat-item">
            <i class="pi pi-video"></i>
            <div class="stat-content">
              <div class="stat-value">{{ videosCount }}</div>
              <div class="stat-label">Видео</div>
            </div>
          </div>
        </div>
      </div>
    </section>
    
    <section class="content">
      <TechSelector />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useQuestionsStore } from '../store'
import NavBar from '../components/NavBar.vue'
import TechSelector from '../components/TechSelector.vue'

const questionsStore = useQuestionsStore()

const totalQuestions = computed(() => questionsStore.questions.length)
const topicsCount = computed(() => questionsStore.topics.length)
const videosCount = computed(() => {
  const uniqueVideos = new Set(questionsStore.questions.map(q => q.video_url))
  return uniqueVideos.size
})

onMounted(async () => {
  await questionsStore.fetchQuestions()
})
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: radial-gradient(ellipse at top, #1e1e3f 0%, #0f0f1e 50%, #000000 100%);
  position: relative;
  overflow: hidden;
}

.home::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 600px;
  background: radial-gradient(circle at 50% 0%, rgba(102, 126, 234, 0.15) 0%, transparent 70%);
  pointer-events: none;
}

.hero {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-size: 200% 200%;
  animation: gradient-shift 15s ease infinite;
  padding: 5rem 2rem;
  text-align: center;
  box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: float 20s linear infinite;
  opacity: 0.3;
}

.hero-content {
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: 4rem;
  font-weight: 900;
  color: white;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  animation: slide-up 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.hero-title i {
  animation: float 3s ease-in-out infinite;
}

.hero-subtitle {
  font-size: 1.4rem;
  color: rgba(255, 255, 255, 0.95);
  margin-bottom: 3.5rem;
  line-height: 1.8;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  animation: slide-up 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.2s both;
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
  animation: slide-up 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.4s both;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  background: rgba(255, 255, 255, 0.15);
  padding: 1.8rem 2.5rem;
  border-radius: 16px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.stat-item:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-8px) scale(1.05);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  border-color: rgba(255, 255, 255, 0.4);
}

.stat-item i {
  font-size: 3rem;
  color: white;
  transition: transform 0.4s ease;
}

.stat-item:hover i {
  transform: scale(1.2) rotate(10deg);
}

.stat-content {
  text-align: left;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 800;
  color: white;
  line-height: 1;
  margin-bottom: 0.3rem;
}

.stat-label {
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.content {
  padding: 4rem 0;
  position: relative;
  z-index: 1;
}
</style>
