<script setup lang="ts">
interface Props {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info'
  label?: string
}

withDefaults(defineProps<Props>(), {
  variant: 'default'
})
</script>

<template>
  <span
    role="status"
    :aria-label="label"
    :class="[
      'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
      {
        'bg-bg-tertiary text-text-secondary': variant === 'default',
        'bg-accent-primary/20 text-accent-light': variant === 'success',
        'bg-status-paused/20 text-status-paused': variant === 'warning',
        'bg-status-error/20 text-status-error': variant === 'danger',
        'bg-status-info/20 text-status-info': variant === 'info'
      }
    ]"
  >
    <span v-if="variant !== 'default'" :class="[
      'w-1.5 h-1.5 rounded-full',
      {
        'bg-status-active': variant === 'success',
        'bg-status-paused': variant === 'warning',
        'bg-status-error': variant === 'danger',
        'bg-status-info': variant === 'info'
      }
    ]"></span>
    <slot />
  </span>
</template>
