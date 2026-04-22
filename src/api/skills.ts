import client from './client'
import type { Skill } from '@/types'

export const skillsApi = {
  async list(): Promise<Skill[]> {
    const { data } = await client.get('/skills')
    return data
  },

  async get(id: string): Promise<Skill> {
    const { data } = await client.get(`/skills/${id}`)
    return data
  },

  async create(skill: Partial<Skill>): Promise<Skill> {
    const { data } = await client.post('/skills', skill)
    return data
  },

  async update(id: string, skill: Partial<Skill>): Promise<Skill> {
    const { data } = await client.put(`/skills/${id}`, skill)
    return data
  },

  async delete(id: string): Promise<void> {
    await client.delete(`/skills/${id}`)
  },

  async getFiles(id: string): Promise<Record<string, string>> {
    const { data } = await client.get(`/skills/${id}/files`)
    return data
  },

  async saveFile(id: string, filename: string, content: string): Promise<void> {
    await client.post(`/skills/${id}/files`, { filename, content })
  }
}