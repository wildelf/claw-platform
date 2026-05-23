<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import { useEmployeeProfilesStore } from '@/stores/employeeProfiles'

const route = useRoute()
const router = useRouter()
const store = useEmployeeProfilesStore()

const profileId = route.params.id as string
const activeFile = ref('profile.md')
const editorContent = ref('')
const isEditing = ref(false)
const saving = ref(false)

const colorMap: Record<string, string> = {
  active: 'success',
  paused: 'warning',
  retired: 'default'
}

function getInitials(name: string): string {
  return name.slice(0, 2).toUpperCase()
}

async function loadProfile() {
  await store.fetchProfile(profileId)
  await store.fetchProfileFiles(profileId)
  if (store.files.length > 0 && !store.files.includes(activeFile.value)) {
    activeFile.value = store.files[0]
  }
  await loadFileContent()
}

async function loadFileContent() {
  if (!activeFile.value) return
  try {
    editorContent.value = await store.getProfileFileContent(profileId, activeFile.value)
    isEditing.value = false
  } catch {
    editorContent.value = 'Failed to load file content.'
  }
}

async function startEdit() {
  isEditing.value = true
}

async function cancelEdit() {
  await loadFileContent()
  isEditing.value = false
}

async function saveFile() {
  saving.value = true
  try {
    await store.updateProfileFileContent(profileId, activeFile.value, editorContent.value)
    isEditing.value = false
  } catch {
    // Error handled by store
  } finally {
    saving.value = false
  }
}

function onFileChange(filename: string) {
  activeFile.value = filename
  loadFileContent()
}

async function handleDelete() {
  if (confirm('确定要删除此员工档案吗？此操作不可撤销。')) {
    await store.deleteProfile(profileId)
    router.push('/employee-profiles')
  }
}

onMounted(() => {
  loadProfile()
})

watch(() => route.params.id, () => {
  loadProfile()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <Button variant="ghost" @click="router.push('/employee-profiles')">
        <svg class="w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        返回列表
      </Button>
    </div>

    <div v-if="store.loading" class="flex items-center justify-center py-12">
      <svg class="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <div v-if="store.currentProfile && !store.loading" class="flex flex-col lg:flex-row gap-6">
      <!-- Left Sidebar: Profile Info -->
      <div class="lg:w-80 flex-shrink-0 space-y-4">
        <Card>
          <div class="flex flex-col items-center text-center">
            <div class="w-16 h-16 rounded-full bg-blue-500 flex items-center justify-center text-white text-xl font-bold mb-3">
              {{ getInitials(store.currentProfile.name) }}
            </div>
            <h2 class="text-lg font-bold text-gray-900">{{ store.currentProfile.name }}</h2>
            <p class="text-sm text-gray-500">{{ store.currentProfile.role || '未设置角色' }}</p>
            <Badge :variant="colorMap[store.currentProfile.status] || 'default'" class="mt-2">
              {{ store.currentProfile.status }}
            </Badge>
          </div>
          <div class="mt-4 space-y-3 border-t border-gray-200 pt-4">
            <div>
              <label class="text-xs font-medium text-gray-500 uppercase">目标</label>
              <p class="text-sm text-gray-700 mt-1">{{ store.currentProfile.goal || '-' }}</p>
            </div>
            <div>
              <label class="text-xs font-medium text-gray-500 uppercase">背景</label>
              <p class="text-sm text-gray-700 mt-1">{{ store.currentProfile.backstory || '-' }}</p>
            </div>
            <div>
              <label class="text-xs font-medium text-gray-500 uppercase">性格</label>
              <p class="text-sm text-gray-700 mt-1">{{ store.currentProfile.personality || '-' }}</p>
            </div>
          </div>
        </Card>

        <Card>
          <h3 class="text-sm font-semibold text-gray-700 mb-3">操作</h3>
          <div class="space-y-2">
            <Button variant="secondary" class="w-full text-sm" size="sm">编辑信息</Button>
            <Button variant="danger" class="w-full text-sm" size="sm" @click="handleDelete">删除员工</Button>
          </div>
          <div class="mt-3 pt-3 border-t border-gray-200">
            <p class="text-xs text-gray-400 truncate" :title="store.currentProfile.git_path">
              Git: {{ store.currentProfile.git_path }}
            </p>
          </div>
        </Card>
      </div>

      <!-- Main Content: File Editor -->
      <div class="flex-1 min-w-0">
        <Card :padding="false">
          <!-- File Tabs -->
          <div class="flex items-center border-b border-gray-200 bg-gray-50 px-4">
            <button
              v-for="file in store.files"
              :key="file"
              @click="onFileChange(file)"
              :class="[
                'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors',
                activeFile === file
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              ]"
            >
              {{ file }}
            </button>
          </div>

          <!-- Editor Area -->
          <div class="p-4">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-medium text-gray-700">{{ activeFile }}</h3>
              <div class="flex gap-2">
                <template v-if="!isEditing">
                  <Button variant="ghost" size="sm" @click="startEdit">编辑</Button>
                </template>
                <template v-else>
                  <Button variant="secondary" size="sm" @click="cancelEdit">取消</Button>
                  <Button variant="primary" size="sm" :loading="saving" @click="saveFile">保存</Button>
                </template>
              </div>
            </div>
            <textarea
              v-if="isEditing"
              v-model="editorContent"
              rows="20"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono"
              spellcheck="false"
            />
            <pre v-else class="bg-gray-50 rounded-lg p-4 text-sm font-mono whitespace-pre-wrap text-gray-800 max-h-[600px] overflow-y-auto">{{ editorContent }}</pre>
          </div>
        </Card>

        <!-- Constraints & Working Rules -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <Card>
            <h3 class="text-sm font-semibold text-gray-700 mb-2">约束条件</h3>
            <pre class="text-sm font-mono whitespace-pre-wrap text-gray-600">{{ store.currentProfile.constraints || '无约束' }}</pre>
          </Card>
          <Card>
            <h3 class="text-sm font-semibold text-gray-700 mb-2">工作规则</h3>
            <pre class="text-sm font-mono whitespace-pre-wrap text-gray-600">{{ store.currentProfile.working_rules || '无规则' }}</pre>
          </Card>
        </div>
      </div>
    </div>
  </div>
</template>
