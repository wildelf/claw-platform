<script setup lang="ts">
import { onMounted, computed } from 'vue'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import { useAgentsStore } from '@/stores/agents'
import { useSkillsStore } from '@/stores/skills'

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
      <h1 class="text-2xl font-bold text-text-primary">Dashboard</h1>
    </div>

    <!-- Recent Agents -->
    <Card title="Recent Agents">
      <div v-if="agentsStore.loading" class="text-center py-4 text-text-muted">Loading...</div>
      <div v-else-if="recentAgents.length === 0" class="text-center py-4 text-text-muted">
        No agents yet
      </div>
      <div v-else class="space-y-3">
        <div
          v-for="agent in recentAgents"
          :key="agent.id"
          class="flex justify-between items-center p-3 bg-bg-secondary rounded-lg"
        >
          <div>
            <p class="font-medium text-text-primary">{{ agent.name }}</p>
            <p class="text-sm text-text-muted">{{ agent.description }}</p>
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
        <div class="text-center p-4 bg-bg-secondary rounded-lg">
          <p class="text-2xl font-bold text-text-primary">{{ skillStats.total }}</p>
          <p class="text-sm text-text-muted">Total Skills</p>
        </div>
        <div class="text-center p-4 bg-status-active/10 rounded-lg">
          <p class="text-2xl font-bold text-status-active">{{ skillStats.trained }}</p>
          <p class="text-sm text-status-active">Trained</p>
        </div>
        <div class="text-center p-4 bg-status-paused/10 rounded-lg">
          <p class="text-2xl font-bold text-status-paused">{{ skillStats.pending }}</p>
          <p class="text-sm text-status-paused">Pending</p>
        </div>
        <div class="text-center p-4 bg-status-error/10 rounded-lg">
          <p class="text-2xl font-bold text-status-error">{{ skillStats.needs_review }}</p>
          <p class="text-sm text-status-error">Needs Review</p>
        </div>
      </div>
    </Card>
  </div>
</template>