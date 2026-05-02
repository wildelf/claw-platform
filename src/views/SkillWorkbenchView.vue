<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import SkillConfigPanel from '@/components/skills/SkillConfigPanel.vue'
import SkillDebugPanel from '@/components/skills/SkillDebugPanel.vue'
import { useModelsStore } from '@/stores/models'
import { useSkillWorkbench } from '@/composables/useSkillWorkbench'

const route = useRoute()
const router = useRouter()
const modelsStore = useModelsStore()

const {
  mode,
  form,
  localConfig,
  generationProgress,
  generationOutput,
  testResult,
  error,
  categoryOptions,
  isEditMode,
  canSave,
  canTest,
  allFiles,
  selectedFile,
  initializeForCreate,
  initializeForEdit,
  handleGenerate,
  handleModify,
  selectFile,
  handleSave,
  handleRunTest,
  handleClear,
  handleCancel
} = useSkillWorkbench()

// Modification text for edit mode
const modificationText = ref('')

onMounted(() => {
  if (modelsStore.models.length === 0) {
    modelsStore.fetchModels()
  }

  const id = route.params.id as string
  if (id) {
    initializeForEdit(id)
  } else {
    initializeForCreate()
  }
})

// Watch for route changes
watch(() => route.params.id, (newId) => {
  if (newId) {
    initializeForEdit(newId as string)
  } else {
    initializeForCreate()
  }
})

function onApplyChanges() {
  handleModify(modificationText.value)
}

function onClearModification() {
  modificationText.value = ''
}

function onSelectFile(name: string) {
  selectFile(name)
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">
        {{ isEditMode ? `Edit: ${form.name}` : 'Create Skill' }}
      </h1>
      <div class="flex gap-3">
        <Button
          v-if="canSave"
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
                :disabled="generationProgress === 'generating'"
              />
            </div>

            <!-- Description -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                v-model="form.description"
                placeholder="Briefly describe what this skill does..."
                rows="3"
                :disabled="generationProgress === 'generating'"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>

            <!-- Category -->
            <Select
              v-model="form.category"
              :options="categoryOptions"
              label="Category"
              placeholder="Select category..."
              :disabled="generationProgress === 'generating'"
            />

            <!-- Tags -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Tags</label>
              <Input
                v-model="form.tags"
                placeholder="comma, separated, tags"
                :disabled="generationProgress === 'generating'"
              />
              <p class="text-xs text-gray-500 mt-1">Separate tags with commas</p>
            </div>
          </div>
        </Card>

        <!-- Create Mode: Definition textarea -->
        <Card v-if="!isEditMode" :padding="true" title="Skill Definition" class="mt-4">
          <div class="space-y-4">
            <p class="text-sm text-gray-600">
              Describe what you want this skill to do in natural language. Be specific about inputs, outputs, and behavior.
            </p>
            <textarea
              v-model="form.definition"
              placeholder="I want a skill that helps with code review. It should:&#10;- Check code for common bugs&#10;- Suggest improvements&#10;- Provide examples..."
              rows="8"
              :disabled="generationProgress === 'generating'"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm disabled:bg-gray-100"
            />
          </div>
        </Card>

        <!-- Edit Mode: Modification textarea -->
        <Card v-if="isEditMode" :padding="true" title="Modify Skill" class="mt-4">
          <div class="space-y-4">
            <p class="text-sm text-gray-600">
              Describe changes in natural language. The AI will modify only the parts you specify.
            </p>
            <textarea
              v-model="modificationText"
              placeholder="e.g., change the model to gpt-4, increase timeout to 60s, add support for Python 3.12..."
              rows="6"
              :disabled="generationProgress === 'generating'"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm disabled:bg-gray-100"
            />
            <div class="flex gap-2">
              <Button
                variant="primary"
                size="sm"
                :disabled="!modificationText.trim() || generationProgress === 'generating'"
                :loading="generationProgress === 'generating'"
                @click="onApplyChanges"
              >
                Apply Changes
              </Button>
              <Button
                variant="secondary"
                size="sm"
                @click="onClearModification"
              >
                Clear
              </Button>
            </div>
          </div>
        </Card>

        <!-- Generate Button (create mode only) -->
        <Button
          v-if="!isEditMode"
          variant="primary"
          class="w-full mt-4"
          size="lg"
          :disabled="!form.name.trim() || generationProgress === 'generating'"
          :loading="generationProgress === 'generating'"
          @click="handleGenerate"
        >
          {{ generationProgress === 'generating' ? 'Generating...' : 'Generate Skill' }}
        </Button>
      </div>

      <!-- CENTER PANEL: Debug + Files -->
      <div class="flex-1 min-w-0 overflow-hidden flex flex-col">
        <SkillDebugPanel
          :generation-progress="generationProgress"
          :generation-output="generationOutput"
          :test-result="testResult"
          :can-test="canTest"
          :files="allFiles"
          :selected-file="selectedFile"
          @select-file="onSelectFile"
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