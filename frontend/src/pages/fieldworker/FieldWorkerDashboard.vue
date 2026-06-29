<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">My Assigned Tasks</h1>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
      <div v-for="stat in stats" :key="stat.label" class="card text-center">
        <p class="text-3xl font-bold" :class="stat.color">{{ stat.value }}</p>
        <p class="text-sm text-gray-500 mt-1">{{ stat.label }}</p>
      </div>
    </div>

    <!-- Task list placeholder -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-gray-900">Assigned Complaints</h2>
        <select class="form-input w-36 text-sm">
          <option value="">All Statuses</option>
          <option value="assigned">Assigned</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
        </select>
      </div>
      <p class="text-gray-400 italic text-sm text-center py-8">
        Task list — coming soon.
      </p>
    </div>
  </div>
</template>

<script setup>
const stats = [
  { label: 'Total Assigned', value: 0, color: 'text-blue-600' },
  { label: 'In Progress', value: 0, color: 'text-orange-600' },
  { label: 'Completed', value: 0, color: 'text-green-600' },
]
</script>
