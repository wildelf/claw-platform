import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Skill } from '@/types'
import { skillsApi } from '@/api/skills'

export const useSkillsStore = defineStore('skills', () => {
  const skills = ref<Skill[]>([])
  const currentSkill = ref<Skill | null>(null)
  const files = ref<Map<string, Record<string, string>>>(new Map())
  const loading = ref(false)

  async function fetchSkills(): Promise<void> {
    loading.value = true
    try {
      skills.value = await skillsApi.getSkills()
    } finally {
      loading.value = false
    }
  }

  async function fetchSkill(id: string): Promise<void> {
    loading.value = true
    try {
      currentSkill.value = await skillsApi.getSkill(id)
    } finally {
      loading.value = false
    }
  }

  async function fetchSkillFiles(id: string): Promise<Record<string, string>> {
    const skillFiles = await skillsApi.getSkillFiles(id)
    files.value.set(id, skillFiles)
    return skillFiles
  }

  return {
    skills,
    currentSkill,
    files,
    loading,
    fetchSkills,
    fetchSkill,
    fetchSkillFiles
  }
})