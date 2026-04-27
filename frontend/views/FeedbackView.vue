<script setup lang="ts">
import { onMounted } from 'vue'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Table from '@/components/ui/Table.vue'
import Button from '@/components/ui/Button.vue'
import { useFeedbackStore } from '@/stores/feedback'

const feedbackStore = useFeedbackStore()

const columns = [
  { key: 'type', label: 'Type', width: '120px' },
  { key: 'content', label: 'Content' },
  { key: 'timestamp', label: 'Time', width: '180px' },
  { key: 'actions', label: 'Actions', width: '100px' }
]

onMounted(() => {
  feedbackStore.fetchFeedback()
})

function getTypeVariant(type: string): 'success' | 'warning' | 'danger' | 'default' {
  switch (type) {
    case 'positive': return 'success'
    case 'negative': return 'danger'
    case 'neutral': return 'default'
    default: return 'default'
  }
}

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleString()
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">Feedback</h1>
      <Button variant="secondary" @click="feedbackStore.fetchFeedback()">
        Refresh
      </Button>
    </div>

    <Card v-if="feedbackStore.loading" class="text-center py-8">
      <p class="text-gray-500">Loading...</p>
    </Card>

    <Card v-else-if="feedbackStore.error" class="bg-red-50">
      <p class="text-red-600">{{ feedbackStore.error }}</p>
    </Card>

    <Card v-else-if="feedbackStore.feedbackList.length === 0" class="text-center py-8">
      <p class="text-gray-500">No feedback yet</p>
    </Card>

    <Card v-else :padding="false">
      <Table :columns="columns" :data="feedbackStore.feedbackList">
        <template #cell-type="{ row }">
          <Badge :variant="getTypeVariant(row.type)">
            {{ row.type }}
          </Badge>
        </template>
        <template #cell-content="{ row }">
          <span class="truncate block max-w-md">{{ row.content }}</span>
        </template>
        <template #cell-timestamp="{ row }">
          {{ formatTime(row.timestamp) }}
        </template>
        <template #cell-actions="{ row }">
          <Button variant="ghost" size="sm">View</Button>
        </template>
      </Table>
    </Card>
  </div>
</template>
