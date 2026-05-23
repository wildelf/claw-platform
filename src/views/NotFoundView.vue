<script setup lang="ts">
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'

const router = useRouter()
</script>

<template>
  <div class="min-h-[60vh] flex items-center justify-center">
    <Card class="text-center max-w-md">
      <h1 class="text-6xl font-bold text-text-primary mb-4">404</h1>
      <p class="text-xl text-text-secondary mb-6">Page not found</p>
      <p class="text-text-muted mb-8">The page you're looking for doesn't exist or has been moved.</p>
      <Button variant="primary" @click="router.push('/')">
        Back to Dashboard
      </Button>
    </Card>
  </div>
</template>
