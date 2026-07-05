<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-2">Administrator Dashboard</h1>
    <p class="text-gray-500 mb-6">
      Signed in as
      <span class="font-medium capitalize">{{ authStore.adminLevel || 'administrator' }}</span>
      administrator.
    </p>

    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
      <div v-for="stat in stats" :key="stat.label" class="card text-center">
        <p class="text-3xl font-bold" :class="stat.color">{{ stat.value }}</p>
        <p class="text-sm text-gray-500 mt-1">{{ stat.label }}</p>
      </div>
    </div>

    <div v-if="authStore.isSystemAdmin" class="card mb-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-gray-900">System Administrator Scope</h2>
        <RouterLink
          to="/admin/municipal-administrators"
          class="btn-secondary px-4 py-2 text-sm"
        >
          Manage Municipal Admins
        </RouterLink>
      </div>
      <p class="text-gray-600 text-sm">
        You can create, manage, and disable municipal administrators and access platform-wide reports.
      </p>
    </div>

    <div v-else-if="authStore.isMunicipalAdmin" class="card mb-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-gray-900">Municipal Administrator Scope</h2>
      </div>
      <p class="text-gray-600 text-sm">
        Your account is assigned to
        <span class="font-medium">{{ authStore.cityName || 'a city' }}</span>.
        Global reports and cross-city administration remain restricted to the system administrator.
      </p>
    </div>

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
        Complaint management table - coming soon.
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const stats = computed(() => {
  if (authStore.isSystemAdmin) {
    return [
      { label: 'Cities', value: 0, color: 'text-gray-800' },
      { label: 'Municipal Admins', value: 0, color: 'text-blue-600' },
      { label: 'Open Complaints', value: 0, color: 'text-yellow-600' },
      { label: 'Resolved', value: 0, color: 'text-green-600' },
    ]
  }

  return [
    { label: 'Assigned City', value: authStore.cityName || '-', color: 'text-gray-800' },
    { label: 'Access Scope', value: 'City', color: 'text-blue-600' },
    { label: 'Reports Access', value: 'No', color: 'text-yellow-600' },
    { label: 'Account Status', value: 'Active', color: 'text-green-600' },
  ]
})
</script>
