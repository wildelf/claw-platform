<script setup lang="ts">
import { ref } from 'vue'
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const theme = ref(localStorage.getItem('theme') || 'light')

function toggleTheme() {
  theme.value = theme.value === 'light' ? 'dark' : 'light'
  document.documentElement.setAttribute('data-theme', theme.value)
  localStorage.setItem('theme', theme.value)
}

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

      <button
        @click="toggleTheme"
        class="p-2 rounded-md hover:bg-gray-100 transition-colors"
        :aria-label="theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'"
      >
        <!-- 太阳图标 (light mode) -->
        <svg v-if="theme === 'light'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-gray-600">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
        </svg>
        <!-- 月亮图标 (dark mode) -->
        <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-gray-400">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
        </svg>
      </button>

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
