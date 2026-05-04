<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import Modal from '@/components/ui/Modal.vue'
import { scheduledTasksApi } from '@/api/scheduled_tasks'
import { useAgentsStore } from '@/stores/agents'
import type { ScheduledTask } from '@/types'

const agentsStore = useAgentsStore()

const tasks = ref<ScheduledTask[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// Modal state
const showModal = ref(false)
const modalTitle = ref('')
const editingTask = ref<ScheduledTask | null>(null)

// Form state
const form = ref({
  name: '',
  description: '',
  agent_id: '',
  schedule_type: 'once' as 'once' | 'cron' | 'interval',
  cron_expression: '',
  interval_seconds: 60,
  run_at: '',
  task_input: ''
})
const formErrors = ref<Record<string, string>>({})
const submitting = ref(false)

onMounted(async () => {
  await loadTasks()
  await agentsStore.fetchAgents()
})

async function loadTasks() {
  loading.value = true
  error.value = null
  try {
    tasks.value = await scheduledTasksApi.list()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load tasks'
  } finally {
    loading.value = false
  }
}

function openCreateModal() {
  editingTask.value = null
  modalTitle.value = 'Create Scheduled Task'
  form.value = {
    name: '',
    description: '',
    agent_id: '',
    schedule_type: 'once',
    cron_expression: '',
    interval_seconds: 60,
    run_at: '',
    task_input: ''
  }
  formErrors.value = {}
  showModal.value = true
}

function openEditModal(task: ScheduledTask) {
  editingTask.value = task
  modalTitle.value = 'Edit Scheduled Task'
  form.value = {
    name: task.name,
    description: task.description,
    agent_id: task.agent_id,
    schedule_type: task.schedule_type,
    cron_expression: task.cron_expression || '',
    interval_seconds: task.interval_seconds || 60,
    run_at: task.run_at ? task.run_at.slice(0, 16) : '',
    task_input: task.task_input
  }
  formErrors.value = {}
  showModal.value = true
}

function closeModal() {
  if (submitting.value) return
  showModal.value = false
  editingTask.value = null
}

function validateForm(): boolean {
  formErrors.value = {}

  if (!form.value.name.trim()) {
    formErrors.value.name = 'Name is required'
  }
  if (!form.value.agent_id) {
    formErrors.value.agent_id = 'Agent is required'
  }
  if (!form.value.task_input.trim()) {
    formErrors.value.task_input = 'Task input is required'
  }
  if (form.value.schedule_type === 'cron' && !form.value.cron_expression.trim()) {
    formErrors.value.cron_expression = 'Cron expression is required'
  }
  if (form.value.schedule_type === 'interval' && (!form.value.interval_seconds || form.value.interval_seconds <= 0)) {
    formErrors.value.interval_seconds = 'Interval must be positive'
  }
  if (form.value.schedule_type === 'once' && !form.value.run_at) {
    formErrors.value.run_at = 'Run at time is required'
  }

  return Object.keys(formErrors.value).length === 0
}

async function handleSubmit() {
  if (!validateForm()) return

  submitting.value = true
  try {
    const payload: Partial<ScheduledTask> = {
      name: form.value.name,
      description: form.value.description,
      agent_id: form.value.agent_id,
      schedule_type: form.value.schedule_type,
      task_input: form.value.task_input
    }

    if (form.value.schedule_type === 'cron') {
      payload.cron_expression = form.value.cron_expression
    }
    if (form.value.schedule_type === 'interval') {
      payload.interval_seconds = form.value.interval_seconds
    }
    if (form.value.schedule_type === 'once') {
      payload.run_at = form.value.run_at
    }

    if (editingTask.value) {
      await scheduledTasksApi.update(editingTask.value.id, payload)
    } else {
      await scheduledTasksApi.create(payload)
    }

    closeModal()
    await loadTasks()
  } catch (e) {
    formErrors.value.submit = e instanceof Error ? e.message : 'Failed to save task'
  } finally {
    submitting.value = false
  }
}

async function handleDelete(task: ScheduledTask) {
  if (!confirm(`Are you sure you want to delete "${task.name}"?`)) return

  try {
    await scheduledTasksApi.delete(task.id)
    await loadTasks()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to delete task'
  }
}

async function handleTrigger(task: ScheduledTask) {
  try {
    await scheduledTasksApi.trigger(task.id)
    await loadTasks()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to trigger task'
  }
}

function getStatusVariant(status: string): 'default' | 'success' | 'warning' | 'danger' | 'info' {
  switch (status) {
    case 'active': return 'success'
    case 'paused': return 'warning'
    case 'completed': return 'info'
    case 'failed': return 'danger'
    default: return 'default'
  }
}

function formatScheduleInfo(task: ScheduledTask): string {
  switch (task.schedule_type) {
    case 'cron':
      return `Cron: ${task.cron_expression}`
    case 'interval':
      return `Every ${task.interval_seconds} seconds`
    case 'once':
      return `Once at ${task.run_at ? new Date(task.run_at).toLocaleString() : 'Not set'}`
    default:
      return task.schedule_type
  }
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return 'Never'
  return new Date(dateStr).toLocaleString()
}

const agentOptions = computed(() =>
  agentsStore.agents.map(a => ({ value: a.id, label: a.name }))
)

const scheduleTypeOptions = [
  { value: 'once', label: 'Once' },
  { value: 'cron', label: 'Cron' },
  { value: 'interval', label: 'Interval' }
]
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">Scheduled Tasks</h1>
      <Button variant="primary" @click="openCreateModal">Create Task</Button>
    </div>

    <!-- Error display -->
    <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
      {{ error }}
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="text-center py-8 text-gray-500">Loading...</div>

    <!-- Empty state -->
    <Card v-else-if="tasks.length === 0" class="text-center py-8">
      <p class="text-gray-500">No scheduled tasks yet.</p>
      <p class="text-gray-400 text-sm mt-1">Create your first task to get started.</p>
    </Card>

    <!-- Tasks list -->
    <div v-else class="space-y-4">
      <Card v-for="task in tasks" :key="task.id">
        <div class="space-y-3">
          <div class="flex justify-between items-start">
            <div>
              <h3 class="text-lg font-semibold text-gray-900">{{ task.name }}</h3>
              <p class="text-gray-500 text-sm">{{ task.description || 'No description' }}</p>
            </div>
            <Badge :variant="getStatusVariant(task.status)">
              {{ task.status }}
            </Badge>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-gray-200">
            <div>
              <p class="text-sm font-medium text-gray-500">Schedule</p>
              <p class="text-gray-900">{{ formatScheduleInfo(task) }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">Task Input</p>
              <p class="text-gray-900 text-sm truncate">{{ task.task_input }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">Next Run</p>
              <p class="text-gray-900">{{ formatDate(task.next_run_at) }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">Last Run</p>
              <p class="text-gray-900">{{ formatDate(task.last_run_at) }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">Run Count</p>
              <p class="text-gray-900">{{ task.run_count }}</p>
            </div>
          </div>

          <!-- Error display -->
          <div v-if="task.last_error" class="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
            <strong>Last Error:</strong> {{ task.last_error }}
          </div>

          <!-- Actions -->
          <div class="flex gap-2 pt-3 border-t border-gray-200">
            <Button variant="primary" size="sm" @click="handleTrigger(task)">Run Now</Button>
            <Button variant="secondary" size="sm" @click="openEditModal(task)">Edit</Button>
            <Button variant="danger" size="sm" @click="handleDelete(task)">Delete</Button>
          </div>
        </div>
      </Card>
    </div>

    <!-- Create/Edit Modal -->
    <Modal :open="showModal" :title="modalTitle" @close="closeModal">
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <Input
            v-model="form.name"
            placeholder="Task name"
            :error="formErrors.name"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <Input
            v-model="form.description"
            placeholder="Optional description"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Agent</label>
          <Select
            v-model="form.agent_id"
            :options="agentOptions"
            placeholder="Select an agent"
            :error="formErrors.agent_id"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Schedule Type</label>
          <Select
            v-model="form.schedule_type"
            :options="scheduleTypeOptions"
          />
        </div>

        <div v-if="form.schedule_type === 'cron'">
          <label class="block text-sm font-medium text-gray-700 mb-1">Cron Expression</label>
          <Input
            v-model="form.cron_expression"
            placeholder="* * * * *"
            :error="formErrors.cron_expression"
          />
          <p class="mt-1 text-xs text-gray-500">Format: minute hour day month weekday</p>
        </div>

        <div v-if="form.schedule_type === 'interval'">
          <label class="block text-sm font-medium text-gray-700 mb-1">Interval (seconds)</label>
          <Input
            v-model="form.interval_seconds"
            type="number"
            :error="formErrors.interval_seconds"
          />
        </div>

        <div v-if="form.schedule_type === 'once'">
          <label class="block text-sm font-medium text-gray-700 mb-1">Run At</label>
          <Input
            v-model="form.run_at"
            type="datetime-local"
            :error="formErrors.run_at"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Task Input</label>
          <textarea
            v-model="form.task_input"
            rows="4"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            :class="{ 'border-red-500': formErrors.task_input }"
            placeholder="Enter the task prompt or input..."
          />
          <p v-if="formErrors.task_input" class="mt-1 text-sm text-red-500">{{ formErrors.task_input }}</p>
        </div>

        <div v-if="formErrors.submit" class="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
          {{ formErrors.submit }}
        </div>
      </form>

      <template #footer>
        <div class="flex justify-end gap-2">
          <Button variant="secondary" @click="closeModal" :disabled="submitting">Cancel</Button>
          <Button variant="primary" @click="handleSubmit" :loading="submitting">
            {{ editingTask ? 'Update' : 'Create' }}
          </Button>
        </div>
      </template>
    </Modal>
  </div>
</template>
