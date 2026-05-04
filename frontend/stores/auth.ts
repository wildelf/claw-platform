import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'

const TOKEN_KEY = 'auth_token'
const USER_KEY = 'auth_user'

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

function getStoredUser(): User | null {
  const stored = localStorage.getItem(USER_KEY)
  return stored ? JSON.parse(stored) : null
}

function setStoredUser(user: User | null): void {
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  } else {
    localStorage.removeItem(USER_KEY)
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getStoredToken())
  const user = ref<User | null>(getStoredUser())

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  async function login(username: string, password: string): Promise<void> {
    // Mock implementation
    token.value = 'mock_token_' + Date.now()
    user.value = { id: '1', username, email: `${username}@example.com` }
    setStoredToken(token.value)
    setStoredUser(user.value)
  }

  async function register(username: string, email: string, password: string): Promise<void> {
    // Mock implementation
    token.value = 'mock_token_' + Date.now()
    user.value = { id: '1', username, email }
    setStoredToken(token.value)
    setStoredUser(user.value)
  }

  function logout(): void {
    token.value = null
    user.value = null
    setStoredToken(null)
    setStoredUser(null)
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