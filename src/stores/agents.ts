import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Agent } from '@/types'
import { agentsApi } from '@/api/agents'

export const useAgentsStore = defineStore('agents', () => {
  const agents = ref<Agent[]>([])
  const currentAgent = ref<Agent | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAgents(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      agents.value = await agentsApi.getAgents()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch agents'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchAgent(id: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      currentAgent.value = await agentsApi.getAgent(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch agent'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createAgent(data: Partial<Agent>): Promise<Agent> {
    loading.value = true
    error.value = null
    try {
      const agent = await agentsApi.createAgent(data)
      agents.value.push(agent)
      return agent
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create agent'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateAgent(id: string, data: Partial<Agent>): Promise<Agent> {
    loading.value = true
    error.value = null
    try {
      const agent = await agentsApi.updateAgent(id, data)
      const index = agents.value.findIndex(a => a.id === id)
      if (index !== -1) {
        agents.value[index] = agent
      }
      if (currentAgent.value?.id === id) {
        currentAgent.value = agent
      }
      return agent
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update agent'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteAgent(id: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await agentsApi.deleteAgent(id)
      agents.value = agents.value.filter(a => a.id !== id)
      if (currentAgent.value?.id === id) {
        currentAgent.value = null
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete agent'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    agents,
    currentAgent,
    loading,
    error,
    fetchAgents,
    fetchAgent,
    createAgent,
    updateAgent,
    deleteAgent
  }
})