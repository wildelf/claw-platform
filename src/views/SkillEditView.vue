<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { useSkillsStore } from '@/stores/skills'
import { skillsApi } from '@/api/skills'

const route = useRoute()
const router = useRouter()
const skillsStore = useSkillsStore()

const skillId = route.params.id as string

const form = ref({
  name: '',
  description: ''
})

const fileNames = ref<string[]>([])
const fileContents = ref<Record<string, string>>({})
const selectedFile = ref<string | null>(null)
const editingContent = ref('')
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const fileError = ref('')

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    await skillsStore.fetchSkill(skillId)
    const skill = skillsStore.currentSkill
    if (skill) {
      form.value = {
        name: skill.name,
        description: skill.description
      }
    }
    await loadFiles()
  } catch (e) {
    error.value = 'Failed to load skill'
  } finally {
    loading.value = false
  }
})

async function loadFiles() {
  try {
    fileNames.value = await skillsApi.getFiles(skillId)
    const contents: Record<string, string> = {}
    for (const filename of fileNames.value) {
      contents[filename] = await skillsApi.getFileContent(skillId, filename)
    }
    fileContents.value = contents
  } catch (e) {
    fileError.value = 'Failed to load files'
    alert('Failed to load files: ' + (e instanceof Error ? e.message : String(e)))
  }
}

function selectFile(filename: string) {
  selectedFile.value = filename
  editingContent.value = fileContents.value[filename] || ''
}

function cancelEdit() {
  selectedFile.value = null
  editingContent.value = ''
}

async function saveFile() {
  if (!selectedFile.value) return

  saving.value = true
  fileError.value = ''
  try {
    await skillsApi.saveFile(skillId, selectedFile.value, editingContent.value)
    fileContents.value[selectedFile.value] = editingContent.value
    selectedFile.value = null
    editingContent.value = ''
  } catch (e) {
    fileError.value = 'Failed to save file'
  } finally {
    saving.value = false
  }
}

async function handleSubmit() {
  saving.value = true
  error.value = ''
  try {
    await skillsStore.updateSkill(skillId, form.value)
    router.push(`/skills/${skillId}`)
  } catch (e) {
    error.value = 'Failed to update skill'
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  router.back()
}
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <div class="flex items-center gap-2">
      <Button variant="secondary" @click="handleCancel">Cancel</Button>
      <h1 class="text-2xl font-bold text-gray-900">Edit Skill</h1>
    </div>

    <Card v-if="loading" class="text-center py-8">
      <p class="text-gray-500">Loading...</p>
    </Card>

    <Card v-else-if="error" class="bg-red-50">
      <p class="text-red-600">{{ error }}</p>
    </Card>

    <template v-else>
      <Card title="Skill Information">
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <Input
              v-model="form.name"
              placeholder="Enter skill name"
              required
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              v-model="form.description"
              placeholder="Enter skill description"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div v-if="error" class="text-red-500 text-sm">{{ error }}</div>

          <div class="flex gap-3 pt-4">
            <Button type="submit" :loading="saving">Save Metadata</Button>
            <Button type="button" variant="secondary" @click="handleCancel">Cancel</Button>
          </div>
        </form>
      </Card>

      <Card title="Skill Files">
        <div v-if="fileError" class="text-red-500 text-sm mb-4">{{ fileError }}</div>

        <div v-if="!selectedFile" class="space-y-2">
          <div class="text-sm text-gray-500 mb-2">Click a file to edit:</div>
          <div
            v-for="filename in fileNames"
            :key="filename"
            @click="selectFile(filename)"
            class="flex items-center justify-between p-3 bg-gray-50 rounded hover:bg-gray-100 cursor-pointer"
          >
            <span class="font-medium text-gray-900">{{ filename }}</span>
            <span class="text-sm text-gray-500">{{ fileContents[filename]?.length || 0 }} chars</span>
          </div>
          <div v-if="fileNames.length === 0" class="text-gray-500 text-center py-4">
            No files
          </div>
        </div>

        <div v-else class="space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="font-medium">Editing: {{ selectedFile }}</h3>
            <Button variant="secondary" size="sm" @click="cancelEdit">Cancel</Button>
          </div>
          <textarea
            v-model="editingContent"
            rows="20"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
          />
          <div class="flex gap-2">
            <Button @click="saveFile" :loading="saving">Save File</Button>
            <Button variant="secondary" @click="cancelEdit">Cancel</Button>
          </div>
        </div>
      </Card>
    </template>
  </div>
</template>