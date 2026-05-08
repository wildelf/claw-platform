<script setup lang="ts">
interface Props {
  title?: string
  padding?: boolean
}

withDefaults(defineProps<Props>(), {
  padding: true
})
</script>

<template>
  <div class="bg-[var(--bg-primary)] rounded-lg shadow border border-[var(--border-color)]">
    <div v-if="title" class="px-4 py-3 border-b border-[var(--border-color)]">
      <h3 class="text-lg font-semibold text-[var(--text-primary)]">{{ title }}</h3>
    </div>
    <div :class="[' rounded-b-lg', { 'p-4': padding }]">
      <slot />
    </div>
  </div>
</template>