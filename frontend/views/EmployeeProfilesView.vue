<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Table from '@/components/ui/Table.vue'
import Input from '@/components/ui/Input.vue'
import { useEmployeeProfilesStore } from '@/stores/employeeProfiles'

const router = useRouter()
const store = useEmployeeProfilesStore()

const searchQuery = ''
const filteredProfiles = computed(() => {
  if (!searchQuery) return store.profiles
  const q = searchQuery.toLowerCase()
  return store.profiles.filter(p =>
    p.name.toLowerCase().includes(q) ||
    p.role.toLowerCase().includes(q) ||
    p.goal.toLowerCase().includes(q)
  )
})

onMounted(() => {
  store.fetchProfiles()
})

function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'default' {
  switch (status) {
    case 'active': return 'success'
    case 'paused': return 'warning'
    case 'retired': return 'default'
    default: return 'default'
  }
}

function getInitials(name: string): string {
  return name.slice(0, 2).toUpperCase()
}

const avatarColors = [
  'bg-blue-500', 'bg-purple-500', 'bg-green-500', 'bg-orange-500',
  'bg-pink-500', 'bg-indigo-500', 'bg-teal-500', 'bg-red-500'
]

function getAvatarColor(id: string): string {
  const idx = parseInt(id.replace(/-/g, ''), 16) % avatarColors.length
  return avatarColors[idx]
}

async function handleDelete(profileId: string) {
  if (confirm('Are you sure you want to delete this employee profile?')) {
    await store.deleteProfile(profileId)
    await store.fetchProfiles()
  }
}

const columns = [
  { key: 'name', label: 'Employee' },
  { key: 'role', label: 'Role' },
  { key: 'goal', label: 'Goal' },
  { key: 'status', label: 'Status', width: '120px' },
  { key: 'actions', label: 'Actions', width: '200px' }
]
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">数字员工</h1>
        <p class="text-sm text-gray-500 mt-1">管理你的数字员工身份和配置</p>
      </div>
      <router-link to="/employee-profiles/create">
        <Button variant="primary">创建员工</Button>
      </router-link>
    </div>

    <div class="flex gap-4">
      <Input
        v-model="searchQuery"
        placeholder="搜索员工..."
        class="max-w-md"
      />
    </div>

    <Card :padding="false">
      <Table :columns="columns" :data="filteredProfiles">
        <template #cell-name="{ row }">
          <div class="flex items-center gap-3">
            <div :class="['w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold', getAvatarColor(row.id)]">
              {{ getInitials(row.name) }}
            </div>
            <router-link :to="`/employee-profiles/${row.id}`" class="text-blue-600 hover:text-blue-800 font-medium">
              {{ row.name }}
            </router-link>
          </div>
        </template>
        <template #cell-role="{ row }">
          <span class="text-gray-600">{{ row.role || '-' }}</span>
        </template>
        <template #cell-goal="{ row }">
          <span class="text-gray-500 text-sm truncate max-w-xs block">{{ row.goal || '-' }}</span>
        </template>
        <template #cell-status="{ row }">
          <Badge :variant="getStatusVariant(row.status)">
            {{ row.status }}
          </Badge>
        </template>
        <template #cell-actions="{ row }">
          <div class="flex gap-2">
            <Button variant="ghost" size="sm" @click="router.push(`/employee-profiles/${row.id}`)">查看</Button>
            <Button variant="ghost" size="sm" @click="router.push(`/employee-profiles/${row.id}`)">编辑</Button>
            <Button variant="danger" size="sm" @click="handleDelete(row.id)">删除</Button>
          </div>
        </template>
      </Table>
    </Card>

    <div v-if="!store.loading && store.profiles.length === 0" class="text-center py-12">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">暂无员工</h3>
      <p class="mt-1 text-sm text-gray-500">点击"创建员工"开始配置你的数字员工。</p>
    </div>
  </div>
</template>
