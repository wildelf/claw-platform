<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Table from '@/components/ui/Table.vue'
import { useAgentsStore } from '@/stores/agents'

const router = useRouter()
const agentsStore = useAgentsStore()

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'description', label: 'Description' },
  { key: 'status', label: 'Status', width: '120px' },
  { key: 'actions', label: 'Actions', width: '200px' }
]

onMounted(() => {
  agentsStore.fetchAgents()
})

function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'default' {
  switch (status) {
    case 'active': return 'success'
    case 'inactive': return 'warning'
    case 'error': return 'danger'
    default: return 'default'
  }
}

function handleRun(agentId: string) {
  console.log('Run agent:', agentId)
}

function handleEdit(agentId: string) {
  router.push(`/agents/${agentId}/edit`)
}

async function handleDelete(agentId: string) {
  if (confirm('Are you sure you want to delete this agent?')) {
    await agentsStore.deleteAgent(agentId)
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">Agents</h1>
      <router-link to="/agents/create">
        <Button variant="primary">Create Agent</Button>
      </router-link>
    </div>

    <Card :padding="false">
      <Table :columns="columns" :data="agentsStore.agents">
        <template #cell-name="{ row }">
          <router-link :to="`/agents/${row.id}`" class="text-blue-600 hover:text-blue-800 font-medium">
            {{ row.name }}
          </router-link>
        </template>
        <template #cell-status="{ row }">
          <Badge :variant="getStatusVariant(row.status)">
            {{ row.status }}
          </Badge>
        </template>
        <template #cell-actions="{ row }">
          <div class="flex gap-2">
            <Button variant="ghost" size="sm" @click="handleRun(row.id)">Run</Button>
            <Button variant="ghost" size="sm" @click="handleEdit(row.id)">Edit</Button>
            <Button variant="danger" size="sm" @click="handleDelete(row.id)">Delete</Button>
          </div>
        </template>
      </Table>
    </Card>
  </div>
</template>