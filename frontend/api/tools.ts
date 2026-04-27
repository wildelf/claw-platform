import client from './client'
import type { Tool } from '@/types'

export const toolsApi = {
  async list(): Promise<Tool[]> {
    const { data } = await client.get('/tools')
    return data
  },

  async get(id: string): Promise<Tool> {
    const { data } = await client.get(`/tools/${id}`)
    return data
  },

  async create(tool: Partial<Tool>): Promise<Tool> {
    const { data } = await client.post('/tools', tool)
    return data
  },

  async update(id: string, tool: Partial<Tool>): Promise<Tool> {
    const { data } = await client.put(`/tools/${id}`, tool)
    return data
  },

  async delete(id: string): Promise<void> {
    await client.delete(`/tools/${id}`)
  }
}
