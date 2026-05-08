import client from './client'

export interface ConversationMemory {
  id: string
  agent_id: string
  user_input: string
  agent_output: string
  summary: string
  created_at: string
}

export const conversationMemoriesApi = {
  async list(agentId: string, limit = 10): Promise<ConversationMemory[]> {
    const { data } = await client.get('/conversation-memories', { params: { agent_id: agentId, limit } })
    return data
  },

  async create(agentId: string, userInput: string, agentOutput: string, sessionId?: string): Promise<ConversationMemory> {
    const { data } = await client.post('/conversation-memories', {
      agent_id: agentId,
      user_input: userInput,
      agent_output: agentOutput,
      session_id: sessionId,
    })
    return data
  },

  async delete(id: string): Promise<void> {
    await client.delete(`/conversation-memories/${id}`)
  },

  async deleteByAgent(agentId: string): Promise<void> {
    await client.delete('/conversation-memories', { params: { agent_id: agentId } })
  },
}