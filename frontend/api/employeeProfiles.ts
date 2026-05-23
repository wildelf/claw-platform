import client from './client'

export interface EmployeeProfile {
  id: string
  name: string
  role: string
  goal: string
  backstory: string
  personality: string
  constraints: string
  working_rules: string
  status: 'active' | 'paused' | 'retired'
  git_path: string
}

export interface EmployeeProfileSummary {
  id: string
  name: string
  role: string
  goal: string
  status: string
  git_path: string
}

export interface CreateProfilePayload {
  name: string
  role?: string
  goal?: string
  backstory?: string
  personality?: string
  constraints?: string
  working_rules?: string
}

export interface UpdateProfilePayload {
  name?: string
  role?: string
  goal?: string
  backstory?: string
  personality?: string
  constraints?: string
  working_rules?: string
  status?: string
}

export default {
  list(): Promise<EmployeeProfileSummary[]> {
    return client.get('/employee-profiles').then(res => res.data)
  },

  get(id: string): Promise<EmployeeProfile> {
    return client.get(`/employee-profiles/${id}`).then(res => res.data)
  },

  create(data: CreateProfilePayload): Promise<{ id: string; git_path: string }> {
    return client.post('/employee-profiles', data).then(res => res.data)
  },

  update(id: string, data: UpdateProfilePayload): Promise<{ id: string }> {
    return client.put(`/employee-profiles/${id}`, data).then(res => res.data)
  },

  delete(id: string): Promise<{ deleted: boolean }> {
    return client.delete(`/employee-profiles/${id}`).then(res => res.data)
  },

  listFiles(id: string): Promise<{ files: string[] }> {
    return client.get(`/employee-profiles/${id}/files`).then(res => res.data)
  },

  getFile(profileId: string, filename: string): Promise<{ filename: string; content: string }> {
    return client.get(`/employee-profiles/${profileId}/files/${filename}`).then(res => res.data)
  },

  updateFile(profileId: string, filename: string, content: string): Promise<{ updated: boolean }> {
    return client.put(`/employee-profiles/${profileId}/files/${filename}/content`, { content }).then(res => res.data)
  },
}
