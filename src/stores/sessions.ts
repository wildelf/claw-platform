import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Session } from '@/api/sessions'
import { sessionsApi } from '@/api/sessions'

export const useSessionsStore = defineStore('sessions', () => {
  const sessions = ref<Session[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchSessions(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      sessions.value = await sessionsApi.list()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch sessions'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createSession(agentId: string, name?: string): Promise<Session> {
    const session = await sessionsApi.create(agentId, name)
    sessions.value.unshift(session)
    return session
  }

  async function updateSession(id: string, name: string): Promise<void> {
    const updated = await sessionsApi.update(id, name)
    const idx = sessions.value.findIndex(s => s.id === id)
    if (idx !== -1) {
      sessions.value[idx] = updated
    }
  }

  async function deleteSession(id: string): Promise<void> {
    await sessionsApi.delete(id)
    sessions.value = sessions.value.filter(s => s.id !== id)
  }

  return {
    sessions,
    loading,
    error,
    fetchSessions,
    createSession,
    updateSession,
    deleteSession
  }
})