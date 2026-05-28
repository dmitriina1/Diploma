import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/',                    name: 'Home',                 component: () => import('../views/Home.vue'),                 meta: { title: 'InterviewHub' } },
  { path: '/login',               name: 'Login',                component: () => import('../views/Login.vue'),                meta: { title: 'Вход', guest: true } },
  { path: '/profile',             name: 'Profile',              component: () => import('../views/Profile.vue'),              meta: { title: 'Профиль', requiresAuth: true } },
  { path: '/interview-questions', name: 'InterviewQuestions',    component: () => import('../views/InterviewQuestions.vue'),   meta: { title: 'Вопросы' } },
  { path: '/question/:id',        name: 'QuestionDetail',        component: () => import('../views/QuestionDetail.vue'),       meta: { title: 'Вопрос' }, props: true },
  { path: '/trainer',             name: 'Trainer',               component: () => import('../views/Trainer.vue'),              meta: { title: 'Тренажёр', requiresAuth: true } },
  { path: '/ai-interview',        name: 'AIInterviewChat',       component: () => import('../views/AIInterviewChat.vue'),      meta: { title: 'AI Interview', requiresAuth: true } },
  { path: '/mock-interview',      name: 'MockInterview',         component: () => import('../views/MockInterview.vue'),        meta: { title: 'Mock Interview', requiresAuth: true } },
  { path: '/recordings',          name: 'InterviewRecordings',   component: () => import('../views/InterviewRecordings.vue'),  meta: { title: 'Записи', requiresAuth: true } },
  { path: '/suggest',             name: 'Suggestions',           component: () => import('../views/Suggestions.vue'),          meta: { title: 'Предложить видео' } },
  { path: '/test-assignments',    name: 'TestAssignments',       component: () => import('../views/TestAssignments.vue'),      meta: { title: 'Тестовые задания', requiresAuth: true } },
  { path: '/test-assignments/:id',name: 'TestAssignmentDetail',  component: () => import('../views/TestAssignmentDetail.vue'), meta: { title: 'Задание', requiresAuth: true }, props: true },
  { path: '/hh-requirements',     name: 'HHRequirements',        component: () => import('../views/HHRequirements.vue'),       meta: { title: 'Навыки из вакансий' } },
  { path: '/admin',               name: 'Admin',                 component: () => import('../views/Admin.vue'),                meta: { title: 'Админ-панель', requiresAuth: true, requiresAdmin: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'InterviewHub'
  const token = localStorage.getItem('auth_token')
  const user = JSON.parse(localStorage.getItem('auth_user') || 'null')
  const isAuth = !!token && !!user
  const isAdmin = user?.role === 'admin'

  if (to.meta.guest && isAuth) return next('/')
  if (to.meta.requiresAuth && !isAuth) return next({ name: 'Login', query: { redirect: to.fullPath } })
  if (to.meta.requiresAdmin && !isAdmin) return next({ name: 'Login', query: { redirect: to.fullPath } })
  next()
})

export default router
