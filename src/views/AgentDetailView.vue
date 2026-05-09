<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Input from '@/components/ui/Input.vue'
import SessionsDrawer from '@/components/SessionsDrawer.vue'
import { useAgentsStore, getStoredSessionId, setStoredSessionId } from '@/stores/agents'
import { useModelsStore } from '@/stores/models'
import { useScheduledTasksStore } from '@/stores/scheduled_tasks'
import { conversationMemoriesApi } from '@/api/conversation_memories'

const route = useRoute()
const router = useRouter()
const agentsStore = useAgentsStore()
const modelsStore = useModelsStore()
const scheduledTasksStore = useScheduledTasksStore()

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
const currentController = ref<AbortController | null>(null)

// Deduplication for events
const seenEvents = new Set<string>()

// Collapsible state
const scheduledTasksExpanded = ref(true)
const configExpanded = ref(true)

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
  thinkingExpanded?: boolean
  isComplete?: boolean
}

const messages = ref<Message[]>([])
const isLoading = ref(false)
const currentSessionId = ref<string | null>(null)
const drawerOpen = ref(false)

// Schedule modal state
const showScheduleModal = ref(false)
const scheduleForm = ref({
  name: '',
  description: '',
  schedule_type: 'once' as 'once' | 'cron' | 'interval',
  cron_expression: '0 9 * * *',
  interval_seconds: 3600,
  run_at: '',
  task_input: ''
})
const scheduleSubmitting = ref(false)

const agentScheduledTasks = computed(() => {
  return scheduledTasksStore.tasks.filter(t => t.agent_id === agentId.value)
})

