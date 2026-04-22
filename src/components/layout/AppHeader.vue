<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const emit = defineEmits<{
  toggleSidebar: []
}>()

const authStore = useAuthStore()
const router = useRouter()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const user = computed(() => authStore.user)

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="fixed top-0 left-0 right-0 h-14 bg-white border-b border-gray-200 z-50">
    <div class="flex items-center h-full px-4">
      <button
        @click="emit('toggleSidebar')"
        class="p-2 rounded-md hover:bg-gray-100 transition-colors"
        aria-label="Toggle sidebar"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
        </svg>
      </button>

      <div class="ml-4 text-lg font-semibold text-gray-900">
        Claw Platform
      </div>

      <nav class="hidden md:flex items-center justify-center flex-1 space-x-8">
        <RouterLink
          to="/"
          class="text-gray-600 hover:text-gray-900 transition-colors"
          active-class="text-primary-600 font-medium"
        >
          Dashboard
        </RouterLink>
        <RouterLink
          to="/agents"
          class="text-gray-600 hover:text-gray-900 transition-colors"
          active-class="text-primary-600 font-medium"
        >
          Agents
        </RouterLink>
        <RouterLink
          to="/skills"
          class="text-gray-600 hover:text-gray-900 transition-colors"
          active-class="text-primary-600 font-medium"
        >
          Skills
        </RouterLink>
        <RouterLink
          to="/tools"
          class="text-gray-600 hover:text-gray-900 transition-colors"
          active-class="text-primary-600 font-medium"
        >
          Tools
        </RouterLink>
        <RouterLink
          to="/feedback"
          class="text-gray-600 hover:text-gray-900 transition-colors"
          active-class="text-primary-600 font-medium"
        >
          Feedback
        </RouterLink>
      </nav>

      <div class="flex items-center space-x-4">
        <template v-if="isAuthenticated && user">
          <span class="text-sm text-gray-700">{{ user.username }}</span>
          <button
            @click="handleLogout"
            class="text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            Logout
          </button>
        </template>
        <template v-else>
          <RouterLink
            to="/login"
            class="text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            Login
          </RouterLink>
          <RouterLink
            to="/register"
            class="text-sm text-primary-600 hover:text-primary-700 transition-colors"
          >
            Register
          </RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>
