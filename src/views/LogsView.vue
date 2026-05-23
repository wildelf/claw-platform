<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import { useLogsStore } from '@/stores/logs'
import { useAgentsStore } from '@/stores/agents'

const logsStore = useLogsStore()
const agentsStore = useAgentsStore()

const filterAgentId = ref('')
const filterSessionId = ref('')
const filterActionType = ref('')
const filterToolName = ref('')
const offset = ref(0)
const limit = ref(100)

const actionTypeOptions = [
  { value: '', label: 'All' },
  { value: 'mcp_call', label: 'MCP Call' },
  { value: 'skill_reading', label: 'Skill Reading' },
  { value: 'decision_branch', label: 'Decision Branch' },
  { value: 'llm_response', label: 'LLM Response' },
  { value: 'agent_start', label: 'Agent Start' },
  { value: 'agent_end', label: 'Agent End' },
]

const agentOptions = computed(() => [
  { value: '', label: 'All Agents' },
  ...agentsStore.agents.map(a => ({ value: a.id, label: a.name })),
])

async function handleQuery() {
  await logsStore.queryLogs({
    agent_id: filterAgentId.value || undefined,
    session_id: filterSessionId.value || undefined,
    action_type: filterActionType.value || undefined,
    tool_name: filterToolName.value || undefined,
    offset: offset.value,
    limit: limit.value,
  })
}

function getActionVariant(type: string): 'success' | 'warning' | 'danger' | 'default' {
  switch (type) {
    case 'mcp_call': return 'success'
    case 'skill_reading': return 'warning'
    case 'decision_branch': return 'default'
    case 'llm_response': return 'default'
    case 'agent_start': return 'success'
    case 'agent_end': return 'success'
    default: return 'default'
  }
}

onMounted(async () => {
  await agentsStore.fetchAgents()
  await handleQuery()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-text-primary">Audit Logs</h1>
      <Button variant="secondary" @click="handleQuery">Refresh</Button>
    </div>

    <!-- Filters -->
    <Card title="Filters">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Select
          v-model="filterAgentId"
          :options="agentOptions"
          label="Agent"
        />
        <Input
          v-model="filterSessionId"
          label="Session ID"
          placeholder="Filter by session..."
        />
        <Select
          v-model="filterActionType"
          :options="actionTypeOptions"
          label="Action Type"
        />
        <Input
          v-model="filterToolName"
          label="Tool Name"
          placeholder="Filter by tool..."
        />
      </div>
      <div class="mt-4 flex justify-end">
        <Button variant="primary" @click="handleQuery">Query Logs</Button>
      </div>
    </Card>

    <!-- Results -->
    <Card v-if="logsStore.loading" class="text-center py-8">
      <p class="text-text-muted">Loading...</p>
    </Card>

    <Card v-else-if="logsStore.error" class="bg-status-error/10">
      <p class="text-status-error">{{ logsStore.error }}</p>
    </Card>

    <Card v-else-if="logsStore.entries.length === 0" class="text-center py-8">
      <p class="text-text-muted">No log entries found</p>
    </Card>

    <Card v-else :padding="false">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-border-primary">
          <thead class="bg-bg-tertiary">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Timestamp</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Agent</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Action</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Tool</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Context</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Error</th>
            </tr>
          </thead>
          <tbody class="bg-bg-primary divide-y divide-border-primary">
            <tr v-for="entry in logsStore.entries" :key="entry.id" class="hover:bg-bg-hover">
              <td class="px-4 py-3 text-sm text-text-muted whitespace-nowrap">
                {{ new Date(entry.timestamp).toLocaleString() }}
              </td>
              <td class="px-4 py-3 text-sm text-text-primary whitespace-nowrap">
                {{ entry.agent_id.substring(0, 8) }}...
              </td>
              <td class="px-4 py-3">
                <Badge :variant="getActionVariant(entry.action_type)">
                  {{ entry.action_type }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-sm text-text-muted whitespace-nowrap">
                {{ entry.tool_name || '-' }}
              </td>
              <td class="px-4 py-3 text-sm text-text-muted max-w-xs truncate">
                {{ entry.decision_context || '-' }}
              </td>
              <td class="px-4 py-3 text-sm">
                <span v-if="entry.error" class="text-status-error">{{ entry.error }}</span>
                <span v-else class="text-text-muted">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>
  </div>
</template>
