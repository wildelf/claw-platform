<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import { useWorkerStore } from '@/stores/worker'

const workerStore = useWorkerStore()

const pollingInterval = ref<number | null>(null)
const lastRefresh = ref<Date | null>(null)

const completedCount = computed(() =>
  workerStore.tasks.filter(t => t.status === 'completed').length
)
const failedCount = computed(() =>
  workerStore.tasks.filter(t => t.status === 'failed').length
)
const runningCount = computed(() =>
  workerStore.tasks.filter(t => t.status === 'running').length
)
const queuedCount = computed(() =>
  workerStore.tasks.filter(t => t.status === 'queued').length
)

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    running: 'Processing',
    queued: 'Queued',
    completed: 'Completed',
    failed: 'Failed',
  }
  return labels[status] || status
}

function getStatusClasses(status: string): string {
  switch (status) {
    case 'running': return 'bg-status-paused/20 text-status-paused'
    case 'queued': return 'bg-bg-tertiary text-text-secondary'
    case 'completed': return 'bg-status-active/20 text-status-active'
    case 'failed': return 'bg-status-error/20 text-status-error'
    default: return 'bg-bg-tertiary text-text-secondary'
  }
}

function getTaskIconClasses(status: string): string {
  switch (status) {
    case 'running': return 'bg-status-paused/20 text-status-paused'
    case 'queued': return 'bg-bg-tertiary text-text-muted'
    case 'completed': return 'bg-status-active/20 text-status-active'
    case 'failed': return 'bg-status-error/20 text-status-error'
    default: return 'bg-bg-tertiary text-text-muted'
  }
}

function getRowBgClass(status: string): string {
  return status === 'completed' ? 'bg-status-active/5' : ''
}

function timeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return `${seconds} seconds ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes} minutes ago`
  const hours = Math.floor(minutes / 60)
  return `${hours} hours ago`
}

async function handleRefresh() {
  await workerStore.fetchWorkerStatus()
  await workerStore.fetchTasks()
  lastRefresh.value = new Date()
}

function handleRestart() {
  // TODO: Implement restart
}

function handleClearQueue() {
  // TODO: Implement clear queue
}

function handleStop() {
  // TODO: Implement stop
}

onMounted(() => {
  handleRefresh()
  pollingInterval.value = window.setInterval(() => {
    handleRefresh()
  }, 5000)
})

onUnmounted(() => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
  }
})
</script>

