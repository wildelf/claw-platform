<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import { useAgentsStore } from '@/stores/agents'
import { useSkillsStore } from '@/stores/skills'

const router = useRouter()
const agentsStore = useAgentsStore()
const skillsStore = useSkillsStore()

const recentAgents = computed(() => agentsStore.agents.slice(0, 5))

const skillStats = computed(() => {
  const skills = skillsStore.skills
  return {
    total: skills.length,
    trained: skills.filter(s => s.status === 'trained').length,
    pending: skills.filter(s => s.status === 'pending').length,
    needs_review: skills.filter(s => s.status === 'needs_review').length
  }
})

onMounted(async () => {
  await Promise.all([
    agentsStore.fetchAgents(),
    skillsStore.fetchSkills()
  ])
})

function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'default' {
  switch (status) {
    case 'active': return 'success'
    case 'inactive': return 'warning'
    case 'error': return 'danger'
    default: return 'default'
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
    </div>

    <!-- Recent Agents -->
    <Card title="Recent Agents">
      <div v-if="agentsStore.loading" class="text-center py-4 text-gray-500">Loading...</div>
      <div v-else-if="recentAgents.length === 0" class="text-center py-4 text-gray-500">
        No agents yet
      </div>
      <div v-else class="space-y-3">
        <div
          v-for="agent in recentAgents"
          :key="agent.id"
          class="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
        >
          <div>
            <p class="font-medium text-gray-900">{{ agent.name }}</p>
            <p class="text-sm text-gray-500">{{ agent.description }}</p>
          </div>
          <Badge :variant="getStatusVariant(agent.status)">
            {{ agent.status }}
          </Badge>
        </div>
      </div>
      <template #footer>
        <router-link to="/agents/create">
          <Button variant="primary" size="sm">Create New Agent</Button>
        </router-link>
      </template>
    </Card>

    <!-- Skill Statistics -->
    <Card title="Skill Statistics">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="text-center p-4 bg-gray-50 rounded-lg">
          <p class="text-2xl font-bold text-gray-900">{{ skillStats.total }}</p>
          <p class="text-sm text-gray-500">Total Skills</p>
        </div>
        <div class="text-center p-4 bg-green-50 rounded-lg">
          <p class="text-2xl font-bold text-green-700">{{ skillStats.trained }}</p>
          <p class="text-sm text-green-600">Trained</p>
        </div>
        <div class="text-center p-4 bg-yellow-50 rounded-lg">
          <p class="text-2xl font-bold text-yellow-700">{{ skillStats.pending }}</p>
          <p class="text-sm text-yellow-600">Pending</p>
        </div>
        <div class="text-center p-4 bg-red-50 rounded-lg">
          <p class="text-2xl font-bold text-red-700">{{ skillStats.needs_review }}</p>
          <p class="text-sm text-red-600">Needs Review</p>
        </div>
      </div>
    </Card>
  </div>
</template>