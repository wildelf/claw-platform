<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
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

// Conversation state
const currentSessionId = ref<string | null>(null)
const messages = ref<Array<{
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}>>([])

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
const thinkingContent = ref('')

// Image state
const generatedImages = ref<Array<{url: string, alt: string}>>([])
const imageModalOpen = ref(false)
const selectedImage = ref<{url: string, alt: string} | null>(null)

onMounted(async () => {
  await agentsStore.fetchAgent(agentId.value)
  await modelsStore.fetchModels()
  // Set default selected model to agent's configured model
  if (agent.value?.model_config_id) {
    selectedModelId.value = agent.value.model_config_id
  }
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'default' {
  switch (status) {
    case 'active': return 'success'
    case 'inactive': return 'warning'
    case 'error': return 'danger'
    default: return 'default'
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

function clearSession() {
  currentSessionId.value = null
  messages.value = []
  clearOutput()
}

function handleRun() {
  if (!taskInput.value.trim()) return
  running.value = true
  clearOutput()
  uploadedImages.value = []

  const controller = new AbortController()

  fetch(`/api/agents/${agentId.value}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task: taskInput.value, images: uploadedImages.value, model_config_id: selectedModelId.value, session_id: currentSessionId.value }),
    signal: controller.signal,
  }).then(async (response) => {
    if (!response.ok) {
      const errorText = await response.text()
      appendOutput(`\nError: HTTP ${response.status}`)
      events.value.push({
        type: 'error',
        content: `HTTP ${response.status}: ${errorText}`,
        timestamp: new Date()
      })
      running.value = false
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
              handleEvent(data)
            } catch {}
          }
        }
      }
    } catch (e) {
      if ((e as Error).name !== 'AbortError') {
        appendOutput(`\nError: Network error`)
        events.value.push({
          type: 'error',
          content: 'Network error',
          timestamp: new Date()
        })
      }
    }

    running.value = false
  }).catch(() => {
    appendOutput(`\nError: Network error`)
    events.value.push({
      type: 'error',
      content: 'Network error',
      timestamp: new Date()
    })
    running.value = false
  })

  // Store controller for potential cancellation
  ;(window as any).__agentAbortController = controller
}

function handleEvent(data: any) {
  const event = {
    type: data.type || 'unknown',
    timestamp: new Date()
  }

  switch (data.type) {
    case 'image':
      if (data.url) {
        generatedImages.value.push({ url: data.url, alt: data.alt || '' })
        events.value.push({
          type: 'image',
          url: data.url,
          alt: data.alt || '',
          timestamp: new Date()
        })
      }
      break

    case 'start':
      // Capture session_id for continued conversation
      if (data.session_id) {
        currentSessionId.value = data.session_id
      }
      generatedImages.value = []
      events.value.push({ ...event, content: `会话: ${data.task}`, model: data.model })
      // Add user message to local history
      messages.value.push({
        id: `user-${Date.now()}`,
        role: 'user',
        content: data.task,
        timestamp: new Date(),
      })
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
      thinkingContent.value += data.message || ''
      events.value.push({ ...event, content: data.message })
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
      // Add assistant response to message history
      const responseContent = outputRef.value?.textContent || ''
      messages.value.push({
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: responseContent,
        timestamp: new Date(),
      })
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

function isSafeImageUrl(url: string): boolean {
  try {
    const parsed = new URL(url)
    return ['http:', 'https:'].includes(parsed.protocol)
  } catch {
    return false
  }
}

function openImageModal(img: {url: string, alt: string}) {
  if (!isSafeImageUrl(img.url)) {
    console.error('Unsafe image URL blocked:', img.url)
    return
  }
  selectedImage.value = img
  imageModalOpen.value = true
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && imageModalOpen.value) {
    imageModalOpen.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">Agent 信息</h1>
      <div class="flex gap-2">
        <Button variant="primary" @click="handleRun" :loading="running">执行 Agent</Button>
        <Button v-if="currentSessionId" variant="secondary" @click="clearSession">
          新对话
        </Button>
        <Button variant="secondary" @click="handleEdit">编辑</Button>
      </div>
    </div>

    <div v-if="agentsStore.loading" class="text-center py-8 text-gray-500">加载中...</div>
    <div v-else-if="!agent" class="text-center py-8 text-gray-500">Agent 未找到</div>
    <template v-else>
      <!-- 2-column layout: Agent info (1 col) + Execution panel (2 cols) -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Left column: Agent Info (compact) -->
        <Card class="md:col-span-1">
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

            <div class="grid grid-cols-1 gap-4 pt-4 border-t border-gray-200">
              <div>
                <p class="text-sm font-medium text-gray-500">Role</p>
                <p class="text-gray-900">{{ agent.role || '未指定' }}</p>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-500">Goal</p>
                <p class="text-gray-900">{{ agent.goal || '未指定' }}</p>
              </div>
            </div>

            <div class="pt-4 border-t border-gray-200">
              <p class="text-sm font-medium text-gray-500">Backstory</p>
              <p class="text-gray-900 mt-1">{{ agent.backstory || '未指定' }}</p>
            </div>
          </div>
        </Card>

        <!-- Right column: Execution Panel (2 cols on desktop) -->
        <div class="md:col-span-2 space-y-6">
          <!-- Run Agent Panel -->
          <Card>
            <h3 class="text-lg font-medium text-gray-900 mb-4">执行面板</h3>
            <div class="space-y-4">
              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-1">模型</label>
                <select
                  v-model="selectedModelId"
                  class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                  :disabled="running"
                >
                  <option :value="null">系统默认</option>
                  <option v-for="model in modelsStore.models" :key="model.id" :value="model.id">
                    {{ model.name }} ({{ model.model }})
                  </option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">任务描述</label>
                <textarea
                  v-model="taskInput"
                  class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows="3"
                  placeholder="输入任务描述..."
                  :disabled="running"
                />
              </div>

              <!-- Image Upload -->
              <div>
                <div class="flex items-center gap-2 mb-2">
                  <label class="text-sm font-medium text-gray-700">图片</label>
                  <button
                    type="button"
                    @click="triggerImageUpload"
                    class="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-gray-600"
                    :disabled="running"
                  >
                    + 添加图片
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
                <p v-else class="text-xs text-gray-400">未添加图片</p>
              </div>
              <Button @click="handleRun" :loading="running" :disabled="!taskInput.trim()">
                执行
              </Button>

              <!-- Simplified Status Bar -->
              <div v-if="running || events.length > 0" class="bg-gray-50 rounded-lg p-3">
                <div class="flex items-center gap-2 mb-2">
                  <span v-if="running" class="animate-pulse text-sm text-blue-600 font-medium">执行中...</span>
                  <span v-else class="text-sm text-green-600 font-medium">已完成</span>
                </div>

                <!-- Current Event -->
                <div v-if="currentEvent" class="flex items-center gap-2 text-sm">
                  <span v-if="currentEvent.type === 'skill_loading'" class="flex items-center gap-1 text-blue-600">
                    <span>[加载 Skill]</span>
                    <span>{{ currentEvent.skillName }}</span>
                  </span>
                  <span v-else-if="currentEvent.type === 'tool_call'" class="flex items-center gap-1 text-purple-600">
                    <span>[调用工具]</span>
                    <span>{{ currentEvent.toolName }}</span>
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

              <!-- Thinking Section (Always Expanded) -->
              <div v-if="thinkingContent" class="border border-gray-200 rounded-lg">
                <div class="px-4 py-2 text-sm text-gray-600 bg-gray-50 font-medium">
                  思考过程
                </div>
                <pre
                  class="px-4 py-2 text-xs text-gray-500 bg-gray-50 overflow-x-auto max-h-48"
                >{{ thinkingContent }}</pre>
              </div>

              <!-- Conversation History -->
              <div v-if="messages.length > 0" class="mb-4 space-y-3">
                <h3 class="text-sm font-medium text-gray-700">对话历史</h3>
                <div v-for="msg in messages" :key="msg.id"
                     :class="['p-3 rounded-lg', msg.role === 'user' ? 'bg-blue-50' : 'bg-gray-50']">
                  <div class="flex items-center gap-2 mb-1">
                    <span :class="['text-xs font-medium', msg.role === 'user' ? 'text-blue-600' : 'text-gray-600']">
                      {{ msg.role === 'user' ? '用户' : '助手' }}
                    </span>
                    <span class="text-xs text-gray-400">{{ new Date(msg.timestamp).toLocaleTimeString() }}</span>
                  </div>
                  <p class="text-sm text-gray-800 whitespace-pre-wrap">{{ msg.content }}</p>
                </div>
              </div>

              <!-- Output -->
              <div class="space-y-4">
                <!-- Text Output -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">输出</label>
                  <pre ref="outputRef" class="bg-gray-100 p-4 rounded text-sm overflow-x-auto max-h-96 whitespace-pre-wrap">等待输入...</pre>
                </div>

                <!-- Generated Images -->
                <div v-if="generatedImages.length > 0" class="space-y-2">
                  <label class="block text-sm font-medium text-gray-700">生成的图片</label>
                  <div class="flex flex-wrap gap-3">
                    <div
                      v-for="(img, idx) in generatedImages"
                      :key="idx"
                      class="relative group cursor-pointer"
                      @click="openImageModal(img)"
                    >
                      <img
                        :src="img.url"
                        :alt="img.alt"
                        class="max-w-xs rounded border border-gray-300 hover:border-primary-500 transition-colors"
                      />
                      <div class="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs p-1 rounded-b">
                        {{ img.alt || 'Generated image' }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <!-- Image Modal -->
      <div
        v-if="imageModalOpen"
        class="fixed inset-0 bg-black/80 flex items-center justify-center z-50"
        @click="imageModalOpen = false"
      >
        <div class="max-w-4xl max-h-full p-4 relative">
          <img
            v-if="selectedImage"
            :src="selectedImage.url"
            :alt="selectedImage.alt"
            class="max-w-full max-h-screen object-contain"
            @click.stop
          />
          <p v-if="selectedImage?.alt" class="text-white text-center mt-2">{{ selectedImage.alt }}</p>
          <button
            class="absolute top-4 right-4 text-white text-2xl hover:text-gray-300"
            @click="imageModalOpen = false"
          >
            ×
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
