import client from './client'
import type { FeedbackEvent } from '@/types'

export const feedbackApi = {
  async list(skillId?: string): Promise<FeedbackEvent[]> {
    const params = skillId ? { skill_id: skillId } : {}
    const { data } = await client.get('/feedback', { params })
    return data
  },

  async get(id: string): Promise<FeedbackEvent> {
    const { data } = await client.get(`/feedback/${id}`)
    return data
  },

  async create(feedback: Partial<FeedbackEvent>): Promise<FeedbackEvent> {
    const { data } = await client.post('/feedback', feedback)
    return data
  }
}
