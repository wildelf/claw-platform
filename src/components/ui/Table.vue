<script setup lang="ts">
interface Column {
  key: string
  label: string
  width?: string
}

interface Props {
  columns: Column[]
  data: any[]
}

defineProps<Props>()
</script>

<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-border-primary">
      <thead class="bg-bg-secondary">
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            :style="column.width ? { width: column.width } : undefined"
            class="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider"
          >
            {{ column.label }}
          </th>
        </tr>
      </thead>
      <tbody class="bg-bg-primary divide-y divide-border-primary">
        <tr v-if="data.length === 0">
          <td :colspan="columns.length" class="px-4 py-8 text-center text-text-muted">
            No data available
          </td>
        </tr>
        <tr
          v-for="(row, index) in data"
          :key="index"
          class="hover:bg-bg-hover transition-colors"
        >
          <td
            v-for="column in columns"
            :key="column.key"
            class="px-4 py-3 text-sm text-text-primary"
          >
            <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
              {{ row[column.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
