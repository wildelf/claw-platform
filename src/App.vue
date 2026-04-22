<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'

const route = useRoute()
const isAuthPage = computed(() =>
  ['/login', '/register'].includes(route.path)
)
</script>

<template>
  <AppLayout v-if="!isAuthPage">
    <RouterView />
  </AppLayout>
  <RouterView v-else />
</template>