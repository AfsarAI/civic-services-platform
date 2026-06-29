<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>
    <p class="text-gray-500 mb-4">Welcome back, <strong>{{ authStore.fullName }}</strong>.</p>

    <!-- Role-based redirect notice -->
    <div class="card">
      <p class="text-gray-600">
        Redirecting to your
        <span class="font-medium capitalize">{{ authStore.userRole?.replace('_', ' ') }}</span>
        dashboard…
      </p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

onMounted(() => {
  const role = authStore.userRole
  if (role === 'citizen')       router.replace({ name: 'citizen-dashboard' })
  else if (role === 'administrator') router.replace({ name: 'admin-dashboard' })
  else if (role === 'field_worker')  router.replace({ name: 'fieldworker-dashboard' })
})
</script>
