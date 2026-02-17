import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Questions from '../views/Questions.vue'
import QuestionDetail from '../views/QuestionDetail.vue'
import Admin from '../views/Admin.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { title: 'Interview Prep - Подготовка к IT собеседованиям' }
  },
  {
    path: '/questions/:topic',
    name: 'Questions',
    component: Questions,
    props: true,
    meta: { title: 'Вопросы' }
  },
  {
    path: '/question/:id',
    name: 'QuestionDetail',
    component: QuestionDetail,
    props: true,
    meta: { title: 'Вопрос' }
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
