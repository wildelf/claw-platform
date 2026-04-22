<script setup lang="ts">
import { ref } from 'vue'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'

const sidebarCollapsed = ref(false)

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader @toggle-sidebar="toggleSidebar" />
    <AppSidebar :collapsed="sidebarCollapsed" />
    <main
      :class="[
        'pt-14 transition-all duration-300',
        sidebarCollapsed ? 'ml-16' : 'ml-60'
      ]"
    >
      <div class="p-6">
        <slot />
      </div>
    </main>
  </div>
</template>
