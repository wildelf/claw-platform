import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ModelConfig } from '@/types'
import { modelsApi } from '@/api/models'

export const useModelsStore = defineStore('models', () => {
  const models = ref<ModelConfig[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchModels(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      models.value = await modelsApi.list()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch models'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createModel(config: Partial<ModelConfig>): Promise<ModelConfig> {
    loading.value = true
    error.value = null
    try {
      const newModel = await modelsApi.create(config)
      models.value.push(newModel)
      return newModel
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create model'
      throw e
    } finally {
      loading.value = false
    }
  }

  return { models, loading, error, fetchModels, createModel }
})