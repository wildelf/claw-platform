<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Input from '@/components/ui/Input.vue'
import { useEmployeeProfilesStore } from '@/stores/employeeProfiles'

const route = useRoute()
const router = useRouter()
const employeeProfilesStore = useEmployeeProfilesStore()

const profileId = route.params.id as string

const form = ref({
  name: '',
  role: '',
  goal: '',
  backstory: '',
  personality: '',
  constraints: '',
  working_rules: ''
})

const loading = ref(false)
const fetching = ref(true)
const error = ref<string | null>(null)
const notFound = ref(false)

onMounted(async () => {
  await employeeProfilesStore.fetchProfile(profileId)
  fetching.value = false
  const profile = employeeProfilesStore.currentProfile
  if (profile) {
    form.value.name = profile.name
    form.value.role = profile.role
    form.value.goal = profile.goal || ''
    form.value.backstory = profile.backstory || ''
    form.value.personality = profile.personality || ''
    form.value.constraints = profile.constraints || ''
    form.value.working_rules = profile.working_rules || ''
  } else {
    notFound.value = true
  }
})

async function handleSubmit() {
  if (!form.value.name.trim()) {
    error.value = 'Name is required'
    return
  }
  if (!form.value.role.trim()) {
    error.value = 'Role is required'
    return
  }

  loading.value = true
  error.value = null

  try {
    await employeeProfilesStore.updateProfile(profileId, form.value)
    router.push(`/employee-profiles/${profileId}`)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to update profile'
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push(`/employee-profiles/${profileId}`)
}
</script>

<template>
  <div class="flex min-h-[calc(100vh-3.5rem)]">
    <main class="flex-1 p-6 max-w-3xl mx-auto w-full">
      <!-- Header -->
      <div class="flex items-center gap-4 mb-6">
        <button
          class="text-sm text-text-muted hover:text-text-primary transition flex items-center gap-1"
          @click="handleCancel"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
          Back
        </button>
        <div>
          <h1 class="text-2xl font-bold text-text-primary">Edit Employee Profile</h1>
          <p class="text-text-secondary text-sm">Update the digital employee identity</p>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="fetching" class="text-center py-12">
        <p class="text-text-muted">Loading profile...</p>
      </div>

      <!-- Not Found State -->
      <div v-else-if="notFound" class="text-center py-12">
        <p class="text-red-400 mb-4">Profile not found</p>
        <button class="btn-primary text-white px-4 py-2 rounded-lg" @click="router.push('/employee-profiles')">
          Back to Profiles
        </button>
      </div>

      <!-- Form Card -->
      <template v-else>
        <div class="bg-bg-card border border-border-primary rounded-xl p-6">
          <form @submit.prevent="handleSubmit" class="space-y-5">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-2">Name *</label>
                <Input v-model="form.name" placeholder="e.g., Data Analyst" />
              </div>
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-2">Role *</label>
                <Input v-model="form.role" placeholder="e.g., Senior Data Analyst" />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-text-secondary mb-2">Goal *</label>
              <Input v-model="form.goal" placeholder="e.g., Analyze data and generate insights" />
            </div>

            <div>
              <label class="block text-sm font-medium text-text-secondary mb-2">Backstory</label>
              <textarea
                v-model="form.backstory"
                rows="3"
                class="w-full px-4 py-2.5 bg-bg-tertiary border border-border-primary rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-primary resize-none"
                placeholder="Background and experience..."
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-text-secondary mb-2">Personality</label>
              <textarea
                v-model="form.personality"
                rows="2"
                class="w-full px-4 py-2.5 bg-bg-tertiary border border-border-primary rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-primary resize-none"
                placeholder="e.g., Detail-oriented, asks clarifying questions"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-text-secondary mb-2">Constraints</label>
              <textarea
                v-model="form.constraints"
                rows="3"
                class="w-full px-4 py-2.5 bg-bg-tertiary border border-border-primary rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-primary resize-none code-editor"
                placeholder="- Never modify production data&#10;- Do not send external notifications without approval"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-text-secondary mb-2">Working Rules</label>
              <textarea
                v-model="form.working_rules"
                rows="3"
                class="w-full px-4 py-2.5 bg-bg-tertiary border border-border-primary rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-primary resize-none code-editor"
                placeholder="- Validate data quality before analysis&#10;- Report anomalies clearly"
              />
            </div>

            <!-- Error Alert -->
            <div v-if="error" class="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
              <p class="text-red-400 text-sm">{{ error }}</p>
            </div>

            <div class="flex gap-3 pt-2">
              <button
                type="submit"
                class="btn-primary text-white px-6 py-2 rounded-lg font-medium"
                :disabled="loading"
              >
                {{ loading ? 'Saving...' : 'Save Changes' }}
              </button>
              <button
                type="button"
                class="bg-bg-tertiary hover:bg-border-primary text-text-primary px-6 py-2 rounded-lg font-medium transition border border-border-primary"
                @click="handleCancel"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </template>
    </main>
  </div>
</template>
