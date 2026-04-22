<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import { useAgentsStore } from '@/stores/agents'

const route = useRoute()
const router = useRouter()
const agentsStore = useAgentsStore()

const agentId = computed(() => route.params.id as string)
const agent = computed(() => agentsStore.currentAgent)

onMounted(async () => {
  await agentsStore.fetchAgent(agentId.value)
})

function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'default' {
  switch (status) {
    case 'active': return 'success'
    case 'inactive': return 'warning'
    case 'error': return 'danger'
    default: return 'default'
  }
}

function handleRun() {
  console.log('Run agent:', agentId.value)
}

function handleEdit() {
  router.push(`/agents/${agentId.value}/edit`)
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">Agent Details</h1>
      <div class="flex gap-2">
        <Button variant="primary" @click="handleRun">Run Agent</Button>
        <Button variant="secondary" @click="handleEdit">Edit</Button>
      </div>
    </div>

    <div v-if="agentsStore.loading" class="text-center py-8 text-gray-500">Loading...</div>
    <div v-else-if="!agent" class="text-center py-8 text-gray-500">Agent not found</div>
    <template v-else>
      <Card>
        <div class="space-y-4">
          <div class="flex justify-between items-start">
            <div>
              <h2 class="text-xl font-semibold text-gray-900">{{ agent.name }}</h2>
              <p class="text-gray-500 mt-1">{{ agent.description }}</p>
            </div>
            <Badge :variant="getStatusVariant(agent.status)" class="text-sm">
              {{ agent.status }}
            </Badge>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200">
            <div>
              <p class="text-sm font-medium text-gray-500">Role</p>
              <p class="text-gray-900">{{ agent.role || 'Not specified' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">Goal</p>
              <p class="text-gray-900">{{ agent.goal || 'Not specified' }}</p>
            </div>
          </div>

          <div class="pt-4 border-t border-gray-200">
            <p class="text-sm font-medium text-gray-500">Backstory</p>
            <p class="text-gray-900 mt-1">{{ agent.backstory || 'Not specified' }}</p>
          </div>
        </div>
      </Card>
    </template>
  </div>
</template>