import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/agents',
      name: 'agents',
      component: () => import('@/views/AgentsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/agents/create',
      name: 'agent-create',
      component: () => import('@/views/AgentCreateView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/agents/:id',
      name: 'agent-detail',
      component: () => import('@/views/AgentDetailView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/agents/:id/edit',
      name: 'agent-edit',
      component: () => import('@/views/AgentEditView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/skills',
      name: 'skills',
      component: () => import('@/views/SkillsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/skills/create',
      name: 'skill-create',
      component: () => import('@/views/SkillWorkbenchView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/skills/:id',
      name: 'skill-detail',
      component: () => import('@/views/SkillDetailView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/skills/:id/edit',
      name: 'skill-edit',
      component: () => import('@/views/SkillWorkbenchView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/tools',
      name: 'tools',
      component: () => import('@/views/ToolsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/tools/create',
      name: 'tool-create',
      component: () => import('@/views/ToolCreateView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/feedback',
      name: 'feedback',
      component: () => import('@/views/FeedbackView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/models',
      name: 'models',
      component: () => import('@/views/ModelsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/models/create',
      name: 'model-create',
      component: () => import('@/views/ModelCreateView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/models/:id/edit',
      name: 'model-edit',
      component: () => import('@/views/ModelEditView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guest: true }
    }
  ]
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' })
  } else if (to.meta.guest && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router