<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Table from '@/components/ui/Table.vue'
import { useSkillsStore } from '@/stores/skills'
import { skillsApi } from '@/api/skills'

const skillsStore = useSkillsStore()

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'status', label: 'Status', width: '120px' },
  { key: 'version', label: 'Version', width: '100px' },
  { key: 'feedback_count', label: 'Feedback', width: '100px' },
  { key: 'actions', label: 'Actions', width: '180px' }
]

onMounted(() => {
  skillsStore.fetchSkills()
})

function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'default' {
  switch (status) {
    case 'trained': return 'success'
    case 'pending': return 'warning'
    case 'needs_review': return 'danger'
    default: return 'default'
  }
}

import { useRouter } from 'vue-router'

const router = useRouter()
const deleting = ref<string | null>(null)

function handleView(skillId: string) {
  router.push(`/skills/${skillId}`)
}

async function handleDelete(skillId: string, skillName: string) {
  if (!confirm(`Delete skill "${skillName}"? This cannot be undone.`)) {
    return
  }
  deleting.value = skillId
  try {
    await skillsApi.delete(skillId)
    await skillsStore.fetchSkills()
  } catch (e) {
    alert('Failed to delete skill')
  } finally {
    deleting.value = null
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">Skills</h1>
      <router-link to="/skills/create">
        <Button variant="primary">Create Skill</Button>
      </router-link>
    </div>

    <Card :padding="false">
      <Table :columns="columns" :data="skillsStore.skills">
        <template #cell-name="{ row }">
          <router-link :to="`/skills/${row.id}`" class="text-blue-600 hover:text-blue-800 font-medium">
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
            <Button variant="ghost" size="sm" @click="handleView(row.id)">View</Button>
            <router-link :to="`/skills/${row.id}/edit`">
              <Button variant="ghost" size="sm">Edit</Button>
            </router-link>
            <Button variant="danger" size="sm" @click="handleDelete(row.id, row.name)" :loading="deleting === row.id">Delete</Button>
          </div>
        </template>
      </Table>
    </Card>
  </div>
</template>