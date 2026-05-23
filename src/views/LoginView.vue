<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref<string | null>(null)

async function handleSubmit() {
  if (!username.value.trim() || !password.value.trim()) {
    error.value = 'Username and password are required'
    return
  }

  loading.value = true
  error.value = null

  try {
    await authStore.login(username.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = (e as any)?.response?.data?.detail || (e as any)?.message || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-bg-secondary">
    <div class="w-full max-w-md">
      <h1 class="text-2xl font-bold text-center text-text-primary mb-6">Login</h1>

      <Card v-if="error" title="Error" class="mb-4 bg-status-error/10">
        <p class="text-status-error">{{ error }}</p>
      </Card>

      <Card title="Sign In">
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-text-secondary mb-1">Username</label>
            <Input
              v-model="username"
              placeholder="Enter username"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-text-secondary mb-1">Password</label>
            <Input
              v-model="password"
              type="password"
              placeholder="Enter password"
            />
          </div>

          <Button type="submit" variant="primary" :loading="loading" class="w-full">
            Login
          </Button>
        </form>

        <template #footer>
          <p class="text-center text-sm text-text-secondary">
            Don't have an account?
            <router-link to="/register" class="text-accent-primary hover:text-accent-light">
              Register
            </router-link>
          </p>
        </template>
      </Card>
    </div>
  </div>
</template>