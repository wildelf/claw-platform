import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Agent } from '@/types'
import { agentsApi } from '@/api/agents'

export const useAgentsStore = defineStore('agents', () => {
  const agents = ref<Agent[]>([])
  const currentAgent = ref<Agent | null>(null)
  const loading = ref(false)

  async function fetchAgents(): Promise<void> {
    loading.value = true
    try {
      agents.value = await agentsApi.getAgents()
    } finally {
      loading.value = false
    }
  }

  async function fetchAgent(id: string): Promise<void> {
    loading.value = true
    try {
      currentAgent.value = await agentsApi.getAgent(id)
    } finally {
      loading.value = false
    }
  }

  async function createAgent(data: Partial<Agent>): Promise<Agent> {
    loading.value = true
    try {
      const agent = await agentsApi.createAgent(data)
      agents.value.push(agent)
      return agent
    } finally {
      loading.value = false
    }
  }

  async function updateAgent(id: string, data: Partial<Agent>): Promise<Agent> {
    loading.value = true
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
    } finally {
      loading.value = false
    }
  }

  async function deleteAgent(id: string): Promise<void> {
    loading.value = true
    try {
      await agentsApi.deleteAgent(id)
      agents.value = agents.value.filter(a => a.id !== id)
      if (currentAgent.value?.id === id) {
        currentAgent.value = null
      }
    } finally {
      loading.value = false
    }
  }

  return {
    agents,
    currentAgent,
    loading,
    fetchAgents,
    fetchAgent,
    createAgent,
    updateAgent,
    deleteAgent
  }
})