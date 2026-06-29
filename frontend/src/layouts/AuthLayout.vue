<template>
  <div class="min-h-screen bg-gradient-to-br from-primary-600 to-primary-900 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <!-- Logo / Brand -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-white">Civic Services</h1>
        <p class="text-primary-200 mt-1">Platform</p>
      </div>
      <!-- Page content (login form) -->
      <RouterView />
    </div>
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
</script>
