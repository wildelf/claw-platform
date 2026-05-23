<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { useAgentsStore } from '@/stores/agents'
import { useSkillsStore } from '@/stores/skills'
import { useModelsStore } from '@/stores/models'
import { useToolsStore } from '@/stores/tools'
import { BUILTIN_TOOLS } from '@/types'

const router = useRouter()
const agentsStore = useAgentsStore()
const skillsStore = useSkillsStore()
const modelsStore = useModelsStore()
const toolsStore = useToolsStore()

const form = ref({
  name: '',
  description: '',
  role: '',
  goal: '',
  backstory: '',
  skill_ids: [] as string[],
  tool_ids: [] as string[],
  enabled_builtin_tools: [] as string[],
  text_model_config_id: '',
  image_model_config_id: '',
  video_model_config_id: '',
})

const loading = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  await Promise.all([
    skillsStore.fetchSkills(),
    modelsStore.fetchModels(),
    toolsStore.fetchTools()
  ])
})

async function handleSubmit() {
  if (!form.value.name.trim()) {
    error.value = 'Name is required'
    return
  }

  loading.value = true
  error.value = null

  try {
    await agentsStore.createAgent(form.value)
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
  const idx = form.value.skill_ids.indexOf(skillId)
  if (idx === -1) {
    form.value.skill_ids.push(skillId)
  } else {
    form.value.skill_ids.splice(idx, 1)
  }
}

function isSkillSelected(skillId: string) {
  return form.value.skill_ids.includes(skillId)
}

function toggleBuiltInTool(toolName: string) {
  const idx = form.value.enabled_builtin_tools.indexOf(toolName)
  if (idx === -1) {
    form.value.enabled_builtin_tools.push(toolName)
  } else {
    form.value.enabled_builtin_tools.splice(idx, 1)
  }
}

function isBuiltInToolSelected(toolName: string) {
  return form.value.enabled_builtin_tools.includes(toolName)
}
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-text-primary">Create New Agent</h1>

    <Card v-if="error" title="Error" class="bg-status-error/10">
      <p class="text-status-error">{{ error }}</p>
    </Card>

    <Card title="Agent Information">
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-text-secondary mb-1">Name *</label>
          <Input
            v-model="form.name"
            placeholder="Enter agent name"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-text-secondary mb-1">Description</label>
          <textarea
            v-model="form.description"
            placeholder="Enter agent description"
            rows="3"
            class="w-full px-3 py-2 border border-border-primary rounded-lg focus:outline-none focus:border-accent-primary bg-bg-secondary text-text-primary"
          ></textarea>
        </div>

        <div>
          <label class="block text-sm font-medium text-text-secondary mb-1">Role</label>
          <Input
            v-model="form.role"
            placeholder="Enter agent role"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-text-secondary mb-1">Goal</label>
          <textarea
            v-model="form.goal"
            placeholder="Enter agent goal"
            rows="2"
            class="w-full px-3 py-2 border border-border-primary rounded-lg focus:outline-none focus:border-accent-primary bg-bg-secondary text-text-primary"
          ></textarea>
        </div>

        <div>
          <label class="block text-sm font-medium text-text-secondary mb-1">Backstory</label>
          <textarea
            v-model="form.backstory"
            placeholder="Enter agent backstory"
            rows="4"
            class="w-full px-3 py-2 border border-border-primary rounded-lg focus:outline-none focus:border-accent-primary bg-bg-secondary text-text-primary"
          ></textarea>
        </div>

        <div>
          <label class="block text-sm font-medium text-text-secondary mb-2">Skills</label>
          <div class="space-y-2 max-h-48 overflow-y-auto border border-border-primary rounded p-3">
            <div
              v-for="skill in skillsStore.skills"
              :key="skill.id"
              @click="toggleSkill(skill.id)"
              class="flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-bg-hover"
              :class="isSkillSelected(skill.id) ? 'bg-accent-primary/10' : ''"
            >
              <input
                type="checkbox"
                :checked="isSkillSelected(skill.id)"
                class="w-4 h-4"
                @click.stop
              />
              <span>{{ skill.name }}</span>
            </div>
            <div v-if="skillsStore.skills.length === 0" class="text-text-muted text-sm">
              No skills available
            </div>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-text-secondary mb-2">Built-in Tools</label>
          <div class="space-y-2 max-h-48 overflow-y-auto border border-border-primary rounded p-3">
            <div
              v-for="tool in BUILTIN_TOOLS"
              :key="tool.name"
              @click="toggleBuiltInTool(tool.name)"
              class="flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-bg-hover"
              :class="isBuiltInToolSelected(tool.name) ? 'bg-status-active/10' : ''"
            >
              <input
                type="checkbox"
                :checked="isBuiltInToolSelected(tool.name)"
                class="w-4 h-4"
                @click.stop
              />
              <div>
                <span class="font-medium">{{ tool.name }}</span>
                <p class="text-text-muted text-sm">{{ tool.description }}</p>
              </div>
            </div>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-text-secondary mb-1">Text Model</label>
          <select
            v-model="form.text_model_config_id"
            class="w-full px-3 py-2 border border-border-primary rounded-lg focus:outline-none focus:border-accent-primary bg-bg-secondary text-text-primary"
          >
            <option value="">Default</option>
            <option v-for="m in modelsStore.models.filter(m => !m.modality || m.modality === 'text')" :key="m.id" :value="m.id">
              {{ m.name }} ({{ m.model }})
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-text-secondary mb-1">Image Model</label>
          <select
            v-model="form.image_model_config_id"
            class="w-full px-3 py-2 border border-border-primary rounded-lg focus:outline-none focus:border-accent-primary bg-bg-secondary text-text-primary"
          >
            <option value="">None</option>
            <option v-for="m in modelsStore.models.filter(m => m.modality && ['text-to-image', 'image-to-image', 'image-to-text'].includes(m.modality as string))" :key="m.id" :value="m.id">
              {{ m.name }} ({{ m.model }})
            </option>
          </select>
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