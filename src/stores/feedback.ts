import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { FeedbackEvent } from '@/types'
import { feedbackApi } from '@/api/feedback'

export const useFeedbackStore = defineStore('feedback', () => {
  const feedbackList = ref<FeedbackEvent[]>([])
  const currentFeedback = ref<FeedbackEvent | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchFeedback(skillId?: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      feedbackList.value = await feedbackApi.list(skillId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch feedback'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchFeedbackItem(id: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      currentFeedback.value = await feedbackApi.get(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch feedback'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createFeedback(data: Partial<FeedbackEvent>): Promise<FeedbackEvent> {
    loading.value = true
    error.value = null
    try {
      const feedback = await feedbackApi.create(data)
      feedbackList.value.unshift(feedback)
      return feedback
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create feedback'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    feedbackList,
    currentFeedback,
    loading,
    error,
    fetchFeedback,
    fetchFeedbackItem,
    createFeedback
  }
})
