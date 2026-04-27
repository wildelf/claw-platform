import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Tool } from '@/types'
import { toolsApi } from '@/api/tools'

export const useToolsStore = defineStore('tools', () => {
  const tools = ref<Tool[]>([])
  const currentTool = ref<Tool | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchTools(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      tools.value = await toolsApi.list()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch tools'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchTool(id: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      currentTool.value = await toolsApi.get(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch tool'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createTool(data: Partial<Tool>): Promise<Tool> {
    loading.value = true
    error.value = null
    try {
      const tool = await toolsApi.create(data)
      tools.value.push(tool)
      return tool
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create tool'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateTool(id: string, data: Partial<Tool>): Promise<Tool> {
    loading.value = true
    error.value = null
    try {
      const tool = await toolsApi.update(id, data)
      const index = tools.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tools.value[index] = tool
      }
      if (currentTool.value?.id === id) {
        currentTool.value = tool
      }
      return tool
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update tool'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteTool(id: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await toolsApi.delete(id)
      tools.value = tools.value.filter(t => t.id !== id)
      if (currentTool.value?.id === id) {
        currentTool.value = null
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete tool'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    tools,
    currentTool,
    loading,
    error,
    fetchTools,
    fetchTool,
    createTool,
    updateTool,
    deleteTool
  }
})
