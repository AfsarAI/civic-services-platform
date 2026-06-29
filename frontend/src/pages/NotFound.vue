<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <div class="text-center">
      <p class="text-8xl font-bold text-primary-600 mb-4">404</p>
      <h1 class="text-2xl font-bold text-gray-900 mb-2">Page Not Found</h1>
      <p class="text-gray-500 mb-8">The page you're looking for doesn't exist or has been moved.</p>
      <RouterLink to="/dashboard" class="btn-primary">Back to Dashboard</RouterLink>
    </div>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>
