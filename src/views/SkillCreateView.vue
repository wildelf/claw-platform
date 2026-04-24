<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'

const router = useRouter()

const form = ref({
  name: '',
  description: ''
})

const generating = ref(false)
const generationOutput = ref('')
const error = ref<string | null>(null)
const outputRef = ref<HTMLPreElement | null>(null)

function appendOutput(text: string) {
  generationOutput.value += text
  if (outputRef.value) {
    outputRef.value.scrollTop = outputRef.value.scrollHeight
  }
}

async function handleSubmit() {
  if (!form.value.name.trim()) {
    error.value = 'Name is required'
    return
  }

  generating.value = true
  generationOutput.value = ''
  error.value = null

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
            appendOutput('\n\nSkill generation completed!')
          }
        } catch (e) {
          console.error('Parse error:', e)
        }
      }
    }
  }

  xhr.onload = () => {
    generating.value = false
    if (xhr.status >= 400) {
      error.value = 'HTTP ' + xhr.status
    } else {
      setTimeout(() => {
        router.push('/skills')
      }, 2000)
    }
  }

  xhr.onerror = () => {
    generating.value = false
    error.value = 'Network error'
  }

  xhr.send(JSON.stringify(form.value))
}

function handleCancel() {
  router.push('/skills')
}
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">Create New Skill</h1>

    <Card v-if="error" class="bg-red-50">
      <p class="text-red-600">{{ error }}</p>
    </Card>

    <Card v-if="generating" class="bg-blue-50">
      <h3 class="text-lg font-medium text-gray-900 mb-2">Generating Skill...</h3>
      <pre ref="outputRef" class="bg-gray-100 p-4 rounded text-sm overflow-x-auto max-h-64 whitespace-pre-wrap">{{ generationOutput || 'Processing...' }}</pre>
      <div class="mt-4 flex justify-end">
        <Button variant="secondary" size="sm" @click="handleCancel">Cancel</Button>
      </div>
    </Card>

    <Card v-else title="Skill Information">
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
          <Input
            v-model="form.name"
            placeholder="e.g., code-review, data-analysis"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Description *</label>
          <textarea
            v-model="form.description"
            placeholder="Briefly describe what this skill does..."
            rows="4"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p class="text-sm text-gray-500 mt-1">
            Describe the skill's purpose and capabilities. The AI will generate the skill code.
          </p>
        </div>

        <div v-if="error" class="text-red-500 text-sm">{{ error }}</div>

        <div class="flex gap-3 pt-4">
          <Button type="submit" variant="primary">
            Create & Generate
          </Button>
          <Button type="button" variant="secondary" @click="handleCancel">
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  </div>
</template>