<template>
  <div class="p-6">
    <!-- Page Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-text-primary mb-1">Operations Dashboard</h1>
      <p class="text-text-secondary">Real-time monitoring of task queues, execution status, and system health</p>
    </div>

    <!-- Status Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <!-- Worker Status -->
      <div class="bg-bg-card border border-border-primary rounded-xl p-5">
        <div class="flex items-center justify-between mb-3">
          <div class="text-sm text-text-muted">Daemon</div>
          <div class="flex items-center gap-1.5">
            <span
              :class="['w-2 h-2 rounded-full', workerStore.isRunning ? 'bg-status-active animate-pulse' : 'bg-text-muted']"
            ></span>
            <span :class="['text-xs', workerStore.isRunning ? 'text-status-active' : 'text-text-muted']">
              {{ workerStore.isRunning ? 'Online' : 'Offline' }}
            </span>
          </div>
        </div>
        <div class="text-2xl font-bold text-text-primary mb-1">{{ workerStore.workerId || 'worker:local' }}</div>
        <div class="text-xs text-text-muted">
          Last heartbeat: {{ workerStore.lastHeartbeat ? timeAgo(new Date(workerStore.lastHeartbeat)) : 'N/A' }}
        </div>
      </div>

      <!-- Queue Stats -->
      <div class="bg-bg-card border border-border-primary rounded-xl p-5">
        <div class="text-sm text-text-muted mb-3">Task Queue</div>
        <div class="flex items-baseline gap-2 mb-1">
          <div class="text-2xl font-bold text-status-info">{{ queuedCount }}</div>
          <div class="text-xs text-text-muted">Pending</div>
        </div>
        <div class="flex items-baseline gap-2">
          <div class="text-2xl font-bold text-status-paused">{{ runningCount }}</div>
          <div class="text-xs text-text-muted">Processing</div>
        </div>
      </div>

      <!-- Completed Tasks -->
      <div class="bg-bg-card border border-border-primary rounded-xl p-5">
        <div class="text-sm text-text-muted mb-3">Completed (Today)</div>
        <div class="text-2xl font-bold text-status-active mb-1">{{ completedCount }}</div>
        <div class="text-xs text-text-muted">
          {{ workerStore.tasks.length }} total tracked
        </div>
      </div>

      <!-- Failed Tasks -->
      <div class="bg-bg-card border border-border-primary rounded-xl p-5">
        <div class="text-sm text-text-muted mb-3">Failed (Today)</div>
        <div class="text-2xl font-bold text-status-error mb-1">{{ failedCount }}</div>
        <div class="text-xs text-text-muted">
          Success rate: {{ workerStore.tasks.length > 0 ? Math.round((completedCount / workerStore.tasks.length) * 100) : 0 }}%
        </div>
      </div>
    </div>

    <!-- Main Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Task Queue (Left 2/3) -->
      <div class="lg:col-span-2 bg-bg-card border border-border-primary rounded-xl">
        <div class="px-5 py-4 border-b border-border-primary flex items-center justify-between">
          <h2 class="font-semibold text-text-primary">Task Queue</h2>
          <button
            class="px-3 py-1.5 rounded-lg bg-bg-tertiary hover:bg-border-primary text-sm font-medium text-text-primary transition border border-border-primary flex items-center gap-1"
            @click="handleRefresh"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Refresh
          </button>
        </div>

        <div class="divide-y divide-border-primary">
          <!-- Empty State -->
          <div v-if="workerStore.tasks.length === 0" class="px-5 py-12 text-center">
            <svg class="w-10 h-10 text-text-muted mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            <p class="text-text-muted text-sm">No tasks in queue</p>
          </div>

          <!-- Task Items -->
          <div
            v-for="task in workerStore.tasks"
            :key="task.task_id"
            :class="['px-5 py-4 hover:bg-bg-hover transition', getRowBgClass(task.status)]"
          >
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-3">
                <!-- Icon -->
                <div :class="['w-8 h-8 rounded-lg flex items-center justify-center', getTaskIconClasses(task.status)]">
                  <!-- Running: spinner -->
                  <svg v-if="task.status === 'running'" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <!-- Queued: clock -->
                  <svg v-else-if="task.status === 'queued'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                  <!-- Completed: check -->
                  <svg v-else-if="task.status === 'completed'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                  <!-- Failed: X -->
                  <svg v-else-if="task.status === 'failed'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </div>
                <div>
                  <div class="text-sm font-medium text-text-primary">{{ task.task_type || 'Task' }}</div>
                  <div class="text-xs text-text-muted font-mono">{{ task.task_id }}</div>
                </div>
              </div>
              <Badge>
                <span :class="['px-2 py-1 rounded-full text-xs font-medium', getStatusClasses(task.status)]">
                  {{ getStatusLabel(task.status) }}
                </span>
              </Badge>
            </div>
            <div class="flex items-center justify-between text-xs text-text-muted">
              <div class="flex items-center gap-4">
                <span v-if="task.task_type">Type: {{ task.task_type }}</span>
                <span v-if="task.message">{{ task.message }}</span>
              </div>
              <button class="text-red-400 hover:text-red-300 transition" v-if="task.status === 'queued' || task.status === 'running'">
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Worker Info (Right 1/3) -->
      <div class="space-y-6">
        <!-- Worker Details -->
        <div class="bg-bg-card border border-border-primary rounded-xl p-5">
          <h3 class="font-semibold text-text-primary mb-4">Daemon Details</h3>
          <div class="space-y-3 text-sm">
            <div class="flex items-center justify-between">
              <span class="text-text-muted">Worker ID</span>
              <span class="code-editor text-xs bg-bg-tertiary px-2 py-1 rounded text-text-secondary">{{ workerStore.workerId || 'N/A' }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-text-muted">Status</span>
              <span :class="workerStore.isRunning ? 'text-status-active' : 'text-text-muted'">
                {{ workerStore.isRunning ? 'Running' : 'Stopped' }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-text-muted">Last Heartbeat</span>
              <span class="text-text-secondary">
                {{ workerStore.lastHeartbeat ? new Date(workerStore.lastHeartbeat).toLocaleTimeString() : 'N/A' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="bg-bg-card border border-border-primary rounded-xl p-5">
          <h3 class="font-semibold text-text-primary mb-4">Quick Actions</h3>
          <div class="space-y-2">
            <button
              class="w-full px-4 py-2 rounded-lg bg-bg-tertiary hover:bg-border-primary text-sm font-medium text-text-primary transition border border-border-primary text-left flex items-center gap-2"
              @click="handleRestart"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              Restart Daemon
            </button>
            <button
              class="w-full px-4 py-2 rounded-lg bg-bg-tertiary hover:bg-border-primary text-sm font-medium text-text-primary transition border border-border-primary text-left flex items-center gap-2"
              @click="handleClearQueue"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
              Clear Queue
            </button>
            <button
              class="w-full px-4 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-sm font-medium transition text-left flex items-center gap-2"
              @click="handleStop"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"/>
              </svg>
              Stop Daemon
            </button>
          </div>
        </div>

        <!-- Redis Connection -->
        <div class="bg-bg-card border border-border-primary rounded-xl p-5">
          <h3 class="font-semibold text-text-primary mb-4">Redis Connection</h3>
          <div class="space-y-3 text-sm">
            <div class="flex items-center justify-between">
              <span class="text-text-muted">Status</span>
              <span class="text-text-secondary">{{ workerStore.redisConnected ? 'Connected' : 'Disconnected' }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-text-muted">Queue Depth</span>
              <span class="text-text-secondary">{{ queuedCount }} tasks</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-text-muted">Processing</span>
              <span class="text-text-secondary">{{ runningCount }} tasks</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
