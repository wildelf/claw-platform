<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { useModelsStore } from '@/stores/models'

const route = useRoute()
const router = useRouter()
const modelsStore = useModelsStore()

const modelId = route.params.id as string

const form = ref({
  name: '',
  type: 'openai',
  model: '',
  api_key: '',
  base_url: '',
  modality: 'text'
})

const loading = ref(false)
const error = ref<string | null>(null)

const providerOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'local', label: 'Local' },
  { value: 'other', label: 'Other' }
]

onMounted(async () => {
  const row = await modelsStore.getModel(modelId)
  if (row) {
    form.value.name = row.name
    form.value.type = row.type
    form.value.model = row.model
    form.value.api_key = row.api_key || ''
    form.value.base_url = row.base_url || ''
    form.value.modality = row.modality || 'text'
  }
})

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
    await modelsStore.updateModel(modelId, {
      name: form.value.name,
      type: form.value.type as any,
      model: form.value.model,
      api_key: form.value.api_key || undefined,
      base_url: form.value.base_url || undefined,
      modality: form.value.modality
    })
    router.push('/models')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to update model'
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push('/models')
}
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">Edit Model Configuration</h1>

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
            placeholder="Leave empty to keep current"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p class="text-sm text-gray-500 mt-1">
            Leave empty to keep current API key
          </p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
          <Input
            v-model="form.base_url"
            placeholder="e.g., https://api.openai.com/v1"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Modality</label>
          <select
            v-model="form.modality"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="text">Text</option>
            <option value="image-to-text">Image to Text (VLM)</option>
            <option value="text-to-image">Text to Image</option>
            <option value="image-to-image">Image to Image</option>
            <option value="text-to-video">Text to Video</option>
            <option value="video">Video (reserved)</option>
          </select>
        </div>

        <div class="flex gap-3 pt-4">
          <Button type="submit" variant="primary" :loading="loading">
            Save Changes
          </Button>
          <Button type="button" variant="secondary" @click="handleCancel">
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  </div>
</template>
