<script setup lang="ts">
import { ref } from 'vue'
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const theme = ref(localStorage.getItem('theme') || 'dark')

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

const navItems = [
  { label: 'Dashboard', path: '/' },
  { label: 'Employee Profiles', path: '/employee-profiles' },
  { label: 'Skills', path: '/skills' },
  { label: 'Tools', path: '/tools' },
  { label: 'Operations', path: '/worker-dashboard' }
]
</script>

<template>
  <header class="fixed top-0 left-0 right-0 h-14 bg-bg-secondary border-b border-border-primary z-50">
    <div class="flex items-center h-full px-4">
      <!-- Sidebar Toggle + Logo -->
      <div class="flex items-center gap-6">
        <button
          @click="emit('toggleSidebar')"
          class="p-2 rounded-md hover:bg-bg-tertiary transition-colors"
          aria-label="Toggle sidebar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 text-text-secondary">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
          </svg>
        </button>

        <div class="flex items-center gap-2">
          <div class="w-8 h-8 bg-accent-primary rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
          </div>
          <span class="text-lg font-bold text-text-primary">Claw Platform</span>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="hidden lg:flex items-center justify-center flex-1 ml-6 space-x-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="px-4 py-2 rounded-lg text-text-secondary hover:bg-bg-tertiary hover:text-text-primary transition-colors text-sm"
          active-class="bg-bg-tertiary text-text-primary font-medium"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <!-- Right Side -->
      <div class="flex items-center gap-4 ml-auto">
        <!-- Notification Bell -->
        <button
          class="w-9 h-9 rounded-lg bg-bg-tertiary hover:bg-border-primary transition flex items-center justify-center"
          aria-label="Notifications"
        >
          <svg class="w-5 h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
          </svg>
        </button>

        <!-- Theme Toggle -->
        <button
          @click="toggleTheme"
          class="p-2 rounded-md hover:bg-bg-tertiary transition-colors"
          :aria-label="theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'"
        >
          <svg v-if="theme === 'light'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-text-secondary">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-text-muted">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
          </svg>
        </button>

        <!-- User / Auth -->
        <div class="flex items-center gap-3">
          <template v-if="isAuthenticated && user">
            <span class="text-sm text-text-secondary">{{ user.username }}</span>
            <button
              @click="handleLogout"
              class="text-sm text-text-secondary hover:text-text-primary transition-colors"
            >
              Logout
            </button>
          </template>
          <template v-else>
            <RouterLink
              to="/login"
              class="text-sm text-text-secondary hover:text-text-primary transition-colors"
            >
              Login
            </RouterLink>
            <RouterLink
              to="/register"
              class="text-sm text-accent-primary hover:text-accent-light transition-colors"
            >
              Register
            </RouterLink>
          </template>
          <!-- User Avatar -->
          <div class="w-9 h-9 rounded-lg bg-accent-primary flex items-center justify-center text-white font-medium">
            {{ user?.username?.[0]?.toUpperCase() || 'U' }}
          </div>
        </div>
      </div>
    </div>
  </header>
</template>
