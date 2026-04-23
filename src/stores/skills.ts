import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Skill } from '@/types'
import { skillsApi } from '@/api/skills'

export const useSkillsStore = defineStore('skills', () => {
  const skills = ref<Skill[]>([])
  const currentSkill = ref<Skill | null>(null)
  const files = ref<Map<string, Record<string, string>>>(new Map())
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchSkills(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      skills.value = await skillsApi.list()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch skills'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchSkill(id: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      currentSkill.value = await skillsApi.get(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch skill'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchSkillFiles(id: string): Promise<Record<string, string>> {
    error.value = null
    try {
      const skillFiles = await skillsApi.getFiles(id)
      files.value.set(id, skillFiles)
      return skillFiles
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch skill files'
      throw e
    }
  }

  return {
    skills,
    currentSkill,
    files,
    loading,
    error,
    fetchSkills,
    fetchSkill,
    fetchSkillFiles,
    async updateSkill(id: string, data: Partial<Skill>): Promise<Skill> {
      loading.value = true
      error.value = null
      try {
        const skill = await skillsApi.update(id, data)
        const index = skills.value.findIndex(s => s.id === id)
        if (index !== -1) {
          skills.value[index] = skill
        }
        if (currentSkill.value?.id === id) {
          currentSkill.value = skill
        }
        return skill
      } catch (e) {
        error.value = e instanceof Error ? e.message : 'Failed to update skill'
        throw e
      } finally {
        loading.value = false
      }
    }
  }
})