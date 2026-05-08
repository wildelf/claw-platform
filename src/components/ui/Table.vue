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

const props = defineProps<Props>()
</script>

<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-[var(--border-color)]">
      <thead class="bg-[var(--bg-secondary)]">
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            :style="column.width ? { width: column.width } : undefined"
            class="px-4 py-3 text-left text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider"
          >
            {{ column.label }}
          </th>
        </tr>
      </thead>
      <tbody class="bg-[var(--bg-primary)] divide-y divide-[var(--border-color)]">
        <tr v-if="props.data.length === 0">
          <td :colspan="columns.length" class="px-4 py-8 text-center text-[var(--text-muted)]">
            No data available
          </td>
        </tr>
        <tr
          v-for="(row, index) in props.data"
          :key="index"
          class="hover:bg-[var(--bg-secondary)]"
        >
          <td
            v-for="column in columns"
            :key="column.key"
            class="px-4 py-3 text-sm text-[var(--text-primary)]"
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