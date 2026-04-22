import type { Agent } from '@/types'

export const agentsApi = {
  async getAgents(): Promise<Agent[]> {
    // TODO: implement actual API call
    return []
  },

  async getAgent(id: string): Promise<Agent | null> {
    // TODO: implement actual API call
    return null
  },

  async createAgent(data: Partial<Agent>): Promise<Agent> {
    // TODO: implement actual API call
    return {} as Agent
  },

  async updateAgent(id: string, data: Partial<Agent>): Promise<Agent> {
    // TODO: implement actual API call
    return {} as Agent
  },

  async deleteAgent(id: string): Promise<void> {
    // TODO: implement actual API call
  }
}