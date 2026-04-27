<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps<{
  collapsed: boolean
}>()

const router = useRouter()

interface NavItem {
  label: string
  path: string
  icon: string
}

interface RecentAgent {
  id: string
  name: string
}

const navItems: NavItem[] = [
  {
    label: 'Dashboard',
    path: '/',
    icon: 'M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25'
  },
  {
    label: 'Agents',
    path: '/agents',
    icon: 'M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z'
  },
  {
    label: 'Skills',
    path: '/skills',
    icon: 'M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a6.759 6.759 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.353.424.682 0 1.015l-1.003.827c-.293.24-.438.612-.438 1.005a.675.675 0 01-.428.255 7.063 7.063 0 01-.254.305l1.298 2.247a1.125 1.125 0 01-1.374 1.41l-1.217-.456c-.355-.133-.675-.372-.795-.572l-.213-1.281c-.09-.543-.56-.94-1.11-.94h-2.594c-.55 0-1.019.398-1.11.94l-.213 1.281c-.063.374-.312.686-.644.87-.074.04-.147.083-.22.127a4.082 4.082 0 01-.247.305l-1.298 2.247a1.125 1.125 0 01-1.369 1.41l-1.217-.456c-.356-.133-.676-.372-.796-.572l-.213-1.281c-.09-.542-.56-.94-1.11-.94h-2.594c-.55 0-1.019.398-1.11.94l-.213 1.281c-.063.374-.313.686-.645.87-.074.04-.147.083-.22.127-.325.196-.72.257-1.075.124l-1.217-.456a1.125 1.125 0 011-1.37l1.296-2.247a1.125 1.125 0 01.26-1.431l1.003-.827c.293-.24.437-.613.43-.991a6.759 6.759 0 010-.255c.007-.378-.137-.75-.43-.991l-1.003-.827a1.125 1.125 0 010-1.015l1.003-.827c.293-.241.438-.613.438-1.005a.675.675 0 01.429-.255 7.063 7.063 0 01.254-.305l-1.298-2.247a1.125 1.125 0 011.373-1.41l1.217.456c.355.133.676.372.796.572l.213 1.281c.09.543.56.94 1.11.94h2.594c.55 0 1.02-.398 1.11-.94l.213-1.281c.063-.374.313-.686.645-.87.074-.04.147-.083.22-.127.325-.196.72-.257 1.075-.124l1.217.456a1.125 1.125 0 011.37-.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a6.759 6.759 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.353.424.682 0 1.015l-1.004.827c-.293.24-.438.612-.438 1.005a.675.675 0 01-.429.255 7.063 7.063 0 01-.254.305l-1.298 2.247a1.125 1.125 0 01-1.369 1.41l-1.217-.456c-.355-.133-.675-.372-.795-.572l-.213-1.281z M15 12a3 3 0 11-6 0 3 3 0 016 0z'
  },
  {
    label: 'Tools',
    path: '/tools',
    icon: 'M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z M21 21l-5.5-5.5'
  },
  {
    label: 'Models',
    path: '/models',
    icon: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z'
  },
  {
    label: 'Feedback',
    path: '/feedback',
    icon: 'M8 10h.01M11 10h.01M14 10h.01M17 10h.01M20 10h.01M6.75 6.75h.01M5.75 6.75h.01M4.75 6.75h.01M6.75 10.25h.01M5.75 10.25h.01M4.75 10.25h.01M6.75 13.75h.01M5.75 13.75h.01M4.75 13.75h.01M14.25 3.75h-9a1 1 0 00-1 1v14a1 1 0 001 1h9a1 1 0 001-1v-14a1 1 0 00-1-1zM14.25 21.75h-9a1 1 0 00-1 1v.008a1 1 0 001 1h9a1 1 0 001-1V22.75a1 1 0 00-1-1h-.008z'
  }
]

const recentAgents: RecentAgent[] = [
  { id: '1', name: 'Code Assistant' },
  { id: '2', name: 'Data Analyzer' },
  { id: '3', name: 'Research Agent' }
]

const sidebarWidth = computed(() => props.collapsed ? 'w-16' : 'w-60')
</script>

<template>
  <aside
    :class="[
      'fixed left-0 top-14 bottom-0 bg-white border-r border-gray-200 transition-all duration-300 z-40',
      sidebarWidth
    ]"
  >
    <nav class="p-2">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        active-class="bg-primary-50 text-primary-600"
        exact-active-class="bg-primary-50 text-primary-600"
        class="flex items-center px-3 py-2.5 rounded-md hover:bg-gray-100 transition-colors mb-1"
        :class="collapsed ? 'justify-center' : ''"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          :class="['w-5 h-5', collapsed ? '' : 'mr-3']"
        >
          <path stroke-linecap="round" stroke-linejoin="round" :d="item.icon" />
        </svg>
        <span v-if="!collapsed" class="text-sm text-gray-700">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <div v-if="!collapsed" class="px-4 pt-4 border-t border-gray-200 mt-4">
      <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Recent Agents</h3>
      <div class="space-y-2">
        <button
          v-for="agent in recentAgents"
          :key="agent.id"
          @click="router.push(`/agents/${agent.id}`)"
          class="w-full text-left px-3 py-2 text-sm text-gray-700 rounded-md hover:bg-gray-100 transition-colors"
        >
          {{ agent.name }}
        </button>
      </div>
    </div>
  </aside>
</template>
