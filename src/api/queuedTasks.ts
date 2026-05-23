import client from './client'
import type { QueuedTask } from '@/types'

export const queuedTasksApi = {
  async runQueued(
    agentId: string,
    payload: {
      task: string
      user_input: string
      images: string[]
      model_config_id: string | null
      session_id?: string
    }
  ): Promise<{ task_id: string; status: string; message: string }> {
    const { data } = await client.post(`/agents/${agentId}/run?mode=queued`, payload)
    return data
  },

  async getTaskStatus(agentId: string, taskId: string): Promise<QueuedTask> {
    const { data } = await client.get(`/agents/${agentId}/tasks/${taskId}/status`)
    return data
  },
}
