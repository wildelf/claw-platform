import client from './client'

export interface ConversationMemory {
  id: string
  agent_id: string
  session_id: string
  user_input: string
  agent_output: string
  summary: string
  created_at: string
}

export const conversationMemoriesApi = {
  async list(agentId: string, sessionId: string, limit = 10): Promise<ConversationMemory[]> {
    const { data } = await client.get('/conversation-memories', { params: { agent_id: agentId, session_id: sessionId, limit } })
    return data
  },

  async create(agentId: string, sessionId: string, userInput: string, agentOutput: string): Promise<ConversationMemory> {
    const { data } = await client.post('/conversation-memories', {
      agent_id: agentId,
      session_id: sessionId,
      user_input: userInput,
      agent_output: agentOutput,
    })
    return data
  },

  async delete(id: string): Promise<void> {
    await client.delete(`/conversation-memories/${id}`)
  },

  async deleteBySession(agentId: string, sessionId: string): Promise<void> {
    await client.delete('/conversation-memories', { params: { agent_id: agentId, session_id: sessionId } })
  },
}
