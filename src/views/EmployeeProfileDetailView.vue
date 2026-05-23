<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Badge from '@/components/ui/Badge.vue'
import { useEmployeeProfilesStore } from '@/stores/employeeProfiles'

const route = useRoute()
const router = useRouter()
const employeeProfilesStore = useEmployeeProfilesStore()

const profileId = route.params.id as string
const profile = computed(() => employeeProfilesStore.currentProfile)

const activeTab = ref<'files' | 'constraints' | 'rules'>('files')
const selectedFile = ref<string | null>(null)
const fileContent = ref('')
const editingFile = ref(false)

onMounted(async () => {
  await employeeProfilesStore.fetchProfile(profileId)
  await employeeProfilesStore.fetchProfileFiles(profileId)
})

function getInitials(name: string): string {
  return name
    .split(' ')
    .map(w => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function getAvatarColor(name: string): string {
  const colors = [
    'from-blue-500 to-blue-600',
    'from-green-500 to-green-600',
    'from-purple-500 to-purple-600',
    'from-orange-500 to-orange-600',
    'from-pink-500 to-pink-600',
    'from-teal-500 to-teal-600',
    'from-indigo-500 to-indigo-600',
  ]
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'default' {
  switch (status) {
    case 'active': return 'success'
    case 'paused':
    case 'inactive': return 'warning'
    case 'error': return 'danger'
    default: return 'default'
  }
}

async function handleSelectFile(filename: string) {
  selectedFile.value = filename
  editingFile.value = false
  await employeeProfilesStore.getProfileFileContent(profileId, filename)
  fileContent.value = employeeProfilesStore.fileContent?.content || ''
}

async function handleSaveFile() {
  if (!selectedFile.value) return
  await employeeProfilesStore.updateProfileFileContent(profileId, selectedFile.value, fileContent.value)
  editingFile.value = false
  await employeeProfilesStore.getProfileFileContent(profileId, selectedFile.value)
  fileContent.value = employeeProfilesStore.fileContent?.content || ''
}

function handleEdit() {
  router.push(`/employee-profiles/${profileId}/edit`)
}

function handleBack() {
  router.push('/employee-profiles')
}
</script>

<template>
  <div class="flex min-h-[calc(100vh-3.5rem)]">
    <!-- Left Sidebar - Profile Info -->
    <aside class="w-72 bg-bg-secondary border-r border-border-primary p-5 flex-shrink-0 overflow-y-auto">
      <!-- Breadcrumb -->
      <button class="text-sm text-text-muted hover:text-text-primary transition mb-4 flex items-center gap-1" @click="handleBack">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        Back to Profiles
      </button>

      <div v-if="profile" class="space-y-5">
        <!-- Avatar + Name -->
        <div class="flex items-center gap-3">
          <div
            :class="['w-14 h-14 rounded-full flex items-center justify-center text-white text-xl font-bold bg-gradient-to-br', getAvatarColor(profile.name)]"
          >
            {{ getInitials(profile.name) }}
          </div>
          <div>
            <h2 class="text-lg font-semibold text-text-primary">{{ profile.name }}</h2>
            <Badge :variant="getStatusVariant(profile.status)">
              <span class="w-1.5 h-1.5 rounded-full" :class="{
                'bg-status-active': profile.status === 'active',
                'bg-status-paused': profile.status === 'paused' || profile.status === 'inactive',
                'bg-status-error': profile.status === 'error'
              }"></span>
              <span class="ml-1 capitalize">{{ profile.status }}</span>
            </Badge>
          </div>
        </div>

        <!-- Role -->
        <div>
          <div class="text-xs text-text-muted mb-1">Role</div>
          <div class="text-sm text-text-primary">{{ profile.role }}</div>
        </div>

        <!-- Goal -->
        <div>
          <div class="text-xs text-text-muted mb-1">Goal</div>
          <div class="text-sm text-text-secondary">{{ profile.goal || 'Not specified' }}</div>
        </div>

        <!-- Backstory -->
        <div v-if="profile.backstory">
          <div class="text-xs text-text-muted mb-1">Backstory</div>
          <div class="text-sm text-text-secondary whitespace-pre-wrap">{{ profile.backstory }}</div>
        </div>

        <!-- Personality -->
        <div v-if="profile.personality">
          <div class="text-xs text-text-muted mb-1">Personality</div>
          <div class="text-sm text-text-secondary whitespace-pre-wrap">{{ profile.personality }}</div>
        </div>

        <!-- Git Path -->
        <div>
          <div class="text-xs text-text-muted mb-1">Git Path</div>
          <div class="text-xs text-text-secondary font-mono bg-bg-tertiary px-2 py-1 rounded break-all">{{ profile.git_path }}</div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-2 pt-3 border-t border-border-primary">
          <button
            class="btn-primary text-white text-sm font-medium px-4 py-2 rounded-lg flex-1"
            @click="handleEdit"
          >
            Edit Profile
          </button>
          <button
            class="bg-bg-tertiary hover:bg-border-primary text-text-primary text-sm font-medium px-3 py-2 rounded-lg transition"
            @click="handleBack"
          >
            Back
          </button>
        </div>
      </div>

      <div v-else-if="employeeProfilesStore.loading" class="text-center py-8">
        <p class="text-text-muted text-sm">Loading profile...</p>
      </div>

      <div v-else class="text-center py-8">
        <p class="text-red-400 text-sm mb-3">Profile not found</p>
        <button class="btn-primary text-white px-4 py-2 rounded-lg text-sm" @click="handleBack">
          Back to Profiles
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-y-auto" v-if="profile">
      <!-- Tab Bar -->
      <div class="flex items-center gap-1 px-5 py-3 border-b border-border-primary bg-bg-secondary">
        <button
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition',
            activeTab === 'files' ? 'tab-active' : 'text-text-muted hover:text-text-primary hover:bg-bg-tertiary'
          ]"
          @click="activeTab = 'files'"
        >
          Files
        </button>
        <button
          v-if="profile.constraints"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition',
            activeTab === 'constraints' ? 'tab-active' : 'text-text-muted hover:text-text-primary hover:bg-bg-tertiary'
          ]"
          @click="activeTab = 'constraints'"
        >
          Constraints
        </button>
        <button
          v-if="profile.working_rules"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition',
            activeTab === 'rules' ? 'tab-active' : 'text-text-muted hover:text-text-primary hover:bg-bg-tertiary'
          ]"
          @click="activeTab = 'rules'"
        >
          Working Rules
        </button>
      </div>

      <!-- Files Tab -->
      <div v-if="activeTab === 'files'" class="p-5">
        <!-- File List -->
        <div class="mb-4">
          <h3 class="text-sm font-medium text-text-muted mb-3">Profile Files</h3>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="file in employeeProfilesStore.files"
              :key="file"
              :class="[
                'px-3 py-1.5 rounded-lg text-sm font-medium transition',
                selectedFile === file
                  ? 'bg-accent-primary/20 text-accent-light border border-accent-primary/30'
                  : 'bg-bg-tertiary border border-border-primary text-text-secondary hover:bg-border-primary'
              ]"
              @click="handleSelectFile(file)"
            >
              {{ file }}
            </button>
            <div v-if="employeeProfilesStore.files.length === 0" class="text-sm text-text-muted">
              No files found
            </div>
          </div>
        </div>

        <!-- File Content -->
        <div v-if="selectedFile" class="bg-bg-card border border-border-primary rounded-xl overflow-hidden">
          <!-- File Header -->
          <div class="flex items-center justify-between px-4 py-2.5 bg-bg-secondary border-b border-border-primary">
            <span class="text-sm font-medium text-text-primary font-mono">{{ selectedFile }}</span>
            <button
              v-if="!editingFile"
              class="text-sm text-text-muted hover:text-accent-primary transition"
              @click="editingFile = true"
            >
              Edit
            </button>
          </div>

          <!-- Editor / Preview -->
          <textarea
            v-if="editingFile"
            v-model="fileContent"
            rows="16"
            class="w-full px-4 py-3 code-editor text-sm text-text-primary bg-bg-card focus:outline-none resize-none"
          />
          <pre
            v-else
            class="px-4 py-3 code-editor text-sm text-text-secondary bg-bg-card whitespace-pre-wrap max-h-[32rem] overflow-y-auto"
          >{{ fileContent }}</pre>

          <!-- Save Actions -->
          <div v-if="editingFile" class="flex gap-2 px-4 py-2.5 bg-bg-secondary border-t border-border-primary">
            <button class="btn-primary text-white px-4 py-1.5 rounded-lg text-sm" @click="handleSaveFile">
              Save
            </button>
            <button
              class="bg-bg-tertiary hover:bg-border-primary text-text-primary px-4 py-1.5 rounded-lg text-sm transition"
              @click="editingFile = false"
            >
              Cancel
            </button>
          </div>
        </div>

        <div v-else class="text-center py-16 border border-border-primary border-dashed rounded-xl">
          <svg class="w-10 h-10 text-text-muted mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          <p class="text-text-muted text-sm">Select a file to view its content</p>
        </div>
      </div>

      <!-- Constraints Tab -->
      <div v-else-if="activeTab === 'constraints'" class="p-5">
        <h3 class="text-sm font-medium text-text-muted mb-3">Constraints</h3>
        <pre class="code-editor text-sm text-text-secondary bg-bg-card border border-border-primary rounded-xl p-4 whitespace-pre-wrap">{{ profile.constraints }}</pre>
      </div>

      <!-- Working Rules Tab -->
      <div v-else-if="activeTab === 'rules'" class="p-5">
        <h3 class="text-sm font-medium text-text-muted mb-3">Working Rules</h3>
        <pre class="code-editor text-sm text-text-secondary bg-bg-card border border-border-primary rounded-xl p-4 whitespace-pre-wrap">{{ profile.working_rules }}</pre>
      </div>
    </main>
  </div>
</template>
