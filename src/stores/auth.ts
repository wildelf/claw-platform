import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'

const TOKEN_KEY = 'auth_token'

function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

function setStoredToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getStoredToken())
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  async function login(username: string, password: string): Promise<void> {
    // Mock implementation
    token.value = 'mock_token_' + Date.now()
    user.value = { id: '1', username, email: `${username}@example.com` }
    setStoredToken(token.value)
  }

  async function register(username: string, email: string, password: string): Promise<void> {
    // Mock implementation
    token.value = 'mock_token_' + Date.now()
    user.value = { id: '1', username, email }
    setStoredToken(token.value)
  }

  function logout(): void {
    token.value = null
    user.value = null
    setStoredToken(null)
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    logout
  }
})