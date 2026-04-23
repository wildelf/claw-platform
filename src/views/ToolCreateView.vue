<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import { useToolsStore } from '@/stores/tools'

const router = useRouter()
const toolsStore = useToolsStore()

const form = ref({
  name: '',
  description: '',
  type: 'CUSTOM'
})

const loading = ref(false)
const error = ref<string | null>(null)

const toolTypes = [
  { value: 'CUSTOM', label: 'Custom' },
  { value: 'MCP', label: 'MCP' }
]

async function handleSubmit() {
  if (!form.value.name.trim()) {
    error.value = 'Name is required'
    return
  }

  loading.value = true
  error.value = null

  try {
    await toolsStore.createTool({
      name: form.value.name,
      description: form.value.description,
      type: form.value.type as any,
      config: {},
      allowed_tools: []
    })
    router.push('/tools')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to create tool'
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push('/tools')
}
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">Create New Tool</h1>

    <Card v-if="error" class="bg-red-50">
      <p class="text-red-600">{{ error }}</p>
    </Card>

    <Card title="Tool Information">
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
          <Input
            v-model="form.name"
            placeholder="Enter tool name"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            v-model="form.description"
            placeholder="Enter tool description"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
          <select
            v-model="form.type"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option v-for="t in toolTypes" :key="t.value" :value="t.value">
              {{ t.label }}
            </option>
          </select>
        </div>

        <div class="flex gap-3 pt-4">
          <Button type="submit" variant="primary" :loading="loading">
            Create Tool
          </Button>
          <Button type="button" variant="secondary" @click="handleCancel">
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  </div>
</template>
