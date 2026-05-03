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

const textModelName = computed(() => {
  if (!agent.value?.text_model_config_id) return 'Default'
  const m = modelsStore.models.find(m => m.id === agent.value?.text_model_config_id)
  return m ? `${m.name} (${m.model})` : 'Default'
})

const imageModelName = computed(() => {
  if (!agent.value?.image_model_config_id) return 'None'
  const m = modelsStore.models.find(m => m.id === agent.value?.image_model_config_id)
  return m ? `${m.name} (${m.model})` : 'None'
})

const videoModelName = computed(() => {
  if (!agent.value?.video_model_config_id) return 'None'
  const m = modelsStore.models.find(m => m.id === agent.value?.video_model_config_id)
  return m ? `${m.name} (${m.model})` : 'None'
})

const running = computed(() => isLoading.value)
const stopping = ref(false)
const taskInput = ref('')
const currentXhr = ref<XMLHttpRequest | null>(null)

// Deduplication for events
const seenEvents = new Set<string>()

// Message for chat-like UI
interface Message {
  id: string
  role: 'user' | 'agent' | 'system'
  content: string
  timestamp: Date
  events?: Array<{
    type: string
    content?: string
    skillName?: string
    toolName?: string
    url?: string
    alt?: string
  }>
  thinking?: string
  isComplete?: boolean
}

const messages = ref<Message[]>([])
const isLoading = ref(false)

onMounted(async () => {
  await agentsStore.fetchAgent(agentId.value)
  await modelsStore.fetchModels()
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
    case 'cancelled': return '🛑'
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
    case 'cancelled': return '已取消'
    default: return type
  }
}

function clearOutput() {
  messages.value = []
  seenEvents.clear()
}

function handleRun() {
  if (!taskInput.value.trim() || isLoading.value) return
  isLoading.value = true
  stopping.value = false

  const userMessage: Message = {
    id: `user-${Date.now()}`,
    role: 'user',
    content: taskInput.value,
    timestamp: new Date()
  }
  messages.value.push(userMessage)

  const agentMessage: Message = {
    id: `agent-${Date.now()}`,
    role: 'agent',
    content: '',
    timestamp: new Date(),
    events: [],
    thinking: ''
  }
  messages.value.push(agentMessage)

  const xhr = new XMLHttpRequest()
  currentXhr.value = xhr
  xhr.open('POST', `/api/agents/${agentId.value}/run`, true)
  xhr.setRequestHeader('Content-Type', 'application/json')

  let lastIndex = 0
  xhr.onprogress = () => {
    const newData = xhr.responseText.substring(lastIndex)
    lastIndex = xhr.responseText.length

    const lines = newData.split('\n')
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          handleEvent(data, agentMessage)
        } catch {}
      }
    }
  }

  xhr.onload = () => {
    const remaining = xhr.responseText.substring(lastIndex)
    lastIndex = xhr.responseText.length

    const lines = remaining.split('\n')
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          handleEvent(data, agentMessage)
        } catch {}
      }
    }

    if (xhr.status >= 400) {
      agentMessage.content += `\nError: HTTP ${xhr.status}`
      agentMessage.events?.push({ type: 'error', content: `HTTP ${xhr.status}` })
    }
    agentMessage.isComplete = true
    isLoading.value = false
    stopping.value = false
    currentXhr.value = null
  }

  xhr.onerror = () => {
    agentMessage.content += `\nError: Network error`
    agentMessage.events?.push({ type: 'error', content: 'Network error' })
    agentMessage.isComplete = true
    isLoading.value = false
    stopping.value = false
    currentXhr.value = null
  }

  xhr.onabort = () => {
    agentMessage.events?.push({ type: 'cancelled', content: '任务已取消' })
    agentMessage.isComplete = true
    isLoading.value = false
    stopping.value = false
    currentXhr.value = null
  }

  xhr.send(JSON.stringify({ task: taskInput.value }))
  taskInput.value = ''
}

async function stopAgent() {
  if (!running.value) return
  stopping.value = true

  // Abort the current XHR
  if (currentXhr.value) {
    currentXhr.value.abort()
  }

  // Call the stop API
  try {
    await fetch(`/api/agents/${agentId.value}/stop`, {
      method: 'POST',
    })
  } catch (e) {
    // Ignore errors from stop API
  }
}

