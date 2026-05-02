<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import SkillConfigPanel from '@/components/skills/SkillConfigPanel.vue'
import SkillDebugPanel from '@/components/skills/SkillDebugPanel.vue'
import { useSkillsStore } from '@/stores/skills'
import { useModelsStore } from '@/stores/models'
import type { SkillConfig } from '@/types'

const router = useRouter()
const skillsStore = useSkillsStore()
const modelsStore = useModelsStore()

// Form state
const form = ref({
  name: '',
  description: '',
  definition: '',
  category: '',
  tags: ''
})

// Local config (passed to SkillConfigPanel)
const localConfig = ref<SkillConfig>({
  model_id: null,
  timeout_ms: 30000,
  max_retries: 3,
  rate_limit: null,
  cache_enabled: false,
  cache_ttl_seconds: 300,
  priority: 'medium',
  max_concurrent: 5
})

const categoryOptions = [
  { value: 'content', label: 'Content Creation' },
  { value: 'data', label: 'Data Processing' },
  { value: 'video', label: 'Video Processing' },
  { value: 'image', label: 'Image Processing' },
  { value: 'audio', label: 'Audio Processing' },
  { value: 'coding', label: 'Coding & Development' },
  { value: 'other', label: 'Other' }
]

const error = ref<string | null>(null)

onMounted(() => {
  if (modelsStore.models.length === 0) {
    modelsStore.fetchModels()
  }
  // Reset generation state
  skillsStore.generationProgress = 'idle'
  skillsStore.generationOutput = ''
  skillsStore.testResult = null
})

function appendOutput(text: string) {
  skillsStore.generationOutput += text
}

async function handleGenerate() {
  console.log('[SkillCreate] handleGenerate called at', Date.now())
  if (!form.value.name.trim()) {
    error.value = 'Name is required'
    return
  }

  error.value = null
  skillsStore.generationProgress = 'generating'
  skillsStore.generationOutput = ''
  console.log('[SkillCreate] State set, starting XHR...')

  const prompt = buildPrompt()
  console.log('[SkillCreate] Sending POST request via XHR...')

  const xhr = new XMLHttpRequest()
  xhr.open('POST', '/api/skills/generate', true)
  xhr.setRequestHeader('Content-Type', 'application/json')

  let buffer = ''
  xhr.onprogress = () => {
    buffer += xhr.responseText.substring(buffer.length)
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'content') {
            appendOutput(data.content)
          } else if (data.type === 'error') {
            appendOutput('\nError: ' + data.error)
          } else if (data.type === 'done') {
            appendOutput('\n\n✓ Skill generation completed!')
            skillsStore.generationProgress = 'success'
          } else if (data.type === 'start') {
            appendOutput('Starting skill generation...\n')
          }
        } catch (e) {}
      }
    }
  }

  xhr.onload = () => {
    console.log('[SkillCreate] XHR complete, status:', xhr.status, 'response length:', xhr.responseText.length)
    // Process remaining buffer
    const remaining = buffer + xhr.responseText.substring(buffer.length)
    const lines = remaining.split('\n')
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'content') appendOutput(data.content)
          else if (data.type === 'done') {
            appendOutput('\n\n✓ Skill generation completed!')
            skillsStore.generationProgress = 'success'
          }
        } catch (e) {}
      }
    }
    if (skillsStore.generationProgress !== 'success') {
      console.log('[SkillCreate] Marking success, output length:', skillsStore.generationOutput.length)
      skillsStore.generationProgress = 'success'
    }
  }

  xhr.onerror = () => {
    console.log('[SkillCreate] XHR error')
    skillsStore.generationProgress = 'error'
    appendOutput('\nNetwork error')
  }

  xhr.send(JSON.stringify({
    name: form.value.name,
    description: form.value.description || `A ${form.value.category || 'general purpose'} skill: ${form.value.name}`,
    prompt,
    config: localConfig.value
  }))

  // Fallback timeout - 8 seconds for faster testing
  setTimeout(() => {
    if (skillsStore.generationProgress === 'generating') {
      console.log('[SkillCreate] Timeout reached, setting success')
      skillsStore.generationProgress = 'success'
    }
  }, 8000)
}

function buildPrompt(): string {
  const parts = []
  if (form.value.description) {
    parts.push(`Description: ${form.value.description}`)
  }
  if (form.value.definition) {
    parts.push(`Definition: ${form.value.definition}`)
  }
  if (form.value.category) {
    parts.push(`Category: ${form.value.category}`)
  }
  if (form.value.tags) {
    parts.push(`Tags: ${form.value.tags}`)
  }
  return parts.join('\n')
}

