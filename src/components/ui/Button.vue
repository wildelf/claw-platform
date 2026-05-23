<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  disabled: false,
  loading: false
})
</script>

<template>
  <button
    :class="[
      'inline-flex items-center justify-center font-medium rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-accent-primary/50',
      {
        'btn-primary text-white': variant === 'primary',
        'bg-bg-tertiary hover:bg-border-primary text-text-primary border border-border-primary': variant === 'secondary',
        'bg-red-500/10 hover:bg-red-500/20 text-red-400': variant === 'danger',
        'bg-transparent text-text-secondary hover:text-text-primary hover:bg-bg-tertiary': variant === 'ghost',
        'px-3 py-1.5 text-sm': size === 'sm',
        'py-2 px-4 text-sm': size === 'md',
        'py-2.5 px-6 text-base': size === 'lg',
        'opacity-50 cursor-not-allowed': disabled || loading
      }
    ]"
    :disabled="disabled || loading"
  >
    <svg
      v-if="loading"
      class="animate-spin -ml-1 mr-2 h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        class="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"
      />
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.279 5.83 3.29 7.916l2.71-2.625z"
      />
    </svg>
    <slot />
  </button>
</template>
