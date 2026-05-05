import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { LogEntry } from '@/api/logs'
import { logsApi } from '@/api/logs'

export const useLogsStore = defineStore('logs', () => {
  const entries = ref<LogEntry[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function queryLogs(params: {
    agent_id?: string
    session_id?: string
    action_type?: string
    tool_name?: string
    offset?: number
    limit?: number
  } = {}): Promise<void> {
    loading.value = true
    error.value = null
    try {
      entries.value = await logsApi.query(params)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch logs'
      throw e
    } finally {
      loading.value = false
    }
  }

  function clearLogs(): void {
    entries.value = []
    error.value = null
  }

  return {
    entries,
    loading,
    error,
    queryLogs,
    clearLogs
  }
})
