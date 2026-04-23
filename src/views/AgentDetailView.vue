<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import { useAgentsStore } from '@/stores/agents'

const route = useRoute()
const router = useRouter()
const agentsStore = useAgentsStore()

const agentId = computed(() => route.params.id as string)
const agent = computed(() => agentsStore.currentAgent)

const running = ref(false)
const taskInput = ref('')
const outputRef = ref<HTMLPreElement | null>(null)

onMounted(async () => {
  await agentsStore.fetchAgent(agentId.value)
})

function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'default' {
  switch (status) {
    case 'active': return 'success'
    case 'inactive': return 'warning'
    case 'error': return 'danger'
    default: return 'default'
  }
}

function appendOutput(text: string) {
  if (outputRef.value) {
    outputRef.value.textContent = (outputRef.value.textContent || '') + text
    outputRef.value.scrollTop = outputRef.value.scrollHeight
  }
}

function handleRun() {
  if (!taskInput.value.trim()) return
  running.value = true
  if (outputRef.value) {
    outputRef.value.textContent = ''
  }

  const xhr = new XMLHttpRequest()
  xhr.open('POST', `/api/agents/${agentId.value}/run`, true)
  xhr.setRequestHeader('Content-Type', 'application/json')

  let buffer = ''
  xhr.onprogress = () => {
    buffer += xhr.responseText.substring(buffer.length)
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'content') {
            let content = data.content
            // Remove AI thinking tags
            content = content.replace(/<think>[\s\S]*?<\/think>/gi, '')
            appendOutput(content)
          } else if (data.type === 'error') {
            appendOutput(`\nError: ${data.error}`)
          }
        } catch {}
      }
    }
  }

  xhr.onload = () => {
    if (xhr.status >= 400) {
      appendOutput(`\nError: HTTP ${xhr.status}`)
    }
    running.value = false
  }

  xhr.onerror = () => {
    appendOutput(`\nError: Network error`)
    running.value = false
  }

  xhr.send(JSON.stringify({ task: taskInput.value }))
}

function handleEdit() {
  router.push(`/agents/${agentId.value}/edit`)
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">Agent Details</h1>
      <div class="flex gap-2">
        <Button variant="primary" @click="handleRun" :loading="running">Run Agent</Button>
        <Button variant="secondary" @click="handleEdit">Edit</Button>
      </div>
    </div>

    <div v-if="agentsStore.loading" class="text-center py-8 text-gray-500">Loading...</div>
    <div v-else-if="!agent" class="text-center py-8 text-gray-500">Agent not found</div>
    <template v-else>
      <Card>
        <div class="space-y-4">
          <div class="flex justify-between items-start">
            <div>
              <h2 class="text-xl font-semibold text-gray-900">{{ agent.name }}</h2>
              <p class="text-gray-500 mt-1">{{ agent.description }}</p>
            </div>
            <Badge :variant="getStatusVariant(agent.status)" class="text-sm">
              {{ agent.status }}
            </Badge>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200">
            <div>
              <p class="text-sm font-medium text-gray-500">Role</p>
              <p class="text-gray-900">{{ agent.role || 'Not specified' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">Goal</p>
              <p class="text-gray-900">{{ agent.goal || 'Not specified' }}</p>
            </div>
          </div>

          <div class="pt-4 border-t border-gray-200">
            <p class="text-sm font-medium text-gray-500">Backstory</p>
            <p class="text-gray-900 mt-1">{{ agent.backstory || 'Not specified' }}</p>
          </div>
        </div>
      </Card>

      <!-- Run Agent Panel -->
      <Card>
        <h3 class="text-lg font-medium text-gray-900 mb-4">Run Agent</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Task</label>
            <textarea
              v-model="taskInput"
              class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows="3"
              placeholder="Enter task description..."
              :disabled="running"
            />
          </div>
          <Button @click="handleRun" :loading="running" :disabled="!taskInput.trim()">
            Execute
          </Button>
          <div class="mt-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">Output</label>
            <pre ref="outputRef" class="bg-gray-100 p-4 rounded text-sm overflow-x-auto max-h-96 whitespace-pre-wrap">Waiting for response...</pre>
          </div>
        </div>
      </Card>
    </template>
  </div>
</template>
