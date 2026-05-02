<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import Button from '@/components/ui/Button.vue'
import type { SkillConfig } from '@/types'
import { useModelsStore } from '@/stores/models'

interface Props {
  modelValue: SkillConfig
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: SkillConfig]
}>()

const modelsStore = useModelsStore()

// Local copy for editing
const localConfig = ref<SkillConfig>({ ...props.modelValue })

onMounted(() => {
  if (modelsStore.models.length === 0) {
    modelsStore.fetchModels()
  }
})

// Sync changes back to parent
watch(localConfig, (newVal) => {
  emit('update:modelValue', { ...newVal })
}, { deep: true })

const rateLimitEnabled = ref(localConfig.value.rate_limit !== null)
const cacheEnabled = ref(localConfig.value.cache_enabled)

function toggleRateLimit() {
  if (rateLimitEnabled.value) {
    localConfig.value.rate_limit = {
      requests_per_minute: 60,
      tokens_per_minute: 100000
    }
  } else {
    localConfig.value.rate_limit = null
  }
}

function toggleCache() {
  localConfig.value.cache_enabled = cacheEnabled.value
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const modelOptions = ref<any[]>([])

watch(() => modelsStore.models, (models) => {
  modelOptions.value = [
    { value: '', label: 'Default (agent model)' },
    ...models.map(m => ({ value: m.id, label: `${m.name} (${m.type})` }))
  ]
}, { immediate: true })

const priorityOptions = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' }
]
</script>

<template>
  <Card title="Skill Configuration" :padding="true">
    <div class="space-y-4">
      <!-- Model Binding -->
      <Select
        v-model="localConfig.model_id"
        :options="modelOptions"
        label="Model"
        placeholder="Select a model..."
      />

      <!-- Timeout -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Timeout (ms)</label>
        <Input
          v-model="localConfig.timeout_ms"
          type="number"
          placeholder="30000"
        />
        <p class="text-xs text-gray-500 mt-1">Maximum time to wait for skill execution (default: 30000ms)</p>
      </div>

      <!-- Max Retries -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Max Retries</label>
        <Input
          v-model="localConfig.max_retries"
          type="number"
          placeholder="3"
        />
      </div>

      <!-- Priority -->
      <Select
        v-model="localConfig.priority"
        :options="priorityOptions"
        label="Priority"
        placeholder="Select priority..."
      />

      <!-- Max Concurrent -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Max Concurrent</label>
        <Input
          v-model="localConfig.max_concurrent"
          type="number"
          placeholder="5"
        />
        <p class="text-xs text-gray-500 mt-1">Maximum parallel executions</p>
      </div>

      <!-- Rate Limiting -->
      <div class="border-t pt-4">
        <div class="flex items-center justify-between mb-3">
          <label class="text-sm font-medium text-gray-700">Rate Limiting</label>
          <button
            type="button"
            @click="toggleRateLimit"
            :class="[
              'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
              rateLimitEnabled ? 'bg-blue-600' : 'bg-gray-200'
            ]"
          >
            <span
              :class="[
                'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                rateLimitEnabled ? 'translate-x-6' : 'translate-x-1'
              ]"
            />
          </button>
        </div>

        <div v-if="rateLimitEnabled" class="space-y-3 pl-4 border-l-2 border-gray-200">
          <div>
            <label class="block text-xs text-gray-600 mb-1">Requests per Minute</label>
            <Input
              v-model="localConfig.rate_limit!.requests_per_minute"
              type="number"
              placeholder="60"
            />
          </div>
          <div>
            <label class="block text-xs text-gray-600 mb-1">Tokens per Minute</label>
            <Input
              v-model="localConfig.rate_limit!.tokens_per_minute"
              type="number"
              placeholder="100000"
            />
          </div>
        </div>
      </div>

      <!-- Caching -->
      <div class="border-t pt-4">
        <div class="flex items-center justify-between mb-3">
          <label class="text-sm font-medium text-gray-700">Result Caching</label>
          <button
            type="button"
            @click="toggleCache"
            :class="[
              'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
              cacheEnabled ? 'bg-blue-600' : 'bg-gray-200'
            ]"
          >
            <span
              :class="[
                'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                cacheEnabled ? 'translate-x-6' : 'translate-x-1'
              ]"
            />
          </button>
        </div>

        <div v-if="cacheEnabled" class="pl-4 border-l-2 border-gray-200">
          <div>
            <label class="block text-xs text-gray-600 mb-1">Cache TTL (seconds)</label>
            <Input
              v-model="localConfig.cache_ttl_seconds"
              type="number"
              placeholder="300"
            />
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>
