<template>
  <header class="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-6 shadow-sm">
    <!-- Brand -->
    <div class="flex items-center gap-3">
      <button
        type="button"
        class="md:hidden inline-flex items-center justify-center rounded-lg p-2 text-gray-600 hover:bg-gray-100"
        @click="emit('toggle-sidebar')"
        aria-label="Toggle navigation menu"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
        </svg>
      </button>

      <RouterLink to="/dashboard" class="flex items-center gap-2 text-primary-700 font-bold text-lg">
        <span class="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center text-white text-sm font-bold">CS</span>
        Civic Services
      </RouterLink>
    </div>

    <!-- Right section -->
    <div class="flex items-center gap-4">
      <!-- Notifications placeholder -->
      <button class="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
        <span class="sr-only">Notifications</span>
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
        </svg>
      </button>

      <!-- User menu placeholder -->
      <div class="flex items-center gap-2 cursor-pointer hover:bg-gray-100 rounded-lg px-3 py-2 transition-colors">
        <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-semibold text-sm">
          {{ authStore.fullName.charAt(0) || 'U' }}
        </div>
        <div class="hidden sm:block">
          <p class="text-sm font-medium text-gray-900">{{ authStore.fullName || 'User' }}</p>
          <p class="text-xs text-gray-500 capitalize">
            {{ authStore.userRole?.replace('_', ' ') || '' }}
            <span v-if="authStore.adminLevel">
              · {{ authStore.adminLevel.replace('_', ' ') }}
            </span>
          </p>
        </div>
      </div>

      <!-- Logout -->
      <button
        @click="handleLogout"
        class="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
        title="Logout"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup>
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const emit = defineEmits(['toggle-sidebar'])
const authStore = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await authStore.logout()
  router.push({ name: 'login' })
}
</script>
