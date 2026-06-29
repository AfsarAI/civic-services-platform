<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-2">Track Complaints</h1>
    <p class="text-gray-500 text-sm mb-6">Search and filter your submitted complaints.</p>

    <!-- Search bar placeholder -->
    <div class="card mb-4">
      <div class="flex gap-3">
        <input
          v-model="search"
          type="text"
          class="form-input flex-1"
          placeholder="Search by title or ID…"
        />
        <select v-model="statusFilter" class="form-input w-40">
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="assigned">Assigned</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </div>
    </div>

    <!-- Complaints table placeholder -->
    <div class="card">
      <p class="text-gray-400 italic text-sm text-center py-8">
        Complaint tracking — coming soon.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const search = ref('')
const statusFilter = ref('')
</script>
