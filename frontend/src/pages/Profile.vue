<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-2">My Profile</h1>
    <p class="text-gray-500 mb-6">View and update your account details.</p>

    <div class="card max-w-lg">
      <div class="space-y-4">
        <div>
          <p class="form-label">Full Name</p>
          <p class="text-gray-900">{{ authStore.fullName || '—' }}</p>
        </div>
        <div>
          <p class="form-label">Role</p>
          <p class="text-gray-900 capitalize">{{ authStore.userRole?.replace('_', ' ') || '—' }}</p>
        </div>
      </div>

      <div class="mt-6 pt-6 border-t border-gray-100">
        <p class="text-sm text-gray-400 italic">Profile editing — coming soon.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()
</script>
