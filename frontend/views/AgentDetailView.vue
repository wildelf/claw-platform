<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import { useAgentsStore } from '@/stores/agents'
import { useModelsStore } from '@/stores/models'

const route = useRoute()
const router = useRouter()
const agentsStore = useAgentsStore()
const modelsStore = useModelsStore()

const agentId = computed(() => route.params.id as string)
const agent = computed(() => agentsStore.currentAgent)

const running = ref(false)
const selectedModelId = ref<string | null>(null)
const taskInput = ref('')
const outputRef = ref<HTMLPreElement | null>(null)
const uploadedImages = ref<string[]>([])
const imageInputRef = ref<HTMLInputElement | null>(null)

// Event state
const currentEvent = ref<{
  type: string
  skillName?: string
  skillId?: string
  toolName?: string
} | null>(null)
const events = ref<Array<{
  type: string
  content?: string
  skillName?: string
  toolName?: string
  timestamp: Date
}>>([])
const thinkingExpanded = ref(false)
const thinkingContent = ref('')

onMounted(async () => {
  await agentsStore.fetchAgent(agentId.value)
  await modelsStore.fetchModels()
  // Set default selected model to agent's configured model
  if (agent.value?.model_config_id) {
    selectedModelId.value = agent.value.model_config_id
  }
})

function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'default' {
  switch (status) {
    case 'active': return 'success'
    case 'inactive': return 'warning'
    case 'error': return 'danger'
    default: return 'default'
  }
}

function getEventIcon(type: string): string {
  switch (type) {
    case 'preparing': return '⚙️'
    case 'skill_loading': return '📦'
    case 'skill_loaded': return '✅'
    case 'skill_reading': return '📖'
    case 'tool_call': return '🔧'
    case 'content': return '💬'
    case 'thinking': return '🤔'
    case 'done': return '🎉'
    case 'error': return '❌'
    default: return '📝'
  }
}

function getEventLabel(type: string): string {
  switch (type) {
    case 'preparing': return '准备中'
    case 'skill_loading': return '加载 Skill'
    case 'skill_loaded': return 'Skill 已加载'
    case 'skill_reading': return '读取 Skill'
    case 'tool_call': return '调用工具'
    case 'content': return '输出'
    case 'thinking': return '思考中'
    case 'done': return '完成'
    case 'error': return '错误'
    default: return type
  }
}

function appendOutput(text: string) {
  if (outputRef.value) {
    outputRef.value.textContent = (outputRef.value.textContent || '') + text
    outputRef.value.scrollTop = outputRef.value.scrollHeight
  }
}

function clearOutput() {
  if (outputRef.value) {
    outputRef.value.textContent = ''
  }
  events.value = []
  thinkingContent.value = ''
  currentEvent.value = null
}

function handleRun() {
  if (!taskInput.value.trim()) return
  running.value = true
  clearOutput()
  uploadedImages.value = []

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
          handleEvent(data)
        } catch {}
      }
    }
  }

  xhr.onload = () => {
    if (xhr.status >= 400) {
      appendOutput(`\nError: HTTP ${xhr.status}`)
      events.value.push({
        type: 'error',
        content: `HTTP ${xhr.status}`,
        timestamp: new Date()
      })
    }
    running.value = false
  }

  xhr.onerror = () => {
    appendOutput(`\nError: Network error`)
    events.value.push({
      type: 'error',
      content: 'Network error',
      timestamp: new Date()
    })
    running.value = false
  }

  xhr.send(JSON.stringify({ task: taskInput.value, images: uploadedImages.value, model_config_id: selectedModelId.value }))
}

function handleEvent(data: any) {
  const event = {
    type: data.type || 'unknown',
    timestamp: new Date()
  }

  switch (data.type) {
    case 'start':
      events.value.push({ ...event, content: `开始执行任务: ${data.task}` })
      break

    case 'preparing':
      currentEvent.value = { type: 'preparing' }
      events.value.push({ ...event, content: data.message || '准备中...' })
      break

    case 'skill_loading':
      currentEvent.value = { type: 'skill_loading', skillName: data.skill_name, skillId: data.skill_id }
      events.value.push({
        ...event,
        type: 'skill_loading',
        skillName: data.skill_name
      })
      break

    case 'skill_loaded':
      currentEvent.value = null
      events.value.push({
        ...event,
        type: 'skill_loaded',
        skillName: data.skill_name
      })
      break

    case 'skill_reading':
      currentEvent.value = { type: 'skill_reading', skillName: data.skill_id }
      events.value.push({
        ...event,
        type: 'skill_reading',
        skillName: data.skill_id,
        content: `读取 Skill 文件: ${data.file}`
      })
      break

    case 'tool_call':
      currentEvent.value = { type: 'tool_call', toolName: data.tool }
      events.value.push({
        ...event,
        type: 'tool_call',
        toolName: data.tool
      })
      break

    case 'thinking':
      thinkingContent.value += data.content || ''
      events.value.push({ ...event, content: data.content })
      break

    case 'content':
      currentEvent.value = null
      let content = data.content || ''
      // Remove AI thinking tags
      content = content.replace(/<think>[\s\S]*?<\/think>/gi, '')
      if (content.trim()) {
        appendOutput(content)
        events.value.push({ ...event, content })
      }
      break

    case 'done':
      currentEvent.value = null
      appendOutput('\n\n--- 完成 ---\n')
      events.value.push({ ...event, content: '任务完成' })
      break

    case 'error':
      currentEvent.value = null
      appendOutput(`\nError: ${data.error}\n`)
      events.value.push({ ...event, content: data.error })
      break
  }
}

