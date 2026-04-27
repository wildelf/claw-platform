<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { useAgentsStore } from '@/stores/agents'
import { useSkillsStore } from '@/stores/skills'
import { useModelsStore } from '@/stores/models'

const router = useRouter()
const agentsStore = useAgentsStore()
const skillsStore = useSkillsStore()
const modelsStore = useModelsStore()

const formData = ref({
  name: '',
  description: '',
  role: '',
  goal: '',
  backstory: '',
  skill_ids: [] as string[],
  model_config_id: null as string | null
})

const loading = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  await skillsStore.fetchSkills()
  await modelsStore.fetchModels()
})

async function handleSubmit() {
  if (!formData.value.name.trim()) {
    error.value = 'Name is required'
    return
  }

  loading.value = true
  error.value = null

  try {
    await agentsStore.createAgent(formData.value)
    router.push('/agents')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to create agent'
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push('/agents')
}

function toggleSkill(skillId: string) {
  const idx = formData.value.skill_ids.indexOf(skillId)
  if (idx === -1) {
    formData.value.skill_ids.push(skillId)
  } else {
    formData.value.skill_ids.splice(idx, 1)
  }
}

function isSkillSelected(skillId: string) {
  return formData.value.skill_ids.includes(skillId)
}
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">Create New Agent</h1>

    <Card v-if="error" title="Error" class="bg-red-50">
      <p class="text-red-600">{{ error }}</p>
    </Card>

    <Card title="Agent Information">
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
          <Input
            v-model="formData.name"
            placeholder="Enter agent name"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            v-model="formData.description"
            placeholder="Enter agent description"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          ></textarea>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Role</label>
          <Input
            v-model="formData.role"
            placeholder="Enter agent role"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Goal</label>
          <textarea
            v-model="formData.goal"
            placeholder="Enter agent goal"
            rows="2"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          ></textarea>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Backstory</label>
          <textarea
            v-model="formData.backstory"
            placeholder="Enter agent backstory"
            rows="4"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          ></textarea>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Skills</label>
          <div class="space-y-2 max-h-48 overflow-y-auto border border-gray-200 rounded p-3">
            <div
              v-for="skill in skillsStore.skills"
              :key="skill.id"
              @click="toggleSkill(skill.id)"
              class="flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-gray-50"
              :class="isSkillSelected(skill.id) ? 'bg-blue-50' : ''"
            >
              <input
                type="checkbox"
                :checked="isSkillSelected(skill.id)"
                class="w-4 h-4"
                @click.stop
              />
              <span>{{ skill.name }}</span>
            </div>
            <div v-if="skillsStore.skills.length === 0" class="text-gray-500 text-sm">
              No skills available
            </div>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Default Model</label>
          <select
            v-model="formData.model_config_id"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option :value="null">System Default</option>
            <option v-for="model in modelsStore.models" :key="model.id" :value="model.id">
              {{ model.name }} ({{ model.model }})
            </option>
          </select>
          <p class="text-sm text-gray-500 mt-1">
            Optionally select a default model for this agent
          </p>
        </div>

        <div class="flex gap-3 pt-4">
          <Button type="submit" variant="primary" :loading="loading">
            Create Agent
          </Button>
          <Button type="button" variant="secondary" @click="handleCancel">
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  </div>
</template>