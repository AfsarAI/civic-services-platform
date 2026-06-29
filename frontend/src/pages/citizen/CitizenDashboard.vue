<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">My Complaints</h1>
        <p class="text-gray-500 text-sm mt-1">Track all the issues you've reported.</p>
      </div>
      <RouterLink to="/citizen/report" class="btn-primary">+ Report Issue</RouterLink>
    </div>

    <!-- Stats placeholder -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div v-for="stat in stats" :key="stat.label" class="card text-center">
        <p class="text-3xl font-bold text-primary-600">{{ stat.value }}</p>
        <p class="text-sm text-gray-500 mt-1">{{ stat.label }}</p>
      </div>
    </div>

    <!-- Complaints list placeholder -->
    <div class="card">
      <p class="text-gray-400 italic text-sm text-center py-8">
        No complaints yet. <RouterLink to="/citizen/report" class="text-primary-600 hover:underline">Report your first issue</RouterLink>.
      </p>
    </div>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'

const stats = [
  { label: 'Total', value: 0 },
  { label: 'Pending', value: 0 },
  { label: 'In Progress', value: 0 },
  { label: 'Resolved', value: 0 },
]
</script>
