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

  async getFiles(id: string): Promise<string[]> {
    const { data } = await client.get(`/skills/${id}/files`)
    return data
  },

  async getFileContent(id: string, filename: string): Promise<string> {
    // Replace / with _SLASH_ to handle paths like scripts/image_processor.py
    const encodedFilename = filename.replace(/\//g, '_SLASH_')
    const { data } = await client.request({
      url: `/skills/${id}/files/${encodedFilename}`,
      method: 'GET',
      transformResponse: [(d) => d],
    })
    return data
  },

  async saveFile(id: string, filename: string, content: string): Promise<void> {
    await client.put(`/skills/${id}/files/${filename}/content`, { content })
  }
}