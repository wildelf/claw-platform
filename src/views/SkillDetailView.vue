<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import { useSkillsStore } from '@/stores/skills'

const route = useRoute()
const router = useRouter()
const skillsStore = useSkillsStore()

const skillId = computed(() => route.params.id as string)
const skill = computed(() => skillsStore.currentSkill)
const fileNames = ref<string[]>([])
const fileContents = ref<Record<string, string>>({})
const loadingFiles = ref(false)
const selectedFile = ref<string | null>(null)
const fileContent = ref('')
const showFileModal = ref(false)

onMounted(async () => {
  await skillsStore.fetchSkill(skillId.value)
  loadFiles()
})

async function loadFiles() {
  loadingFiles.value = true
  try {
    const names = await skillsStore.fetchSkillFiles(skillId.value)
    fileNames.value = names
    fileContents.value = skillsStore.files.get(skillId.value) || {}
  } catch (e) {
    console.error('Failed to load files:', e)
  } finally {
    loadingFiles.value = false
  }
}

function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'default' {
  switch (status) {
    case 'trained': return 'success'
    case 'pending': return 'warning'
    case 'needs_review': return 'danger'
    case 'evolved': return 'success'
    default: return 'default'
  }
}

function handleEdit() {
  router.push(`/skills/${skillId.value}/edit`)
}

function handleBack() {
  router.push('/skills')
}

function handleViewFile(filename: string) {
  selectedFile.value = filename
  fileContent.value = fileContents.value[filename] || ''
  showFileModal.value = true
}

function closeFileModal() {
  showFileModal.value = false
  selectedFile.value = null
  fileContent.value = ''
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div class="flex gap-2">
        <Button variant="secondary" @click="handleBack">Back</Button>
        <h1 class="text-2xl font-bold text-gray-900">Skill Detail</h1>
      </div>
      <Button variant="primary" @click="handleEdit">Edit</Button>
    </div>

    <div v-if="skillsStore.loading" class="text-center py-8">
      <p class="text-gray-500">Loading...</p>
    </div>

    <div v-else-if="!skill" class="text-center py-8">
      <p class="text-gray-500">Skill not found</p>
    </div>

    <template v-else>
      <Card>
        <div class="space-y-4">
          <div class="flex justify-between items-start">
            <div>
              <h2 class="text-xl font-semibold text-gray-900">{{ skill.name }}</h2>
              <p class="text-gray-500 mt-1">{{ skill.description }}</p>
            </div>
            <Badge :variant="getStatusVariant(skill.status)" class="text-sm">
              {{ skill.status }}
            </Badge>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
            <div>
              <p class="text-sm font-medium text-gray-500">Version</p>
              <p class="text-gray-900">{{ skill.version }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">Feedback Count</p>
              <p class="text-gray-900">{{ skill.feedback_count }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">Path</p>
              <p class="text-gray-900 text-sm truncate">{{ skill.path || 'Not set' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">Created</p>
              <p class="text-gray-900 text-sm">{{ new Date(skill.created_at).toLocaleDateString() }}</p>
            </div>
          </div>
        </div>
      </Card>

      <!-- Skill Files -->
      <Card>
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-medium text-gray-900">Files</h3>
          <Button variant="secondary" size="sm" @click="loadFiles" :loading="loadingFiles">
            Refresh
          </Button>
        </div>

        <div v-if="loadingFiles" class="text-center py-4">
          <p class="text-gray-500">Loading files...</p>
        </div>

        <div v-else-if="fileNames.length === 0" class="text-center py-4">
          <p class="text-gray-500">No files</p>
        </div>

        <div v-else class="space-y-2">
          <div
            v-for="filename in fileNames"
            :key="filename"
            class="flex items-center justify-between p-3 bg-gray-50 rounded hover:bg-gray-100"
          >
            <div class="flex items-center gap-3">
              <span class="font-medium text-gray-900">{{ filename }}</span>
            </div>
            <div class="flex gap-2">
              <Button variant="ghost" size="sm" @click="handleViewFile(filename)">View</Button>
            </div>
          </div>
        </div>
      </Card>
    </template>

    <!-- File View Modal -->
    <Teleport to="body">
      <div v-if="showFileModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
          <div class="flex justify-between items-center p-4 border-b">
            <h3 class="text-lg font-medium">{{ selectedFile }}</h3>
            <Button variant="ghost" size="sm" @click="closeFileModal">✕</Button>
          </div>
          <div class="flex-1 overflow-auto p-4">
            <pre class="text-sm font-mono whitespace-pre-wrap">{{ fileContent }}</pre>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
