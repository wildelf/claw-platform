<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAgentsStore } from '@/stores/agents'
import { useSkillsStore } from '@/stores/skills'
import { useModelsStore } from '@/stores/models'
import { useToolsStore } from '@/stores/tools'
import { BUILTIN_TOOLS } from '@/types'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'

const route = useRoute()
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
const saving = ref(false)
const error = ref('')

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    await Promise.all([
      agentsStore.fetchAgent(route.params.id as string),
      skillsStore.fetchSkills(),
      modelsStore.fetchModels(),
      toolsStore.fetchTools()
    ])
    const agent = agentsStore.currentAgent
    if (agent) {
      form.value = {
        name: agent.name,
        description: agent.description,
        role: agent.role,
        goal: agent.goal,
        backstory: agent.backstory,
        skill_ids: agent.skill_ids || [],
        tool_ids: agent.tool_ids || [],
        enabled_builtin_tools: agent.enabled_builtin_tools || [],
        text_model_config_id: agent.text_model_config_id || '',
        image_model_config_id: agent.image_model_config_id || '',
        video_model_config_id: agent.video_model_config_id || '',
      }
    }
  } catch (e) {
    error.value = 'Failed to load agent'
  } finally {
    loading.value = false
  }
})

const handleSubmit = async () => {
  saving.value = true
  error.value = ''
  try {
    await agentsStore.updateAgent(route.params.id as string, form.value)
    router.push(`/agents/${route.params.id}`)
  } catch (e) {
    error.value = 'Failed to update agent'
  } finally {
    saving.value = false
  }
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

function toggleTool(toolId: string) {
  const idx = form.value.tool_ids.indexOf(toolId)
  if (idx === -1) {
    form.value.tool_ids.push(toolId)
  } else {
    form.value.tool_ids.splice(idx, 1)
  }
}

function isToolSelected(toolId: string) {
  return form.value.tool_ids.includes(toolId)
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-semibold mb-6 text-text-primary">Edit Agent</h1>

    <Card v-if="loading" class="text-center py-8">
      <p class="text-text-muted">Loading...</p>
    </Card>

    <Card v-else-if="error" class="text-center py-8">
      <p class="text-status-error">{{ error }}</p>
    </Card>

    <Card v-else>
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-text-secondary mb-1">Name</label>
          <input
            v-model="form.name"
            type="text"
            class="w-full px-3 py-2 border border-border-primary rounded focus:outline-none focus:border-accent-primary bg-bg-secondary text-text-primary"
            required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-text-secondary mb-1">Description</label>
          <textarea
            v-model="form.description"
            class="w-full px-3 py-2 border border-border-primary rounded focus:outline-none focus:border-accent-primary bg-bg-secondary text-text-primary"
            rows="3"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-text-secondary mb-1">Role</label>
          <input
            v-model="form.role"
            type="text"
            class="w-full px-3 py-2 border border-border-primary rounded focus:outline-none focus:border-accent-primary bg-bg-secondary text-text-primary"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-text-secondary mb-1">Goal</label>
          <textarea
            v-model="form.goal"
            class="w-full px-3 py-2 border border-border-primary rounded focus:outline-none focus:border-accent-primary bg-bg-secondary text-text-primary"
            rows="2"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-text-secondary mb-1">Backstory</label>
          <textarea
            v-model="form.backstory"
            class="w-full px-3 py-2 border border-border-primary rounded focus:outline-none focus:border-accent-primary bg-bg-secondary text-text-primary"
            rows="3"
          />
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
                @click.stop="toggleBuiltInTool(tool.name)"
              />
              <div>
                <span class="font-medium">{{ tool.name }}</span>
                <p class="text-text-muted text-sm">{{ tool.description }}</p>
              </div>
            </div>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-text-secondary mb-2">Registered MCP Tools</label>
          <div class="space-y-2 max-h-48 overflow-y-auto border border-border-primary rounded p-3">
            <div
              v-for="tool in toolsStore.tools.filter(t => t.type === 'MCP')"
              :key="tool.id"
              @click="toggleTool(tool.id)"
              class="flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-bg-hover"
              :class="isToolSelected(tool.id) ? 'bg-accent-primary/10' : ''"
            >
              <input
                type="checkbox"
                :checked="isToolSelected(tool.id)"
                class="w-4 h-4"
                @click.stop
              />
              <div>
                <span class="font-medium">{{ tool.name }}</span>
                <p class="text-text-muted text-sm">{{ tool.description || 'MCP tool' }}</p>
              </div>
            </div>
            <div v-if="toolsStore.tools.filter(t => t.type === 'MCP').length === 0" class="text-text-muted text-sm">
              No MCP tools registered. Go to Tools to register MCP servers.
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

        <div v-if="error" class="text-status-error text-sm">{{ error }}</div>

        <div class="flex space-x-2">
          <Button type="submit" :loading="saving">Save</Button>
          <Button type="button" variant="secondary" @click="router.back()">Cancel</Button>
        </div>
      </form>
    </Card>
  </div>
</template>