onMounted(async () => {
  await agentsStore.fetchAgent(agentId.value)
  await modelsStore.fetchModels()
  await scheduledTasksStore.fetchTasks()
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
  currentSessionId.value = null
  localStorage.removeItem(`agent_session_${agentId.value}`)
}

function openSessionsDrawer() {
  drawerOpen.value = true
}

function handleSessionSelect(sessionId: string) {
  currentSessionId.value = sessionId
  setStoredSessionId(agentId.value, sessionId)
  messages.value = []
  seenEvents.clear()
}

function openScheduleModal() {
  scheduleForm.value = {
    name: '',
    description: '',
    schedule_type: 'once',
    cron_expression: '0 9 * * *',
    interval_seconds: 3600,
    run_at: '',
    task_input: ''
  }
  showScheduleModal.value = true
}

async function handleScheduleSubmit() {
  if (!scheduleForm.value.name.trim() || !scheduleForm.value.task_input.trim()) return
  scheduleSubmitting.value = true
  try {
    const payload: any = {
      name: scheduleForm.value.name,
      description: scheduleForm.value.description,
      agent_id: agentId.value,
      schedule_type: scheduleForm.value.schedule_type,
      task_input: scheduleForm.value.task_input
    }
    if (scheduleForm.value.schedule_type === 'cron') {
      payload.cron_expression = scheduleForm.value.cron_expression
    } else if (scheduleForm.value.schedule_type === 'interval') {
      payload.interval_seconds = scheduleForm.value.interval_seconds
    } else {
      payload.run_at = scheduleForm.value.run_at
    }
    await scheduledTasksStore.createTask(payload)
    showScheduleModal.value = false
  } catch (e) {
    console.error('Failed to create scheduled task:', e)
  } finally {
    scheduleSubmitting.value = false
  }
}

function formatScheduleBrief(task: any): string {
  switch (task.schedule_type) {
    case 'cron': return `Cron: ${task.cron_expression}`
    case 'interval': return `Every ${task.interval_seconds}s`
    case 'once': return `Once at ${task.run_at ? new Date(task.run_at).toLocaleString() : 'Not set'}`
    default: return task.schedule_type
  }
}

async function triggerTask(taskId: string) {
  await scheduledTasksStore.triggerTask(taskId)
}

async function deleteTask(taskId: string) {
  if (confirm('Are you sure?')) {
    await scheduledTasksStore.deleteTask(taskId)
  }
}

async function handleRun() {
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
    thinking: '',
    thinkingExpanded: false,
    isComplete: false
  }
  messages.value.push(agentMessage)

  const controller = new AbortController()
  currentController.value = controller

  // Restore or create session_id for persistence across turns
  const storedSessionId = getStoredSessionId(agentId.value)
  const sessionId = storedSessionId || crypto.randomUUID()
  if (!storedSessionId) {
    setStoredSessionId(agentId.value, sessionId)
  }
  currentSessionId.value = sessionId

  // Fetch recent memories and build context
  let fullTask = taskInput.value
  try {
    const memories = await conversationMemoriesApi.list(agentId.value, 10)
    if (memories.length > 0) {
      // Build context from memories - use summary if available, otherwise use agent_output
      const historyContext = memories
        .map(m => {
          // Use summary if available, otherwise use the raw agent output
          const responseText = m.summary || m.agent_output
          return `用户: ${m.user_input}\n助手: ${responseText}`
        })
        .join('\n\n')
      if (historyContext) {
        fullTask = `${historyContext}\n\n当前问题: ${taskInput.value}`
      }
    }
  } catch (e) {
    // Silently fail - proceed without memory context
    console.warn('Failed to fetch memories:', e)
  }

  const response = await fetch(`/api/agents/${agentId.value}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task: fullTask, session_id: sessionId }),
    signal: controller.signal,
  })

  if (!response.ok) {
    const errorText = await response.text()
    agentMessage.content += `\nError: HTTP ${response.status}`
    agentMessage.events?.push({ type: 'error', content: `HTTP ${response.status}: ${errorText}` })
    agentMessage.isComplete = true
    isLoading.value = false
    stopping.value = false
    currentController.value = null
    taskInput.value = ''
    return
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            handleEvent(data, agentMessage)
          } catch {}
        }
      }
    }
  } catch (e) {
    if ((e as Error).name === 'AbortError') {
      agentMessage.events?.push({ type: 'cancelled', content: '任务已取消' })
    } else {
      agentMessage.content += `\nError: Network error`
      agentMessage.events?.push({ type: 'error', content: 'Network error' })
    }
    agentMessage.isComplete = true
    isLoading.value = false
    stopping.value = false
    currentController.value = null
    taskInput.value = ''
    return
  }

  agentMessage.isComplete = true

  // Store conversation memory asynchronously (fire-and-forget)
  if (agentMessage.content) {
    conversationMemoriesApi.create(
      agentId.value,
      userMessage.content,  // original user input
      agentMessage.content,  // agent output
      currentSessionId.value || undefined
    ).catch(e => {
      console.warn('Failed to store memory:', e)
    })
  }

  isLoading.value = false
  stopping.value = false
  currentController.value = null
  taskInput.value = ''
}

async function stopAgent() {
  if (!running.value) return
  stopping.value = true

  // Abort the current fetch request
  if (currentController.value) {
    currentController.value.abort()
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
      agentMessage.thinking = (agentMessage.thinking || '') + (data.message || '')
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
      agentMessage.thinkingExpanded = false
      break

    case 'done':
      agentMessage.events?.push({ type: 'done', content: '任务完成' })
      agentMessage.thinkingExpanded = false
      break

    case 'error':
      agentMessage.content += `\nError: ${data.error || 'Unknown error'}`
      agentMessage.events?.push({ type: 'error', content: (data.error || '').substring(0, 100) + ((data.error || '').length > 100 ? '...' : '') })
      agentMessage.thinkingExpanded = false
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
        <Button variant="secondary" @click="openScheduleModal">Schedule</Button>
        <Button variant="secondary" @click="handleEdit">Edit</Button>
        <Button variant="ghost" @click="openSessionsDrawer" title="会话历史">历史</Button>
      </div>
    </div>

    <!-- Scheduled Tasks Section -->
    <Card title="Scheduled Tasks" :padding="false">
      <div class="p-4">
        <button
          @click="scheduledTasksExpanded = !scheduledTasksExpanded"
          class="w-full flex items-center justify-between text-sm text-gray-600 hover:bg-gray-50 -mx-4 -mt-4 px-4 py-2"
        >
          <span>Scheduled Tasks</span>
          <span>{{ scheduledTasksExpanded ? '收起' : '展开' }}</span>
        </button>
        <div v-show="scheduledTasksExpanded">
          <div v-if="agentScheduledTasks.length === 0" class="text-center py-4 text-gray-500">
            No scheduled tasks for this agent
          </div>
          <div v-else class="space-y-2">
            <div v-for="task in agentScheduledTasks" :key="task.id" class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <div>
                <p class="font-medium text-gray-900">{{ task.name }}</p>
                <p class="text-sm text-gray-500">{{ formatScheduleBrief(task) }}</p>
              </div>
              <div class="flex gap-2">
                <Button variant="primary" size="sm" @click="triggerTask(task.id)">Run Now</Button>
                <Button variant="danger" size="sm" @click="deleteTask(task.id)">Delete</Button>
              </div>
            </div>
          </div>
          <div class="mt-4">
            <Button variant="secondary" size="sm" @click="openScheduleModal">Create Scheduled Task</Button>
          </div>
        </div>
      </div>
    </Card>

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
            <button
              @click="configExpanded = !configExpanded"
              class="w-full flex items-center justify-between text-sm text-gray-600 hover:bg-gray-50 -mx-4 -mt-4 px-4 py-2"
            >
              <span>Configuration</span>
              <span>{{ configExpanded ? '收起' : '展开' }}</span>
            </button>
            <div v-show="configExpanded">
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
                  <div v-if="msg.thinking" class="mt-2">
                    <button
                      @click="msg.thinkingExpanded = !msg.thinkingExpanded"
                      class="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      <span>{{ msg.thinkingExpanded ? '▼' : '▶' }}</span>
                      <span>🤔 思考过程</span>
                      <span v-if="!msg.thinkingExpanded" class="text-gray-300">({{ msg.thinking.length }} 字)</span>
                    </button>
                    <pre
                      v-if="msg.thinkingExpanded"
                      class="mt-1 text-xs text-gray-500 bg-gray-50 rounded p-2 whitespace-pre-wrap max-h-40 overflow-y-auto"
                    >{{ msg.thinking }}</pre>
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

      <!-- Schedule Task Modal -->
      <div v-if="showScheduleModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <Card class="w-full max-w-md" :title="agent ? `Schedule Task for ${agent.name}` : 'Schedule Task'">
          <form @submit.prevent="handleScheduleSubmit" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Task Name</label>
              <Input v-model="scheduleForm.name" placeholder="e.g., Daily Report" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <Input v-model="scheduleForm.description" placeholder="Optional description" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Schedule Type</label>
              <select v-model="scheduleForm.schedule_type" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                <option value="once">Once</option>
                <option value="cron">Cron Expression</option>
                <option value="interval">Interval</option>
              </select>
            </div>
            <div v-if="scheduleForm.schedule_type === 'cron'">
              <label class="block text-sm font-medium text-gray-700 mb-1">Cron Expression</label>
              <Input v-model="scheduleForm.cron_expression" placeholder="0 9 * * *" />
              <p class="mt-1 text-xs text-gray-500">Format: minute hour day month weekday</p>
            </div>
            <div v-if="scheduleForm.schedule_type === 'interval'">
              <label class="block text-sm font-medium text-gray-700 mb-1">Interval (seconds)</label>
              <Input v-model="scheduleForm.interval_seconds" type="number" />
            </div>
            <div v-if="scheduleForm.schedule_type === 'once'">
              <label class="block text-sm font-medium text-gray-700 mb-1">Run At</label>
              <Input v-model="scheduleForm.run_at" type="datetime-local" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Task Input</label>
              <textarea
                v-model="scheduleForm.task_input"
                rows="3"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                placeholder="What should this agent do?"
              />
            </div>
            <div class="flex gap-2 justify-end">
              <Button variant="secondary" @click="showScheduleModal = false" :disabled="scheduleSubmitting">Cancel</Button>
              <Button variant="primary" @click="handleScheduleSubmit" :loading="scheduleSubmitting">Create</Button>
            </div>
          </form>
        </Card>
      </div>
    </template>
  </div>
  <SessionsDrawer
    :open="drawerOpen"
    :agent-id="agentId"
    @close="drawerOpen = false"
    @select="handleSessionSelect"
  />
</template>
