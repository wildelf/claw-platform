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
  <div class="bg-white rounded-lg shadow border border-gray-200">
    <div v-if="title" class="px-4 py-3 border-b border-gray-200">
      <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
    </div>
    <div :class="[' rounded-b-lg', { 'p-4': padding }]">
      <slot />
    </div>
  </div>
</template>