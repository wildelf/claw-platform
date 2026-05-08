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
      :class="[
        'w-full px-3 py-2 border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500',
        {
          'border-[var(--border-color)]': !error,
          'border-[var(--color-danger)]': error,
          'bg-[var(--bg-tertiary)] cursor-not-allowed': disabled,
          'bg-[var(--bg-primary)]': !disabled
        }
      ]"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <p v-if="error" class="mt-1 text-sm text-[var(--color-danger)]">{{ error }}</p>
  </div>
</template>