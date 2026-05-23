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
  <div class="bg-bg-card border border-border-primary rounded-xl">
    <div v-if="title" class="px-5 py-4 border-b border-border-primary">
      <h3 class="text-lg font-semibold text-text-primary">{{ title }}</h3>
    </div>
    <div :class="[{ 'p-5': padding }]">
      <slot />
    </div>
  </div>
</template>
