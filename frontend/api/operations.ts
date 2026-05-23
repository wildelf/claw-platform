import client from './client'

export interface WorkerStatus {
  worker_id: string | null
  status: 'online' | 'stale' | 'offline'
  last_heartbeat: string | null
  last_heartbeat_seconds_ago: number | null
  started_at: string | null
  uptime_seconds: number | null
  redis_connection: string
}

export interface QueueStats {
  queued: number
  processing: number
  completed_today: number
  failed_today: number
  success_rate: number
}

export interface TaskItem {
  task_id: string
  agent_id: string | null
  agent_name?: string
  task: string
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled'
  created_at: string | null
  started_at: string | null
  completed_at: string | null
  elapsed_seconds: number | null
  error: string | null
}

export interface TaskListResponse {
  tasks: TaskItem[]
  total: number
}

export default {
  getWorkerStatus(): Promise<WorkerStatus> {
    return client.get('/operations/worker/status').then(res => res.data)
  },

  getQueueStats(): Promise<QueueStats> {
    return client.get('/operations/queue/stats').then(res => res.data)
  },

  listTasks(params?: { status?: string; limit?: number }): Promise<TaskListResponse> {
    return client.get('/operations/tasks', { params }).then(res => res.data)
  },

  cancelTask(taskId: string): Promise<{ cancelled: boolean; task_id: string; message: string }> {
    return client.post(`/operations/tasks/${taskId}/cancel`).then(res => res.data)
  },

  restartWorker(): Promise<{ restarting: boolean; message: string }> {
    return client.post('/operations/worker/restart').then(res => res.data)
  },

  stopWorker(): Promise<{ stopping: boolean; message: string }> {
    return client.post('/operations/worker/stop').then(res => res.data)
  },

  clearQueue(): Promise<{ cleared_count: number; message: string }> {
    return client.post('/operations/queue/clear').then(res => res.data)
  },
}
