<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAgentsStore } from '@/stores/agents'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'

const route = useRoute()
const router = useRouter()
const agentsStore = useAgentsStore()

const form = ref({
  name: '',
  description: '',
  role: '',
  goal: '',
  backstory: '',
})

const loading = ref(false)
const saving = ref(false)
const error = ref('')

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    await agentsStore.fetchAgent(route.params.id as string)
    const agent = agentsStore.currentAgent
    if (agent) {
      form.value = {
        name: agent.name,
        description: agent.description,
        role: agent.role,
        goal: agent.goal,
        backstory: agent.backstory,
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
</script>

<template>
  <div>
    <h1 class="text-2xl font-semibold mb-6">Edit Agent</h1>

    <Card v-if="loading" class="text-center py-8">
      <p class="text-gray-500">Loading...</p>
    </Card>

    <Card v-else-if="error" class="text-center py-8">
      <p class="text-red-500">{{ error }}</p>
    </Card>

    <Card v-else>
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input
            v-model="form.name"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
            required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            v-model="form.description"
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
            rows="3"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Role</label>
          <input
            v-model="form.role"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Goal</label>
          <textarea
            v-model="form.goal"
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
            rows="2"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Backstory</label>
          <textarea
            v-model="form.backstory"
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
            rows="3"
          />
        </div>

        <div v-if="error" class="text-red-500 text-sm">{{ error }}</div>

        <div class="flex space-x-2">
          <Button type="submit" :loading="saving">Save</Button>
          <Button type="button" variant="secondary" @click="router.back()">Cancel</Button>
        </div>
      </form>
    </Card>
  </div>
</template>
