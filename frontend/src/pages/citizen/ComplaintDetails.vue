<template>
  <div class="max-w-3xl">
    <div class="flex items-center gap-2 mb-6">
      <RouterLink to="/citizen/track" class="text-primary-600 hover:underline text-sm">← Back to complaints</RouterLink>
    </div>

    <div class="card">
      <div class="flex items-start justify-between mb-4">
        <div>
          <h1 class="text-xl font-bold text-gray-900">Complaint #{{ route.params.id }}</h1>
          <p class="text-gray-500 text-sm mt-1">Submitted on —</p>
        </div>
        <span class="badge-pending">Pending</span>
      </div>

      <div class="space-y-4 border-t border-gray-100 pt-4">
        <div>
          <p class="form-label">Description</p>
          <p class="text-gray-700 text-sm italic">Complaint details — coming soon.</p>
        </div>
        <div>
          <p class="form-label">Location</p>
          <p class="text-gray-700 text-sm">—</p>
        </div>
        <div>
          <p class="form-label">Category</p>
          <p class="text-gray-700 text-sm">—</p>
        </div>
      </div>

      <!-- Progress timeline placeholder -->
      <div class="mt-6 pt-6 border-t border-gray-100">
        <p class="font-medium text-gray-900 mb-3">Status Timeline</p>
        <p class="text-gray-400 text-sm italic">Timeline — coming soon.</p>
      </div>

      <!-- Feedback placeholder -->
      <div class="mt-6 pt-6 border-t border-gray-100">
        <p class="font-medium text-gray-900 mb-3">Feedback</p>
        <p class="text-gray-400 text-sm italic">Feedback submission — coming soon.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { RouterLink, useRoute } from 'vue-router'
const route = useRoute()
</script>
