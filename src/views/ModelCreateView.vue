<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { useModelsStore } from '@/stores/models'

const router = useRouter()
const modelsStore = useModelsStore()

const form = ref({
  name: '',
  type: 'openai',
  model: '',
  api_key: '',
  base_url: ''
})

const loading = ref(false)
const testing = ref(false)
const testResult = ref<{ok: boolean, message: string} | null>(null)
const error = ref<string | null>(null)

const providerOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'local', label: 'Local' },
  { value: 'other', label: 'Other' }
]

async function handleSubmit() {
  if (!form.value.name.trim()) {
    error.value = 'Name is required'
    return
  }
  if (!form.value.model.trim()) {
    error.value = 'Model name is required'
    return
  }

  loading.value = true
  error.value = null

  try {
    await modelsStore.createModel({
      name: form.value.name,
      type: form.value.type as any,
      model: form.value.model,
      api_key: form.value.api_key || undefined,
      base_url: form.value.base_url || undefined
    })
    router.push('/models')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to create model'
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push('/models')
}

async function testConnection() {
  if (!form.value.model.trim()) {
    testResult.value = { ok: false, message: 'Model name is required' }
    return
  }

  testing.value = true
  testResult.value = null

  try {
    const response = await fetch('/api/models/test-connection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: form.value.type,
        model: form.value.model,
        api_key: form.value.api_key || undefined,
        base_url: form.value.base_url || undefined
      })
    })
    testResult.value = await response.json()
  } catch (e) {
    testResult.value = { ok: false, message: 'Failed to test connection' }
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">Create Model Configuration</h1>

    <Card v-if="error" class="bg-red-50">
      <p class="text-red-600">{{ error }}</p>
    </Card>

    <Card title="Model Information">
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
          <Input
            v-model="form.name"
            placeholder="e.g., OpenAI GPT-4o"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Provider *</label>
          <select
            v-model="form.type"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option v-for="opt in providerOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Model Name *</label>
          <Input
            v-model="form.model"
            placeholder="e.g., gpt-4o"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">API Key</label>
          <input
            v-model="form.api_key"
            type="password"
            placeholder="Optional - for API authentication"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
          <Input
            v-model="form.base_url"
            placeholder="e.g., https://api.openai.com/v1"
          />
          <p class="text-sm text-gray-500 mt-1">
            Optional - leave empty to use provider's default endpoint
          </p>
        </div>

        <!-- Test Connection -->
        <div class="flex items-center gap-3">
          <Button
            type="button"
            variant="secondary"
            @click="testConnection"
            :loading="testing"
            :disabled="!form.model.trim()"
          >
            Test Connection
          </Button>
          <span v-if="testResult" :class="testResult.ok ? 'text-green-600' : 'text-red-600'">
            {{ testResult.message }}
          </span>
        </div>

        <div class="flex gap-3 pt-4">
          <Button type="submit" variant="primary" :loading="loading">
            Create
          </Button>
          <Button type="button" variant="secondary" @click="handleCancel">
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  </div>
</template>