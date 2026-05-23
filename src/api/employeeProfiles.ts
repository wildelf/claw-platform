import client from './client'
import type { EmployeeProfile } from '@/types'

export const employeeProfilesApi = {
  async list(): Promise<EmployeeProfile[]> {
    const { data } = await client.get('/employee-profiles')
    return data
  },

  async get(id: string): Promise<EmployeeProfile> {
    const { data } = await client.get(`/employee-profiles/${id}`)
    return data
  },

  async create(profile: Partial<EmployeeProfile>): Promise<{ id: string; git_path: string }> {
    const { data } = await client.post('/employee-profiles', profile)
    return data
  },

  async update(id: string, profile: Partial<EmployeeProfile>): Promise<{ id: string }> {
    const { data } = await client.put(`/employee-profiles/${id}`, profile)
    return data
  },

  async delete(id: string): Promise<{ deleted: boolean }> {
    const { data } = await client.delete(`/employee-profiles/${id}`)
    return data
  },

  async listFiles(id: string): Promise<{ files: string[] }> {
    const { data } = await client.get(`/employee-profiles/${id}/files`)
    return data
  },

  async getFile(profileId: string, filename: string): Promise<{ filename: string; content: string }> {
    const { data } = await client.get(`/employee-profiles/${profileId}/files/${filename}`)
    return data
  },

  async updateFile(profileId: string, filename: string, content: string): Promise<{ updated: boolean }> {
    const { data } = await client.put(`/employee-profiles/${profileId}/files/${filename}/content`, { content })
    return data
  },
}
