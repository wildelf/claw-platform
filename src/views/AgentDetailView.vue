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

  xhr.send(JSON.stringify({ task: taskInput.value }))
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