function handleEvent(data: any, agentMessage: Message) {
  const eventKey = data.type + (data.content ? data.content.substring(0, 100) : '') + (data.tool || '') + (data.skill_name || '')
  if (seenEvents.has(eventKey) && data.type === 'content') {
    return
  }
  seenEvents.add(eventKey)

  switch (data.type) {
    case 'start':
      agentMessage.events?.push({ type: 'start', content: `开始执行任务: ${data.task}` })
      break

    case 'skill_loading':
      agentMessage.events?.push({ type: 'skill_loading', skillName: data.skill_name })
      break

    case 'skill_loaded':
      agentMessage.events?.push({ type: 'skill_loaded', skillName: data.skill_name })
      break

    case 'skill_reading':
      agentMessage.events?.push({
        type: 'skill_reading',
        skillName: data.skill_id,
        content: `读取 Skill 文件: ${data.file}`
      })
      break

    case 'tool_call':
      agentMessage.events?.push({ type: 'tool_call', toolName: data.tool })
      break

    case 'thinking':
      agentMessage.thinking = (agentMessage.thinking || '') + (data.content || '')
      break

    case 'content':
      let content = data.content || ''
      content = content.replace(/<think>[\s\S]*?<\/think>/gi, '')
      if (content.trim()) {
        agentMessage.content += content
      }
      break

    case 'cancelled':
      agentMessage.events?.push({ type: 'cancelled', content: '任务已取消' })
      break

    case 'done':
      agentMessage.events?.push({ type: 'done', content: '任务完成' })
      break

    case 'error':
      agentMessage.content += `\nError: ${data.error || 'Unknown error'}`
      agentMessage.events?.push({ type: 'error', content: (data.error || '').substring(0, 100) + ((data.error || '').length > 100 ? '...' : '') })
      break

    case 'image':
      agentMessage.content += `\n[图片: ${data.alt || 'Generated image'}](${data.url})`
      agentMessage.events?.push({ type: 'image', url: data.url, alt: data.alt })
      break
  }
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

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
            <div>
              <p class="text-sm font-medium text-gray-500">Text Model</p>
              <p class="text-gray-900">{{ textModelName }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">Image Model</p>
              <p class="text-gray-900">{{ imageModelName }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">Video Model</p>
              <p class="text-gray-900">{{ videoModelName }}</p>
            </div>
          </div>
        </div>
      </Card>

      <!-- Run Agent Panel -->
      <Card :padding="false">
        <div class="flex flex-col" style="height: 500px;">
          <!-- Header -->
          <div class="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
            <h3 class="text-lg font-medium text-gray-900">对话</h3>
            <Button v-if="messages.length > 0" variant="ghost" size="sm" @click="clearOutput">
              清空对话
            </Button>
          </div>

          <!-- Messages Area -->
          <div class="flex-1 overflow-y-auto p-4 space-y-4">
            <div v-if="messages.length === 0" class="text-center text-gray-400 py-8">
              输入任务开始对话
            </div>

            <div v-for="msg in messages" :key="msg.id">
              <!-- User Message -->
              <div v-if="msg.role === 'user'" class="flex gap-3">
                <div class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white text-sm font-medium shrink-0">
                  {{ msg.content.charAt(0).toUpperCase() }}
                </div>
                <div class="flex-1">
                  <div class="text-sm font-medium text-gray-900">{{ agent?.name || 'User' }}</div>
                  <div class="mt-1 text-gray-700 bg-gray-100 rounded-lg px-4 py-2">
                    {{ msg.content }}
                  </div>
                </div>
              </div>

              <!-- Agent Message -->
              <div v-else class="flex gap-3">
                <div class="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center text-white text-sm font-medium shrink-0">
                  AI
                </div>
                <div class="flex-1">
                  <div class="text-sm font-medium text-gray-900">Agent</div>

                  <!-- Events -->
                  <div v-if="msg.events && msg.events.length > 0" class="mt-2 space-y-1">
                    <div v-for="(evt, idx) in msg.events" :key="idx" class="flex items-center gap-2 text-xs">
                      <span>{{ getEventIcon(evt.type) }}</span>
                      <span class="text-gray-600">{{ getEventLabel(evt.type) }}</span>
                      <span v-if="evt.skillName" class="text-blue-600">{{ evt.skillName }}</span>
                      <span v-else-if="evt.toolName" class="text-purple-600">{{ evt.toolName }}</span>
                      <span v-else-if="evt.url" class="text-green-600">
                        <a :href="evt.url" target="_blank" class="underline">{{ evt.alt || '查看图片' }}</a>
                      </span>
                    </div>
                  </div>

                  <!-- Thinking -->
                  <div v-if="msg.thinking" class="mt-2 text-xs text-gray-400 italic">
                    🤔 {{ msg.thinking.length > 100 ? msg.thinking.substring(0, 100) + '...' : msg.thinking }}
                  </div>

                  <!-- Content -->
                  <div class="mt-2 text-gray-700 whitespace-pre-wrap">{{ msg.content || (msg.isComplete ? '' : '思考中...') }}</div>

                  <!-- Loading indicator -->
                  <div v-if="!msg.isComplete && !msg.content && !msg.thinking" class="mt-1 flex items-center gap-2 text-xs text-gray-400">
                    <span class="animate-pulse">●</span>
                    <span>处理中</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Input Area -->
          <div class="p-4 border-t border-gray-200">
            <div class="flex gap-2">
              <textarea
                v-model="taskInput"
                @keydown.enter.exact.prevent="handleRun"
                class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                rows="2"
                placeholder="输入任务，按 Enter 发送..."
                :disabled="isLoading"
              />
              <div class="flex flex-col gap-2">
                <Button @click="handleRun" :loading="isLoading" :disabled="!taskInput.trim()">
                  发送
                </Button>
                <Button v-if="isLoading" variant="danger" :loading="stopping" @click="stopAgent">
                  停止
                </Button>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </template>
  </div>
</template>
