<script setup lang="ts">
interface Props {
  modelValue?: string | number
  type?: string
  placeholder?: string
  disabled?: boolean
  error?: string
}

defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <div class="w-full">
    <input
      :type="type || 'text'"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      class="w-full px-4 py-2 bg-bg-tertiary border border-border-primary rounded-lg text-sm text-text-primary placeholder-text-muted transition-colors focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary/50"
      :class="{
        'border-status-error': error,
        'cursor-not-allowed opacity-50': disabled
      }"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <p v-if="error" class="mt-1 text-sm text-status-error">{{ error }}</p>
  </div>
</template>
