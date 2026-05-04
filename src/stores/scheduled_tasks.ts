import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ScheduledTask } from '@/types'
import { scheduledTasksApi } from '@/api/scheduled_tasks'

export const useScheduledTasksStore = defineStore('scheduled_tasks', () => {
  const tasks = ref<ScheduledTask[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchTasks(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      tasks.value = await scheduledTasksApi.list()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch tasks'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createTask(data: Partial<ScheduledTask>): Promise<ScheduledTask> {
    loading.value = true
    error.value = null
    try {
      const task = await scheduledTasksApi.create(data)
      tasks.value.push(task)
      return task
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create task'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateTask(id: string, data: Partial<ScheduledTask>): Promise<ScheduledTask> {
    loading.value = true
    error.value = null
    try {
      const task = await scheduledTasksApi.update(id, data)
      const index = tasks.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tasks.value[index] = task
      }
      return task
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update task'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteTask(id: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await scheduledTasksApi.delete(id)
      tasks.value = tasks.value.filter(t => t.id !== id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete task'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function triggerTask(id: string): Promise<void> {
    try {
      await scheduledTasksApi.trigger(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to trigger task'
      throw e
    }
  }

  return {
    tasks,
    loading,
    error,
    fetchTasks,
    createTask,
    updateTask,
    deleteTask,
    triggerTask
  }
})