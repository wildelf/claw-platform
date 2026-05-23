<script setup lang="ts">
import AppHeader from './AppHeader.vue'
</script>

<template>
  <div class="min-h-screen bg-bg-primary text-text-primary">
    <AppHeader />
    <main class="pt-14">
      <slot />
    </main>
  </div>
</template>
