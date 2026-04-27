import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue')
    },
    {
      path: '/agents',
      name: 'agents',
      component: () => import('@/views/AgentsView.vue')
    },
    {
      path: '/agents/create',
      name: 'agent-create',
      component: () => import('@/views/AgentCreateView.vue')
    },
    {
      path: '/agents/:id',
      name: 'agent-detail',
      component: () => import('@/views/AgentDetailView.vue')
    },
    {
      path: '/agents/:id/edit',
      name: 'agent-edit',
      component: () => import('@/views/AgentEditView.vue')
    },
    {
      path: '/skills',
      name: 'skills',
      component: () => import('@/views/SkillsView.vue')
    },
    {
      path: '/skills/create',
      name: 'skill-create',
      component: () => import('@/views/SkillCreateView.vue')
    },
    {
      path: '/skills/:id',
      name: 'skill-detail',
      component: () => import('@/views/SkillDetailView.vue')
    },
    {
      path: '/skills/:id/edit',
      name: 'skill-edit',
      component: () => import('@/views/SkillEditView.vue')
    },
    {
      path: '/tools',
      name: 'tools',
      component: () => import('@/views/ToolsView.vue')
    },
    {
      path: '/tools/create',
      name: 'tool-create',
      component: () => import('@/views/ToolCreateView.vue')
    },
    {
      path: '/feedback',
      name: 'feedback',
      component: () => import('@/views/FeedbackView.vue')
    },
    {
      path: '/models',
      name: 'models',
      component: () => import('@/views/ModelsView.vue')
    },
    {
      path: '/models/create',
      name: 'model-create',
      component: () => import('@/views/ModelCreateView.vue')
    },
    {
      path: '/models/:id/edit',
      name: 'model-edit',
      component: () => import('@/views/ModelEditView.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue')
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue')
    }
  ]
})

export default router