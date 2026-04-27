import client from './client'
import type { Agent } from '@/types'

export const agentsApi = {
  async list(): Promise<Agent[]> {
    const { data } = await client.get('/agents')
    return data
  },

  async get(id: string): Promise<Agent> {
    const { data } = await client.get(`/agents/${id}`)
    return data
  },

  async create(agent: Partial<Agent>): Promise<Agent> {
    const { data } = await client.post('/agents', agent)
    return data
  },

  async update(id: string, agent: Partial<Agent>): Promise<Agent> {
    const { data } = await client.put(`/agents/${id}`, agent)
    return data
  },

  async delete(id: string): Promise<void> {
    await client.delete(`/agents/${id}`)
  },

  async run(id: string, task: string): Promise<unknown> {
    const { data } = await client.post(`/agents/${id}/run`, { task })
    return data
  }
}