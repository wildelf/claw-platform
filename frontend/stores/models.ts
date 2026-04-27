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

  async function getModel(id: string): Promise<ModelConfig | null> {
    try {
      return await modelsApi.get(id)
    } catch {
      return null
    }
  }

  async function updateModel(id: string, data: Partial<ModelConfig>): Promise<ModelConfig> {
    loading.value = true
    error.value = null
    try {
      const model = await modelsApi.update(id, data)
      const index = models.value.findIndex(m => m.id === id)
      if (index !== -1) {
        models.value[index] = model
      }
      return model
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update model'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteModel(id: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await modelsApi.delete(id)
      models.value = models.value.filter(m => m.id !== id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete model'
      throw e
    } finally {
      loading.value = false
    }
  }

  return { models, loading, error, fetchModels, getModel, createModel, updateModel, deleteModel }
})