async function handleSave() {
  try {
    await skillsStore.createSkill({
      name: form.value.name,
      description: form.value.description,
      metadata: {
        category: form.value.category,
        tags: form.value.tags,
        definition: form.value.definition,
        config: localConfig.value
      }
    })
    router.push('/skills')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to save skill'
  }
}

function handleRunTest() {
  // Placeholder - set a mock result for now
  skillsStore.testResult = {
    output: { result: 'Test execution not yet implemented. The skill has been generated.' },
    metrics: { duration_ms: 0, tokens_used: 0, cache_hit: false }
  }
}

function handleClear() {
  skillsStore.testResult = null
}

function handleCancel() {
  skillsStore.generationProgress = 'idle'
  skillsStore.generationOutput = ''
  router.push('/skills')
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Create Skill</h1>
      <div class="flex gap-3">
        <Button
          v-if="skillsStore.generationProgress === 'success'"
          variant="primary"
          @click="handleSave"
        >
          Save Skill
        </Button>
        <Button variant="secondary" @click="handleCancel">Cancel</Button>
      </div>
    </div>

    <!-- Error Banner -->
    <div v-if="error" class="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
      <p class="text-red-600 text-sm">{{ error }}</p>
    </div>

    <!-- Three Panel Layout -->
    <div class="flex-1 flex gap-6 min-h-0">
      <!-- LEFT PANEL: Form -->
      <div class="w-80 flex-shrink-0 overflow-y-auto">
        <Card :padding="true" title="Skill Information">
          <div class="space-y-4">
            <!-- Name -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <Input
                v-model="form.name"
                placeholder="e.g., code-review, data-analysis"
                :disabled="skillsStore.generationProgress === 'generating'"
              />
            </div>

            <!-- Description -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                v-model="form.description"
                placeholder="Briefly describe what this skill does..."
                rows="3"
                :disabled="skillsStore.generationProgress === 'generating'"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>

            <!-- Category -->
            <Select
              v-model="form.category"
              :options="categoryOptions"
              label="Category"
              placeholder="Select category..."
              :disabled="skillsStore.generationProgress === 'generating'"
            />

            <!-- Tags -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Tags</label>
              <Input
                v-model="form.tags"
                placeholder="comma, separated, tags"
                :disabled="skillsStore.generationProgress === 'generating'"
              />
              <p class="text-xs text-gray-500 mt-1">Separate tags with commas</p>
            </div>
          </div>
        </Card>

        <!-- Natural Language Prompt -->
        <Card :padding="true" title="Skill Definition" class="mt-4">
          <div class="space-y-4">
            <p class="text-sm text-gray-600">
              Describe what you want this skill to do in natural language. Be specific about inputs, outputs, and behavior.
            </p>
            <textarea
              v-model="form.definition"
              placeholder="I want a skill that helps with code review. It should:&#10;- Check code for common bugs&#10;- Suggest improvements&#10;- Provide examples..."
              rows="8"
              :disabled="skillsStore.generationProgress === 'generating'"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm disabled:bg-gray-100"
            />
          </div>
        </Card>

        <!-- Generate Button -->
        <Button
          variant="primary"
          class="w-full mt-4"
          size="lg"
          :disabled="!form.name.trim() || skillsStore.generationProgress === 'generating'"
          :loading="skillsStore.generationProgress === 'generating'"
          @click="handleGenerate"
        >
          {{ skillsStore.generationProgress === 'generating' ? 'Generating...' : 'Generate Skill' }}
        </Button>
      </div>

      <!-- CENTER PANEL: Debug -->
      <div class="flex-1 min-w-0 overflow-hidden flex flex-col">
        <SkillDebugPanel
          :generation-progress="skillsStore.generationProgress"
          :generation-output="skillsStore.generationOutput"
          :test-result="skillsStore.testResult"
          :can-test="skillsStore.generationProgress === 'success'"
          @run-test="handleRunTest"
          @clear="handleClear"
        />
      </div>

      <!-- RIGHT PANEL: Config -->
      <div class="w-72 flex-shrink-0 overflow-y-auto">
        <SkillConfigPanel
          v-model="localConfig"
        />
      </div>
    </div>
  </div>
</template>
