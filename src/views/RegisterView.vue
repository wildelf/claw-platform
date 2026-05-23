<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formData = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const loading = ref(false)
const error = ref<string | null>(null)

async function handleSubmit() {
  if (!formData.value.username.trim() || !formData.value.email.trim() || !formData.value.password.trim()) {
    error.value = 'All fields are required'
    return
  }

  if (formData.value.password !== formData.value.confirmPassword) {
    error.value = 'Passwords do not match'
    return
  }

  if (formData.value.password.length < 6) {
    error.value = 'Password must be at least 6 characters'
    return
  }

  loading.value = true
  error.value = null

  try {
    await authStore.register(formData.value.username, formData.value.email, formData.value.password)
    router.push('/')
  } catch (e) {
    error.value = (e as any)?.response?.data?.detail || (e as any)?.message || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-bg-secondary">
    <div class="w-full max-w-md">
      <h1 class="text-2xl font-bold text-center text-text-primary mb-6">Register</h1>

      <Card v-if="error" title="Error" class="mb-4 bg-status-error/10">
        <p class="text-status-error">{{ error }}</p>
      </Card>

      <Card title="Create Account">
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-text-secondary mb-1">Username</label>
            <Input
              v-model="formData.username"
              placeholder="Enter username"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-text-secondary mb-1">Email</label>
            <Input
              v-model="formData.email"
              type="email"
              placeholder="Enter email"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-text-secondary mb-1">Password</label>
            <Input
              v-model="formData.password"
              type="password"
              placeholder="Enter password"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-text-secondary mb-1">Confirm Password</label>
            <Input
              v-model="formData.confirmPassword"
              type="password"
              placeholder="Confirm password"
            />
          </div>

          <Button type="submit" variant="primary" :loading="loading" class="w-full">
            Register
          </Button>
        </form>

        <template #footer>
          <p class="text-center text-sm text-text-secondary">
            Already have an account?
            <router-link to="/login" class="text-accent-primary hover:text-accent-light">
              Login
            </router-link>
          </p>
        </template>
      </Card>
    </div>
  </div>
</template>