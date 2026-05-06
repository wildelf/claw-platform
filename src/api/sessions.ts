import client from './client'

export interface Session {
  id: string
  name: string
  agent_id: string
  created_at: string
  updated_at: string
  message_count: number
}

export const sessionsApi = {
  async list(): Promise<Session[]> {
    const { data } = await client.get('/sessions')
    return data
  },

  async get(id: string): Promise<Session> {
    const { data } = await client.get(`/sessions/${id}`)
    return data
  },

  async create(agentId: string, name?: string): Promise<Session> {
    const { data } = await client.post('/sessions', { agent_id: agentId, name })
    return data
  },

  async update(id: string, name: string): Promise<Session> {
    const { data } = await client.patch(`/sessions/${id}`, { name })
    return data
  },

  async delete(id: string): Promise<void> {
    await client.delete(`/sessions/${id}`)
  }
}