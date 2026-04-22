import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface User {
  id: string
  username: string
  email: string
}

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false)
  const user = ref<User | null>(null)

  function logout() {
    isAuthenticated.value = false
    user.value = null
  }

  return {
    isAuthenticated,
    user,
    logout
  }
})
