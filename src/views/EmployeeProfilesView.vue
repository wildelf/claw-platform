<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Badge from '@/components/ui/Badge.vue'
import { useEmployeeProfilesStore } from '@/stores/employeeProfiles'

const router = useRouter()
const employeeProfilesStore = useEmployeeProfilesStore()

const searchQuery = ref('')
const statusFilter = ref('all')

const filteredProfiles = computed(() => {
  let result = employeeProfilesStore.profiles
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(p =>
      p.name.toLowerCase().includes(q) ||
      p.role.toLowerCase().includes(q)
    )
  }
  if (statusFilter.value !== 'all') {
    result = result.filter(p => p.status === statusFilter.value)
  }
  return result
})

const stats = computed(() => {
  const total = employeeProfilesStore.profiles.length
  const active = employeeProfilesStore.profiles.filter(p => p.status === 'active').length
  const paused = employeeProfilesStore.profiles.filter(p => p.status === 'paused' || p.status === 'inactive').length
  return { total, active, paused }
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

function handleView(profileId: string) {
  router.push(`/employee-profiles/${profileId}`)
}

function handleEdit(profileId: string) {
  router.push(`/employee-profiles/${profileId}/edit`)
}

async function handleDelete(profileId: string, profileName: string) {
  if (!confirm(`Delete employee profile "${profileName}"? This cannot be undone.`)) {
    return
  }
  try {
    await employeeProfilesStore.deleteProfile(profileId)
    await employeeProfilesStore.fetchProfiles()
  } catch (e) {
    alert('Failed to delete profile')
  }
}

onMounted(() => {
  employeeProfilesStore.fetchProfiles()
})
</script>

<template>
  <div class="flex min-h-[calc(100vh-3.5rem)]">
    <!-- Left Sidebar -->
    <aside class="w-64 bg-bg-secondary border-r border-border-primary p-4 flex-shrink-0">
      <!-- Create Button -->
      <router-link to="/employee-profiles/create" class="block">
        <button class="w-full btn-primary text-white font-medium py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 mb-6 transition">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          Create Profile
        </button>
      </router-link>

      <!-- Recent Employees -->
      <div class="mb-4">
        <h3 class="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">Recent</h3>
        <div class="space-y-1">
          <button
            v-for="profile in employeeProfilesStore.profiles.slice(0, 5)"
            :key="profile.id"
            @click="handleView(profile.id)"
            class="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-bg-tertiary transition text-left"
          >
            <div
              :class="['w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium bg-gradient-to-br', getAvatarColor(profile.name)]"
            >
              {{ getInitials(profile.name) }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-text-primary truncate">{{ profile.name }}</div>
              <div class="text-xs text-text-muted">{{ profile.status }}</div>
            </div>
          </button>
          <div v-if="employeeProfilesStore.profiles.length === 0" class="text-xs text-text-muted px-3">
            No profiles yet
          </div>
        </div>
      </div>

      <!-- Quick Stats -->
      <div class="bg-bg-tertiary rounded-lg p-4 border border-border-primary">
        <h3 class="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">Stats</h3>
        <div class="space-y-3">
          <div>
            <div class="text-2xl font-bold text-text-primary">{{ stats.total }}</div>
            <div class="text-xs text-text-secondary">Total Profiles</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-status-active">{{ stats.active }}</div>
            <div class="text-xs text-text-secondary">Active</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-status-paused">{{ stats.paused }}</div>
            <div class="text-xs text-text-secondary">Paused</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 p-6 overflow-y-auto">
      <!-- Page Header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-text-primary mb-1">Employee Profiles</h1>
          <p class="text-text-secondary">Manage your AI digital employees, define identities, skills, and permissions</p>
        </div>
        <div class="flex items-center gap-3">
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search employees..."
              class="bg-bg-tertiary border border-border-primary rounded-lg pl-10 pr-4 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-primary w-64"
            />
            <svg class="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
          </div>
          <select
            v-model="statusFilter"
            class="bg-bg-tertiary border border-border-primary rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent-primary"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="error">Error</option>
          </select>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="employeeProfilesStore.loading" class="text-center py-12">
        <p class="text-text-secondary">Loading profiles...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="employeeProfilesStore.error" class="text-center py-12">
        <p class="text-red-400 mb-4">{{ employeeProfilesStore.error }}</p>
        <button class="btn-primary text-white px-4 py-2 rounded-lg" @click="employeeProfilesStore.fetchProfiles()">
          Retry
        </button>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredProfiles.length === 0" class="text-center py-12">
        <p class="text-text-secondary mb-4">No profiles found</p>
        <router-link to="/employee-profiles/create">
          <button class="btn-primary text-white px-4 py-2 rounded-lg">Create Your First Profile</button>
        </router-link>
      </div>

      <!-- Employee Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <div
          v-for="profile in filteredProfiles"
          :key="profile.id"
          class="bg-bg-card border border-border-primary rounded-xl p-5 card-hover"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3">
              <div
                :class="['w-12 h-12 rounded-full flex items-center justify-center text-white text-lg font-bold bg-gradient-to-br', getAvatarColor(profile.name)]"
              >
                {{ getInitials(profile.name) }}
              </div>
              <div>
                <h3 class="font-semibold text-lg text-text-primary">{{ profile.name }}</h3>
                <div class="flex items-center gap-2">
                  <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-accent-primary/20 text-accent-light">
                    {{ profile.role }}
                  </span>
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
            </div>
          </div>

          <div class="mb-4">
            <div class="text-xs text-text-muted mb-1">Goal</div>
            <p class="text-sm text-text-secondary line-clamp-2">{{ profile.goal || 'Not specified' }}</p>
          </div>

          <div class="flex items-center gap-2 pt-4 border-t border-border-primary">
            <button
              class="flex-1 px-3 py-1.5 rounded-lg bg-bg-tertiary hover:bg-border-primary text-sm font-medium text-text-primary transition"
              @click="handleView(profile.id)"
            >
              View
            </button>
            <button
              class="flex-1 px-3 py-1.5 rounded-lg bg-bg-tertiary hover:bg-border-primary text-sm font-medium text-text-primary transition"
              @click="handleEdit(profile.id)"
            >
              Edit
            </button>
            <button
              class="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-sm font-medium transition"
              @click="handleDelete(profile.id, profile.name)"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
