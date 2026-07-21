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
      <!-- Notifications -->
      <div class="relative" data-notif-root>
        <button
          type="button"
          class="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          @click="toggleNotifPanel"
        >
          <span class="sr-only">Notifications</span>
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
          </svg>
          <span
            v-if="unreadCount > 0"
            class="absolute -top-0.5 -right-0.5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-bold text-white"
          >
            {{ unreadCount > 9 ? '9+' : unreadCount }}
          </span>
        </button>

        <transition name="fade">
          <div
            v-if="notifPanelOpen"
            class="absolute right-0 z-30 mt-2 w-80 max-w-[90vw] rounded-2xl border border-gray-200 bg-white shadow-xl"
          >
            <div class="flex items-center justify-between border-b border-gray-100 px-4 py-3">
              <p class="text-sm font-semibold text-gray-900">Notifications</p>
              <button
                v-if="unreadCount > 0"
                type="button"
                class="text-xs font-semibold text-primary-600 hover:text-primary-700"
                @click="handleMarkAllRead"
              >
                Mark all read
              </button>
            </div>

            <div class="max-h-80 overflow-y-auto">
              <p v-if="loadingNotifs" class="px-4 py-6 text-center text-xs text-gray-400">Loading...</p>
              <p v-else-if="recentNotifs.length === 0" class="px-4 py-6 text-center text-xs text-gray-400">
                You're all caught up.
              </p>
              <button
                v-for="n in recentNotifs"
                :key="n.id"
                type="button"
                class="block w-full border-b border-gray-50 px-4 py-3 text-left transition-colors hover:bg-gray-50"
                :class="{ 'bg-primary-50/40': !n.is_read }"
                @click="handleNotifClick(n)"
              >
                <div class="flex items-start justify-between gap-2">
                  <p class="text-xs font-semibold text-gray-900">{{ n.title }}</p>
                  <span v-if="!n.is_read" class="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-primary-500"></span>
                </div>
                <p class="mt-1 text-xs text-gray-500 line-clamp-2">{{ n.message }}</p>
                <p class="mt-1 text-[11px] text-gray-400">{{ formatDate(n.created_at) }}</p>
              </button>
            </div>

            <div class="border-t border-gray-100 px-4 py-2 text-center">
              <RouterLink
                to="/notifications"
                class="text-xs font-semibold text-primary-600 hover:text-primary-700"
                @click="notifPanelOpen = false"
              >
                View all notifications
              </RouterLink>
            </div>
          </div>
        </transition>
      </div>

      <!-- User menu placeholder -->
      <div class="flex items-center gap-2 cursor-pointer hover:bg-gray-100 rounded-lg px-3 py-2 transition-colors">
        <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-semibold text-sm overflow-hidden">
          <img v-if="avatarUrl" :src="avatarUrl" alt="Profile photo" class="h-full w-full object-cover" />
          <span v-else>{{ authStore.fullName.charAt(0) || 'U' }}</span>
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
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import notificationService from '@/services/notification.service'

const emit = defineEmits(['toggle-sidebar'])
const authStore = useAuthStore()
const router = useRouter()

const avatarUrl = computed(() => {
  const url = authStore.user?.avatar_url
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1'
  return `${apiBase.replace(/\/api\/v1$/, '')}${url}`
})

const notifPanelOpen = ref(false)
const loadingNotifs = ref(false)
const unreadCount = ref(0)
const recentNotifs = ref([])
let pollInterval = null

async function fetchUnreadCount() {
  try {
    const response = await notificationService.getUnreadCount()
    unreadCount.value = response?.data?.count || 0
  } catch {
    // Silently ignore — header badge is best-effort.
  }
}

async function fetchRecentNotifs() {
  loadingNotifs.value = true
  try {
    const response = await notificationService.getNotifications({ page: 1, per_page: 8 })
    recentNotifs.value = response?.data?.items || []
  } catch {
    recentNotifs.value = []
  } finally {
    loadingNotifs.value = false
  }
}

function toggleNotifPanel() {
  notifPanelOpen.value = !notifPanelOpen.value
  if (notifPanelOpen.value) {
    fetchRecentNotifs()
  }
}

async function handleNotifClick(notification) {
  if (!notification.is_read) {
    try {
      await notificationService.markAsRead(notification.id)
      notification.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch {
      // Ignore — non-critical UI action.
    }
  }
}

async function handleMarkAllRead() {
  try {
    await notificationService.markAllAsRead()
    recentNotifs.value = recentNotifs.value.map((n) => ({ ...n, is_read: true }))
    unreadCount.value = 0
  } catch {
    // Ignore — non-critical UI action.
  }
}

function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function handleClickOutside(event) {
  if (!notifPanelOpen.value) return
  const root = event.target.closest('[data-notif-root]')
  if (!root) {
    notifPanelOpen.value = false
  }
}

async function handleLogout() {
  await authStore.logout()
  router.push({ name: 'login' })
}

onMounted(() => {
  fetchUnreadCount()
  pollInterval = window.setInterval(fetchUnreadCount, 30000)
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  window.clearInterval(pollInterval)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

