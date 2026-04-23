<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { useSkillsStore } from '@/stores/skills'

const route = useRoute()
const router = useRouter()
const skillsStore = useSkillsStore()

const skillId = route.params.id as string

const form = ref({
  name: '',
  description: ''
})

const loading = ref(false)
const saving = ref(false)
const error = ref('')

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
  } catch (e) {
    error.value = 'Failed to load skill'
  } finally {
    loading.value = false
  }
})

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
  <div class="max-w-2xl mx-auto space-y-6">
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

    <Card v-else title="Skill Information">
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
            rows="4"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div v-if="error" class="text-red-500 text-sm">{{ error }}</div>

        <div class="flex gap-3 pt-4">
          <Button type="submit" :loading="saving">Save</Button>
          <Button type="button" variant="secondary" @click="handleCancel">Cancel</Button>
        </div>
      </form>
    </Card>
  </div>
</template>
