import type { Skill } from '@/types'

export const skillsApi = {
  async getSkills(): Promise<Skill[]> {
    // TODO: implement actual API call
    return []
  },

  async getSkill(id: string): Promise<Skill | null> {
    // TODO: implement actual API call
    return null
  },

  async getSkillFiles(id: string): Promise<Record<string, string>> {
    // TODO: implement actual API call
    return {}
  }
}