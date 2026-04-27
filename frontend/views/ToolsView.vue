<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Table from '@/components/ui/Table.vue'
import { useToolsStore } from '@/stores/tools'

const router = useRouter()
const toolsStore = useToolsStore()

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'description', label: 'Description' },
  { key: 'type', label: 'Type', width: '120px' },
  { key: 'actions', label: 'Actions', width: '150px' }
]

onMounted(() => {
  toolsStore.fetchTools()
})

function getTypeVariant(type: string): 'success' | 'warning' | 'danger' | 'default' {
  switch (type) {
    case 'MCP': return 'success'
    case 'CUSTOM': return 'default'
    default: return 'default'
  }
}

function handleView(toolId: string) {
  console.log('View tool:', toolId)
}

function handleEdit(toolId: string) {
  console.log('Edit tool:', toolId)
}

function handleDelete(toolId: string) {
  if (confirm('Are you sure you want to delete this tool?')) {
    toolsStore.deleteTool(toolId)
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">Tools</h1>
      <router-link to="/tools/create">
        <Button variant="primary">Create Tool</Button>
      </router-link>
    </div>

    <Card v-if="toolsStore.loading" class="text-center py-8">
      <p class="text-gray-500">Loading...</p>
    </Card>

    <Card v-else-if="toolsStore.error" class="bg-red-50">
      <p class="text-red-600">{{ toolsStore.error }}</p>
    </Card>

    <Card v-else-if="toolsStore.tools.length === 0" class="text-center py-8">
      <p class="text-gray-500">No tools yet</p>
      <router-link to="/tools/create" class="text-blue-600 hover:text-blue-800 mt-2 inline-block">
        Create your first tool
      </router-link>
    </Card>

    <Card v-else :padding="false">
      <Table :columns="columns" :data="toolsStore.tools">
        <template #cell-name="{ row }">
          <span class="font-medium text-gray-900">{{ row.name }}</span>
        </template>
        <template #cell-description="{ row }">
          <span class="text-gray-500 truncate block max-w-md">{{ row.description || 'No description' }}</span>
        </template>
        <template #cell-type="{ row }">
          <Badge :variant="getTypeVariant(row.type)">
            {{ row.type }}
          </Badge>
        </template>
        <template #cell-actions="{ row }">
          <div class="flex gap-2">
            <Button variant="ghost" size="sm" @click="handleView(row.id)">View</Button>
            <Button variant="ghost" size="sm" @click="handleEdit(row.id)">Edit</Button>
            <Button variant="ghost" size="sm" class="text-red-600" @click="handleDelete(row.id)">Delete</Button>
          </div>
        </template>
      </Table>
    </Card>
  </div>
</template>
