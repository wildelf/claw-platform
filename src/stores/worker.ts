import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { QueuedTask } from '@/types'
import { queuedTasksApi } from '@/api/queuedTasks'

export const useWorkerStore = defineStore('worker', () => {
  const tasks = ref<QueuedTask[]>([])
  const currentTask = ref<QueuedTask | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Worker status
  const isRunning = ref(false)
  const lastHeartbeat = ref<string | null>(null)
  const workerId = ref<string>('worker:local')
  const redisConnected = ref(false)

  async function fetchWorkerStatus() {
    // TODO: Replace with actual API call when endpoint is available
    isRunning.value = true
    lastHeartbeat.value = new Date().toISOString()
  }

  async function fetchTasks() {
    // TODO: Replace with actual API call when endpoint is available
    loading.value = true
    try {
      // Placeholder - would call a real tasks list endpoint
    } finally {
      loading.value = false
    }
  }

  async function runQueuedTask(
    agentId: string,
    payload: {
      task: string
      user_input: string
      images: string[]
      model_config_id: string | null
      session_id?: string
    }
  ) {
    return await queuedTasksApi.runQueued(agentId, payload)
  }

  async function fetchTaskStatus(agentId: string, taskId: string): Promise<QueuedTask> {
    return await queuedTasksApi.getTaskStatus(agentId, taskId)
  }

  function startPolling(agentId: string, taskId: string, intervalMs = 5000) {
    const poll = async () => {
      try {
        const status = await queuedTasksApi.getTaskStatus(agentId, taskId)
        currentTask.value = status
        if (status.status !== 'completed' && status.status !== 'failed') {
          setTimeout(poll, intervalMs)
        }
      } catch (e) {
        error.value = e instanceof Error ? e.message : 'Failed to fetch task status'
      }
    }
    poll()
  }

  return {
    tasks,
    currentTask,
    loading,
    error,
    isRunning,
    lastHeartbeat,
    workerId,
    redisConnected,
    fetchWorkerStatus,
    fetchTasks,
    runQueuedTask,
    fetchTaskStatus,
    startPolling,
  }
})
