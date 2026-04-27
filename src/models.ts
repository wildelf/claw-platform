import client from './client'
import type { ModelConfig } from '@/types'

export const modelsApi = {
  async list(): Promise<ModelConfig[]> {
    const { data } = await client.get('/models')
    return data
  },

  async get(id: string): Promise<ModelConfig> {
    const { data } = await client.get(`/models/${id}`)
    return data
  },

  async create(config: Partial<ModelConfig>): Promise<ModelConfig> {
    const { data } = await client.post('/models', config)
    return data
  },

  async update(id: string, config: Partial<ModelConfig>): Promise<ModelConfig> {
    const { data } = await client.put(`/models/${id}`, config)
    return data
  },

  async delete(id: string): Promise<void> {
    await client.delete(`/models/${id}`)
  }
}