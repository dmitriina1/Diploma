import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import QuestionDetail from '../views/QuestionDetail.vue'
import Admin from '../views/Admin.vue'
import Suggestions from '../views/Suggestions.vue'
import Trainer from '../views/Trainer.vue'
import InterviewRecordings from '../views/InterviewRecordings.vue'
import InterviewQuestions from '../views/InterviewQuestions.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { title: 'Interview Prep - Подготовка к IT собеседованиям' }
  },
  {
    path: '/question/:id',
    name: 'QuestionDetail',
    component: QuestionDetail,
    props: true,
    meta: { title: 'Вопрос' }
  },
  {
    path: '/suggest',
    name: 'Suggestions',
    component: Suggestions,
    meta: { title: 'Предложить видео' }
  },
  {
    path: '/trainer',
    name: 'Trainer',
    component: Trainer,
    meta: { title: 'Тренажёр' }
  },
  {
    path: '/recordings',
    name: 'InterviewRecordings',
    component: InterviewRecordings,
    meta: { title: 'Записи собеседований' }
  },
  {
    path: '/interview-questions',
    name: 'InterviewQuestions',
    component: InterviewQuestions,
    meta: { title: 'Вопросы с собеседований' }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { title: 'Админ-панель', requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'Interview Prep'
  next()
})

export default router
