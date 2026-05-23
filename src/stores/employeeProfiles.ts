import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { EmployeeProfile } from '@/types'
import { employeeProfilesApi } from '@/api/employeeProfiles'

export const useEmployeeProfilesStore = defineStore('employeeProfiles', () => {
  const profiles = ref<EmployeeProfile[]>([])
  const currentProfile = ref<EmployeeProfile | null>(null)
  const files = ref<string[]>([])
  const fileContent = ref<{ filename: string; content: string } | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchProfiles() {
    loading.value = true
    error.value = null
    try {
      profiles.value = await employeeProfilesApi.list()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch profiles'
    } finally {
      loading.value = false
    }
  }

  async function createProfile(data: Partial<EmployeeProfile>) {
    return await employeeProfilesApi.create(data)
  }

  async function fetchProfile(id: string) {
    loading.value = true
    error.value = null
    try {
      currentProfile.value = await employeeProfilesApi.get(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch profile'
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(id: string, data: Partial<EmployeeProfile>) {
    return await employeeProfilesApi.update(id, data)
  }

  async function deleteProfile(id: string) {
    return await employeeProfilesApi.delete(id)
  }

  async function fetchProfileFiles(id: string) {
    loading.value = true
    error.value = null
    try {
      const result = await employeeProfilesApi.listFiles(id)
      files.value = result.files
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch files'
    } finally {
      loading.value = false
    }
  }

  async function getProfileFileContent(profileId: string, filename: string) {
    loading.value = true
    error.value = null
    try {
      fileContent.value = await employeeProfilesApi.getFile(profileId, filename)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch file content'
    } finally {
      loading.value = false
    }
  }

  async function updateProfileFileContent(profileId: string, filename: string, content: string) {
    return await employeeProfilesApi.updateFile(profileId, filename, content)
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
