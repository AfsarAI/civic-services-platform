<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Administrator Dashboard</h1>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div v-for="stat in stats" :key="stat.label" class="card text-center">
        <p class="text-3xl font-bold" :class="stat.color">{{ stat.value }}</p>
        <p class="text-sm text-gray-500 mt-1">{{ stat.label }}</p>
      </div>
    </div>

    <!-- Complaints management placeholder -->
    <div class="card mb-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-gray-900">Recent Complaints</h2>
        <div class="flex gap-2">
          <select class="form-input w-36 text-sm">
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="assigned">Assigned</option>
          </select>
          <select class="form-input w-36 text-sm">
            <option value="">All Categories</option>
            <option value="pothole">Pothole</option>
          </select>
        </div>
      </div>
      <p class="text-gray-400 italic text-sm text-center py-8">
        Complaint management table — coming soon.
      </p>
    </div>
  </div>
</template>

<script setup>
const stats = [
  { label: 'Total', value: 0, color: 'text-gray-800' },
  { label: 'Pending', value: 0, color: 'text-yellow-600' },
  { label: 'In Progress', value: 0, color: 'text-blue-600' },
  { label: 'Resolved', value: 0, color: 'text-green-600' },
]
</script>