function handleEdit() {
  router.push(`/agents/${agentId.value}/edit`)
}

function triggerImageUpload() {
  imageInputRef.value?.click()
}

function handleImageSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files) return

  Array.from(files).forEach(file => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const result = e.target?.result as string
      if (result) {
        uploadedImages.value.push(result)
      }
    }
    reader.readAsDataURL(file)
  })
  target.value = ''
}

function removeImage(index: number) {
  uploadedImages.value.splice(index, 1)
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
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">Model</label>
            <select
              v-model="selectedModelId"
              class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
              :disabled="running"
            >
              <option :value="null">System Default</option>
              <option v-for="model in modelsStore.models" :key="model.id" :value="model.id">
                {{ model.name }} ({{ model.model }})
              </option>
            </select>
          </div>
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

          <!-- Image Upload -->
          <div>
            <div class="flex items-center gap-2 mb-2">
              <label class="text-sm font-medium text-gray-700">Images</label>
              <button
                type="button"
                @click="triggerImageUpload"
                class="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-gray-600"
                :disabled="running"
              >
                + Add Images
              </button>
              <input
                ref="imageInputRef"
                type="file"
                accept="image/*"
                multiple
                class="hidden"
                @change="handleImageSelect"
              />
            </div>
            <div v-if="uploadedImages.length > 0" class="flex flex-wrap gap-2">
              <div
                v-for="(img, idx) in uploadedImages"
                :key="idx"
                class="relative group"
              >
                <img
                  :src="img"
                  class="w-20 h-20 object-cover rounded border border-gray-300"
                />
                <button
                  @click="removeImage(idx)"
                  class="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                  :disabled="running"
                >
                  ×
                </button>
              </div>
            </div>
            <p v-else class="text-xs text-gray-400">No images added</p>
          </div>
          <Button @click="handleRun" :loading="running" :disabled="!taskInput.trim()">
            Execute
          </Button>

          <!-- Status Bar -->
          <div v-if="running || events.length > 0" class="bg-gray-50 rounded-lg p-3">
            <div class="flex items-center gap-2 mb-2">
              <span v-if="running" class="animate-pulse text-sm text-gray-500">执行中...</span>
              <span v-else class="text-sm text-green-600">已完成</span>
            </div>

            <!-- Current Event -->
            <div v-if="currentEvent" class="flex items-center gap-2 text-sm">
              <span v-if="currentEvent.type === 'skill_loading'" class="flex items-center gap-1 text-blue-600">
                <span>📦</span>
                <span>加载 Skill: {{ currentEvent.skillName }}</span>
              </span>
              <span v-else-if="currentEvent.type === 'tool_call'" class="flex items-center gap-1 text-purple-600">
                <span>🔧</span>
                <span>调用工具: {{ currentEvent.toolName }}</span>
              </span>
            </div>

            <!-- Event Timeline (Collapsed) -->
            <details v-if="events.length > 0" class="mt-2">
              <summary class="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                查看事件日志 ({{ events.length }})
              </summary>
              <div class="mt-2 space-y-1 text-xs max-h-32 overflow-y-auto">
                <div
                  v-for="(evt, idx) in events"
                  :key="idx"
                  class="flex items-start gap-2 py-1"
                >
                  <span>{{ getEventIcon(evt.type) }}</span>
                  <span class="text-gray-600">{{ getEventLabel(evt.type) }}</span>
                  <span v-if="evt.skillName" class="text-blue-600">{{ evt.skillName }}</span>
                  <span v-else-if="evt.toolName" class="text-purple-600">{{ evt.toolName }}</span>
                  <span v-else-if="evt.content" class="text-gray-500 truncate flex-1">
                    {{ evt.content.substring(0, 50) }}{{ evt.content.length > 50 ? '...' : '' }}
                  </span>
                </div>
              </div>
            </details>
          </div>

          <!-- Thinking Section (Collapsible) -->
          <div v-if="thinkingContent" class="border border-gray-200 rounded-lg">
            <button
              @click="thinkingExpanded = !thinkingExpanded"
              class="w-full px-4 py-2 flex items-center justify-between text-sm text-gray-600 hover:bg-gray-50"
            >
              <span>🤔 思考过程</span>
              <span>{{ thinkingExpanded ? '收起' : '展开' }}</span>
            </button>
            <pre
              v-if="thinkingExpanded"
              class="px-4 py-2 text-xs text-gray-500 bg-gray-50 overflow-x-auto max-h-48"
            >{{ thinkingContent }}</pre>
          </div>

          <!-- Output -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Output</label>
            <pre ref="outputRef" class="bg-gray-100 p-4 rounded text-sm overflow-x-auto max-h-96 whitespace-pre-wrap">Waiting for response...</pre>
          </div>
        </div>
      </Card>
    </template>
  </div>
</template>
