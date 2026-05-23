<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import operationsApi, { type WorkerStatus, type QueueStats, type TaskItem } from '@/api/operations'

const workerStatus = ref<WorkerStatus | null>(null)
const queueStats = ref<QueueStats | null>(null)
const tasks = ref<TaskItem[]>([])
const loading = ref(false)
const refreshing = ref(false)

let refreshInterval: ReturnType<typeof setInterval> | null = null

const taskStatusVariant = (status: string): 'success' | 'warning' | 'danger' | 'info' | 'default' => {
  switch (status) {
    case 'completed': return 'success'
    case 'processing': return 'info'
    case 'queued': return 'warning'
    case 'failed': return 'danger'
    case 'cancelled': return 'default'
    default: return 'default'
  }
}

const statusLabel = (status: string) => {
  const labels: Record<string, string> = {
    online: '在线',
    stale: '心跳超时',
    offline: '离线',
    queued: '排队中',
    processing: '执行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return labels[status] || status
}

const statusDotClass = (status: string) => {
  switch (status) {
    case 'online': return 'bg-green-500'
    case 'stale': return 'bg-yellow-500'
    case 'offline': return 'bg-gray-400'
    case 'processing': return 'bg-blue-500 animate-pulse'
    case 'queued': return 'bg-yellow-500'
    case 'completed': return 'bg-green-500'
    case 'failed': return 'bg-red-500'
    default: return 'bg-gray-400'
  }
}

async function refreshAll() {
  refreshing.value = true
  try {
    const [worker, stats, taskList] = await Promise.all([
      operationsApi.getWorkerStatus(),
      operationsApi.getQueueStats(),
      operationsApi.listTasks({ limit: 50 })
    ])
    workerStatus.value = worker
    queueStats.value = stats
    tasks.value = taskList.tasks || []
  } catch (e) {
    console.error('Failed to refresh operations data:', e)
  } finally {
    refreshing.value = false
  }
}

async function handleCancelTask(taskId: string) {
  if (confirm('确定要取消此任务吗？')) {
    await operationsApi.cancelTask(taskId)
    await refreshAll()
  }
}

async function handleRestartWorker() {
  if (confirm('确定要重启 Worker 吗？')) {
    await operationsApi.restartWorker()
    await refreshAll()
  }
}

async function handleStopWorker() {
  if (confirm('确定要停止 Worker 吗？')) {
    await operationsApi.stopWorker()
    await refreshAll()
  }
}

async function handleClearQueue() {
  if (confirm('确定要清空队列吗？所有排队中的任务将被移除。')) {
    await operationsApi.clearQueue()
    await refreshAll()
  }
}

function formatUptime(seconds: number | null): string {
  if (!seconds) return '-'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

function formatTime(iso: string | null): string {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

onMounted(() => {
  refreshAll()
  refreshInterval = setInterval(refreshAll, 5000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">运行监控面板</h1>
        <p class="text-sm text-gray-500 mt-1">Worker 守护进程状态与任务队列监控</p>
      </div>
      <Button variant="ghost" size="sm" :loading="refreshing" @click="refreshAll">
        <svg class="w-4 h-4 mr-1" :class="{ 'animate-spin': refreshing }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        刷新
      </Button>
    </div>

    <!-- Status Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">守护进程</p>
            <p class="text-2xl font-bold mt-1" :class="{
              'text-green-600': workerStatus?.status === 'online',
              'text-yellow-600': workerStatus?.status === 'stale',
              'text-gray-400': workerStatus?.status === 'offline'
            }">{{ statusLabel(workerStatus?.status || 'offline') }}</p>
          </div>
          <div :class="['w-3 h-3 rounded-full', statusDotClass(workerStatus?.status || 'offline')]" />
        </div>
        <p v-if="workerStatus?.last_heartbeat_seconds_ago" class="text-xs text-gray-400 mt-2">
          最后心跳: {{ workerStatus.last_heartbeat_seconds_ago }}s 前
        </p>
      </Card>

      <Card>
        <div>
          <p class="text-sm text-gray-500">排队中</p>
          <p class="text-2xl font-bold text-yellow-600 mt-1">{{ queueStats?.queued || 0 }}</p>
        </div>
      </Card>

      <Card>
        <div>
          <p class="text-sm text-gray-500">今日完成</p>
          <p class="text-2xl font-bold text-green-600 mt-1">{{ queueStats?.completed_today || 0 }}</p>
        </div>
      </Card>

      <Card>
        <div>
          <p class="text-sm text-gray-500">今日失败</p>
          <p class="text-2xl font-bold text-red-600 mt-1">{{ queueStats?.failed_today || 0 }}</p>
        </div>
        <p v-if="queueStats?.success_rate !== undefined" class="text-xs text-gray-400 mt-2">
          成功率: {{ (queueStats.success_rate * 100).toFixed(0) }}%
        </p>
      </Card>
    </div>

    <!-- Main Grid: Task Queue + Worker Details -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Task Queue (2/3) -->
      <div class="lg:col-span-2">
        <Card :padding="false">
          <div class="px-4 py-3 border-b border-gray-200 flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900">任务队列</h3>
            <span class="text-sm text-gray-500">{{ tasks.length }} 个任务</span>
          </div>
          <div v-if="tasks.length === 0" class="p-8 text-center text-gray-500 text-sm">
            暂无任务
          </div>
          <div v-else class="divide-y divide-gray-100">
            <div
              v-for="task in tasks"
              :key="task.task_id"
              class="px-4 py-3 flex items-center justify-between hover:bg-gray-50"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div :class="['w-2.5 h-2.5 rounded-full flex-shrink-0', statusDotClass(task.status)]" />
                <div class="min-w-0">
                  <p class="text-sm font-medium text-gray-900 truncate">{{ task.task || '无任务描述' }}</p>
                  <p class="text-xs text-gray-400 font-mono truncate">
                    {{ task.task_id }}
                    <span v-if="task.agent_name" class="ml-2">· {{ task.agent_name }}</span>
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-3 flex-shrink-0">
                <span class="text-xs text-gray-400">{{ formatTime(task.created_at) }}</span>
                <Badge :variant="taskStatusVariant(task.status)">
                  {{ statusLabel(task.status) }}
                </Badge>
                <Button
                  v-if="task.status === 'queued' || task.status === 'processing'"
                  variant="danger"
                  size="sm"
                  @click="handleCancelTask(task.task_id)"
                >取消</Button>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <!-- Sidebar (1/3) -->
      <div class="space-y-4">
        <!-- Worker Details -->
        <Card>
          <h3 class="text-sm font-semibold text-gray-700 mb-3">守护进程详情</h3>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-500">Worker ID</span>
              <span class="text-gray-900 font-mono text-xs">{{ workerStatus?.worker_id || '-' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">运行时间</span>
              <span class="text-gray-900">{{ formatUptime(workerStatus?.uptime_seconds || null) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">启动时间</span>
              <span class="text-gray-900">{{ formatTime(workerStatus?.started_at || null) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">Redis 连接</span>
              <span class="text-gray-900 font-mono text-xs">{{ workerStatus?.redis_connection || '-' }}</span>
            </div>
          </div>
        </Card>

        <!-- Quick Actions -->
        <Card>
          <h3 class="text-sm font-semibold text-gray-700 mb-3">快捷操作</h3>
          <div class="space-y-2">
            <Button variant="secondary" class="w-full text-sm" size="sm" @click="handleRestartWorker">
              <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              重启 Worker
            </Button>
            <Button variant="secondary" class="w-full text-sm" size="sm" @click="handleClearQueue">
              <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              清空队列
            </Button>
            <Button variant="danger" class="w-full text-sm" size="sm" @click="handleStopWorker">
              <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
              </svg>
              停止 Worker
            </Button>
          </div>
        </Card>

        <!-- Queue Stats -->
        <Card>
          <h3 class="text-sm font-semibold text-gray-700 mb-3">队列统计</h3>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-500">排队中</span>
              <span class="text-yellow-600 font-semibold">{{ queueStats?.queued || 0 }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">处理中</span>
              <span class="text-blue-600 font-semibold">{{ queueStats?.processing || 0 }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">今日完成</span>
              <span class="text-green-600 font-semibold">{{ queueStats?.completed_today || 0 }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">今日失败</span>
              <span class="text-red-600 font-semibold">{{ queueStats?.failed_today || 0 }}</span>
            </div>
            <div class="flex justify-between pt-2 border-t border-gray-200">
              <span class="text-gray-500">成功率</span>
              <span class="font-semibold" :class="queueStats && queueStats.success_rate >= 0.9 ? 'text-green-600' : 'text-red-600'">
                {{ queueStats ? (queueStats.success_rate * 100).toFixed(0) + '%' : '0%' }}
              </span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>
