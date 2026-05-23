import { defineStore } from 'pinia'
import { ref } from 'vue'
import employeeProfilesApi, { type EmployeeProfile, type EmployeeProfileSummary, type CreateProfilePayload, type UpdateProfilePayload } from '@/api/employeeProfiles'

export const useEmployeeProfilesStore = defineStore('employeeProfiles', () => {
  const profiles = ref<EmployeeProfileSummary[]>([])
  const currentProfile = ref<EmployeeProfile | null>(null)
  const files = ref<string[]>([])
  const fileContent = ref<string>('')
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchProfiles() {
    loading.value = true
    error.value = null
    try {
      profiles.value = await employeeProfilesApi.list()
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch profiles'
    } finally {
      loading.value = false
    }
  }

  async function createProfile(data: CreateProfilePayload) {
    loading.value = true
    error.value = null
    try {
      const result = await employeeProfilesApi.create(data)
      return result
    } catch (e: any) {
      error.value = e.message || 'Failed to create profile'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchProfile(id: string) {
    loading.value = true
    error.value = null
    try {
      currentProfile.value = await employeeProfilesApi.get(id)
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch profile'
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(id: string, data: UpdateProfilePayload) {
    loading.value = true
    error.value = null
    try {
      return await employeeProfilesApi.update(id, data)
    } catch (e: any) {
      error.value = e.message || 'Failed to update profile'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteProfile(id: string) {
    loading.value = true
    error.value = null
    try {
      return await employeeProfilesApi.delete(id)
    } catch (e: any) {
      error.value = e.message || 'Failed to delete profile'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchProfileFiles(id: string) {
    loading.value = true
    error.value = null
    try {
      const res = await employeeProfilesApi.listFiles(id)
      files.value = res.files
    } catch (e: any) {
      error.value = e.message || 'Failed to list files'
    } finally {
      loading.value = false
    }
  }

  async function getProfileFileContent(profileId: string, filename: string) {
    loading.value = true
    error.value = null
    try {
      const res = await employeeProfilesApi.getFile(profileId, filename)
      fileContent.value = res.content
      return res.content
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch file content'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateProfileFileContent(profileId: string, filename: string, content: string) {
    loading.value = true
    error.value = null
    try {
      return await employeeProfilesApi.updateFile(profileId, filename, content)
    } catch (e: any) {
      error.value = e.message || 'Failed to update file'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    profiles,
    currentProfile,
    files,
    fileContent,
    loading,
    error,
    fetchProfiles,
    createProfile,
    fetchProfile,
    updateProfile,
    deleteProfile,
    fetchProfileFiles,
    getProfileFileContent,
    updateProfileFileContent,
  }
})
