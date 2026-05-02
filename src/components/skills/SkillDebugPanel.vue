<script setup lang="ts">
import { ref, computed } from 'vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'

interface Props {
  generationProgress: 'idle' | 'generating' | 'success' | 'error'
  generationOutput: string
  testResult: { output: any; metrics: { duration_ms: number; tokens_used: number; cache_hit: boolean } } | null
  canTest: boolean
  files?: Record<string, string>
  selectedFile?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  files: () => ({}),
  selectedFile: null
})

const emit = defineEmits<{
  'select-file': [name: string]
  'run-test': []
  'clear': []
}>()

const testInput = ref('')
const isRunning = ref(false)
const activeTab = ref<'output' | 'files'>('output')

const outputLines = computed(() => props.generationOutput.split('\n'))
const fileNames = computed(() => Object.keys(props.files))
const selectedFileContent = computed(() => {
  if (props.selectedFile && props.files[props.selectedFile]) {
    return props.files[props.selectedFile]
  }
  return null
})

function onTabClick(tab: 'output' | 'files') {
  activeTab.value = tab
}

function onFileClick(name: string) {
  emit('select-file', name)
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Generation Progress Section -->
    <Card :padding="true" class="mb-4">
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="font-medium text-gray-900">Generation Progress</h3>
          <span
            v-if="generationProgress === 'generating'"
            class="flex items-center text-sm text-blue-600"
          >
            <span class="animate-spin mr-2">⟳</span>
            Generating...
          </span>
        </div>
      </template>

      <div
        class="bg-gray-900 text-gray-100 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm"
      >
        <div v-if="generationProgress === 'idle'" class="text-gray-500">
          Fill in the form and click "Generate" to create your skill...
        </div>
        <div v-else-if="generationProgress === 'generating'" class="space-y-1">
          <div v-for="(line, i) in outputLines" :key="i" class="whitespace-pre-wrap">
            {{ line }}
          </div>
          <span class="animate-pulse">▊</span>
        </div>
        <div v-else-if="generationProgress === 'success'" class="space-y-1">
          <div v-for="(line, i) in outputLines" :key="i" class="whitespace-pre-wrap">
            {{ line }}
          </div>
          <div class="mt-4 pt-4 border-t border-gray-700 text-green-400">
            ✓ Generation completed successfully!
          </div>
        </div>
        <div v-else-if="generationProgress === 'error'" class="text-red-400 space-y-1">
          <div v-for="(line, i) in outputLines" :key="i" class="whitespace-pre-wrap">
            {{ line }}
          </div>
        </div>
      </div>
    </Card>

    <!-- File Tabs Section -->
    <Card v-if="fileNames.length > 0" :padding="true" class="mb-4">
      <template #header>
        <div class="flex items-center gap-2">
          <h3 class="font-medium text-gray-900">Generated Files</h3>
        </div>
      </template>

      <div class="flex flex-col space-y-3">
        <!-- Tab buttons -->
        <div class="flex gap-2 border-b border-gray-200 pb-2">
          <button
            v-for="name in fileNames"
            :key="name"
            @click="onFileClick(name)"
            :class="[
              'px-3 py-1 text-sm rounded-t border transition-colors',
              selectedFile === name
                ? 'bg-blue-100 border-blue-300 text-blue-700'
                : 'bg-gray-100 border-gray-200 text-gray-600 hover:bg-gray-200'
            ]"
          >
            {{ name }}
          </button>
        </div>

        <!-- File content display -->
        <div v-if="selectedFile && selectedFileContent" class="bg-gray-50 rounded-lg p-3 max-h-64 overflow-auto">
          <pre class="text-sm text-gray-800 whitespace-pre-wrap font-mono">{{ selectedFileContent }}</pre>
        </div>
        <div v-else-if="fileNames.length > 0" class="text-sm text-gray-500">
          Click a file tab to view its content
        </div>
      </div>
    </Card>

    <!-- Test Section (show in success or edit mode) -->
    <Card v-if="generationProgress === 'success' || canTest" :padding="true">
      <template #header>
        <h3 class="font-medium text-gray-900">Test Your Skill</h3>
      </template>

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Test Input</label>
          <textarea
            v-model="testInput"
            placeholder="Enter test input for your skill..."
            rows="4"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
          />
        </div>

        <div class="flex gap-2">
          <Button
            variant="primary"
            :disabled="!canTest || !testInput.trim()"
            :loading="isRunning"
            @click="emit('run-test')"
          >
            Run Test
          </Button>
          <Button variant="secondary" @click="emit('clear')">
            Clear
          </Button>
        </div>

        <!-- Test Result -->
        <div v-if="testResult" class="mt-4">
          <h4 class="text-sm font-medium text-gray-700 mb-2">Result:</h4>
          <div
            class="bg-gray-50 border border-gray-200 rounded-lg p-4 overflow-x-auto"
          >
            <pre class="text-sm text-gray-800 whitespace-pre-wrap font-mono">{{ typeof testResult.output?.result === 'string' ? testResult.output.result : JSON.stringify(testResult.output, null, 2) }}</pre>
          </div>

          <!-- Metrics -->
          <div class="mt-4 grid grid-cols-3 gap-4">
            <div class="bg-blue-50 rounded-lg p-3">
              <div class="text-xs text-blue-600 font-medium">Duration</div>
              <div class="text-lg font-semibold text-blue-900">{{ testResult.metrics.duration_ms }}ms</div>
            </div>
            <div class="bg-green-50 rounded-lg p-3">
              <div class="text-xs text-green-600 font-medium">Tokens Used</div>
              <div class="text-lg font-semibold text-green-900">{{ testResult.metrics.tokens_used }}</div>
            </div>
            <div class="bg-purple-50 rounded-lg p-3">
              <div class="text-xs text-purple-600 font-medium">Cache Hit</div>
              <div class="text-lg font-semibold text-purple-900">{{ testResult.metrics.cache_hit ? 'Yes' : 'No' }}</div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>