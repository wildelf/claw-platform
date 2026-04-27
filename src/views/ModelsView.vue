<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Table from '@/components/ui/Table.vue'
import { useModelsStore } from '@/stores/models'

const router = useRouter()
const modelsStore = useModelsStore()

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'type', label: 'Provider', width: '120px' },
  { key: 'model', label: 'Model' },
  { key: 'base_url', label: 'Base URL' },
  { key: 'actions', label: 'Actions', width: '200px' }
]

onMounted(() => {
  modelsStore.fetchModels()
})

function handleEdit(modelId: string) {
  router.push(`/models/${modelId}/edit`)
}

async function handleDelete(modelId: string) {
  if (confirm('Are you sure you want to delete this model config?')) {
    await modelsStore.deleteModel(modelId)
  }
}

function getProviderBadge(type: string): string {
  switch (type) {
    case 'openai': return 'blue'
    case 'anthropic': return 'purple'
    case 'deepseek': return 'green'
    default: return 'gray'
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">Model Configurations</h1>
      <router-link to="/models/create">
        <Button variant="primary">Create Model</Button>
      </router-link>
    </div>

    <Card v-if="modelsStore.loading" class="text-center py-8 text-gray-500">
      Loading...
    </Card>

    <Card v-else-if="modelsStore.models.length === 0" class="text-center py-8">
      <p class="text-gray-500 mb-4">No model configurations yet</p>
      <router-link to="/models/create">
        <Button variant="primary">Create Your First Model</Button>
      </router-link>
    </Card>

    <Card v-else :padding="false">
      <Table :columns="columns" :data="modelsStore.models">
        <template #cell-name="{ row }">
          <span class="font-medium">{{ row.name }}</span>
        </template>
        <template #cell-type="{ row }">
          <span class="px-2 py-1 rounded text-xs" :class="`bg-${getProviderBadge(row.type)}-100 text-${getProviderBadge(row.type)}-800`">
            {{ row.type }}
          </span>
        </template>
        <template #cell-model="{ row }">
          <span class="text-gray-600">{{ row.model }}</span>
        </template>
        <template #cell-base_url="{ row }">
          <span class="text-gray-500 text-sm">{{ row.base_url || '-' }}</span>
        </template>
        <template #cell-actions="{ row }">
          <div class="flex gap-2">
            <Button variant="ghost" size="sm" @click="handleEdit(row.id)">Edit</Button>
            <Button variant="danger" size="sm" @click="handleDelete(row.id)">Delete</Button>
          </div>
        </template>
      </Table>
    </Card>
  </div>
</template>