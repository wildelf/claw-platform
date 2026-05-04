import client from './client'
import type { ScheduledTask } from '@/types'

export const scheduledTasksApi = {
  async list(): Promise<ScheduledTask[]> {
    const { data } = await client.get('/scheduled-tasks')
    return data
  },

  async get(id: string): Promise<ScheduledTask> {
    const { data } = await client.get(`/scheduled-tasks/${id}`)
    return data
  },

  async create(task: Partial<ScheduledTask>): Promise<ScheduledTask> {
    const { data } = await client.post('/scheduled-tasks', task)
    return data
  },

  async update(id: string, task: Partial<ScheduledTask>): Promise<ScheduledTask> {
    const { data } = await client.put(`/scheduled-tasks/${id}`, task)
    return data
  },

  async delete(id: string): Promise<void> {
    await client.delete(`/scheduled-tasks/${id}`)
  },

  async trigger(id: string): Promise<void> {
    await client.post(`/scheduled-tasks/${id}/trigger`)
  }
}