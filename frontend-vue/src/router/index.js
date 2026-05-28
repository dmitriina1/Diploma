import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import QuestionDetail from '../views/QuestionDetail.vue'
import Admin from '../views/Admin.vue'
import Suggestions from '../views/Suggestions.vue'
import Trainer from '../views/Trainer.vue'
import InterviewRecordings from '../views/InterviewRecordings.vue'
import InterviewQuestions from '../views/InterviewQuestions.vue'
import TestAssignments from '../views/TestAssignments.vue'
import TestAssignmentDetail from '../views/TestAssignmentDetail.vue'
import HHRequirements from '../views/HHRequirements.vue'
import Login from '../views/Login.vue'
import Profile from '../views/Profile.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { title: 'Interview Prep - Подготовка к IT собеседованиям' }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { title: 'Вход / Регистрация', guest: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: { title: 'Профиль', requiresAuth: true }
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
    meta: { title: 'Тренажёр SM-2', requiresAuth: true }
  },
  {
    path: '/recordings',
    name: 'InterviewRecordings',
    component: InterviewRecordings,
    meta: { title: 'Записи собеседований', requiresAuth: true }
  },
  {
    path: '/interview-questions',
    name: 'InterviewQuestions',
    component: InterviewQuestions,
    meta: { title: 'Вопросы с собеседований' }
  },
  {
    path: '/test-assignments',
    name: 'TestAssignments',
    component: TestAssignments,
    meta: { title: 'Тестовые задания', requiresAuth: true }
  },
  {
    path: '/test-assignments/:id',
    name: 'TestAssignmentDetail',
    component: TestAssignmentDetail,
    props: true,
    meta: { title: 'Тестовое задание', requiresAuth: true }
  },
  {
    path: '/hh-requirements',
    name: 'HHRequirements',
    component: HHRequirements,
    meta: { title: 'Навыки из вакансий' }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { title: 'Админ-панель', requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'Interview Prep'
  
  const token = localStorage.getItem('auth_token')
  const user = JSON.parse(localStorage.getItem('auth_user') || 'null')
  const isAuthenticated = !!token && !!user
  const isAdmin = user?.role === 'admin'

  // Redirect authenticated users away from login page
  if (to.meta.guest && isAuthenticated) {
    return next('/')
  }

  // Require authentication
  if (to.meta.requiresAuth && !isAuthenticated) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }

  // Require admin role
  if (to.meta.requiresAdmin && !isAdmin) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }

  next()
})

export default router
