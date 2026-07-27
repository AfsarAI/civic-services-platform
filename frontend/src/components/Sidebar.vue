<template>
  <aside class="w-64 bg-white border-r border-gray-200 min-h-full hidden md:flex flex-col">
    <nav class="flex-1 p-4 space-y-1">
      <!-- Common links -->
      <RouterLink
        v-for="link in filteredLinks"
        :key="link.name"
        :to="link.to"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="isActive(link.to)
          ? 'bg-primary-50 text-primary-700'
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'"
      >
        <span class="w-5 h-5 flex-shrink-0" v-html="link.icon"></span>
        {{ link.label }}
      </RouterLink>
    </nav>
  </aside>

  <transition name="fade">
    <div v-if="mobileOpen" class="fixed inset-0 z-40 md:hidden">
      <button
        type="button"
        class="absolute inset-0 bg-slate-900/45"
        @click="emit('close')"
        aria-label="Close navigation menu"
      ></button>

      <aside class="absolute left-0 top-0 h-full w-72 max-w-[85vw] bg-white border-r border-gray-200 shadow-xl">
        <div class="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <p class="text-sm font-semibold text-slate-700">Navigation</p>
          <button
            type="button"
            class="inline-flex items-center justify-center rounded-lg p-2 text-gray-600 hover:bg-gray-100"
            @click="emit('close')"
            aria-label="Close navigation"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <nav class="p-4 space-y-1 overflow-y-auto h-[calc(100%-3.5rem)]">
          <RouterLink
            v-for="link in filteredLinks"
            :key="`mobile-${link.name || link.to}`"
            :to="link.to"
            class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="isActive(link.to)
              ? 'bg-primary-50 text-primary-700'
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'"
            @click="emit('close')"
          >
            <span class="w-5 h-5 flex-shrink-0" v-html="link.icon"></span>
            {{ link.label }}
          </RouterLink>
        </nav>
      </aside>
    </div>
  </transition>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

defineProps({
  mobileOpen: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close'])
const authStore = useAuthStore()
const route = useRoute()

const allLinks = [
  {
    label: 'Dashboard',
    to: '/dashboard',
    roles: ['citizen', 'administrator', 'field_worker'],
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7h18M3 12h18M3 17h18"/></svg>',
  },
  {
    label: 'My Complaints',
    to: '/citizen/dashboard',
    roles: ['citizen'],
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>',
  },
  {
    label: 'Report Issue',
    to: '/citizen/report',
    roles: ['citizen'],
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>',
  },
  {
    label: 'Track Complaint',
    to: '/citizen/track',
    roles: ['citizen'],
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a2 2 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>',
  },
  {
    label: 'All Complaints',
    to: '/admin/dashboard',
    roles: ['administrator'],
    adminLevels: ['system', 'municipal'],
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>',
  },
  {
    label: 'Monitor Progress',
    to: '/admin/assignments',
    roles: ['administrator'],
    adminLevels: ['system', 'municipal'],
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 19V5m0 14h16M7 15l3-3 3 2 5-7"/></svg>',
  },
  {
    label: 'Municipal Admins',
    to: '/admin/municipal-administrators',
    roles: ['administrator'],
    adminLevels: ['system'],
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5V4H2v16h5m10 0v-2a4 4 0 00-4-4H11a4 4 0 00-4 4v2m10 0H7m8-10a3 3 0 11-6 0 3 3 0 016 0z"/></svg>',
  },
  {
    label: 'Field Workers',
    to: '/admin/field-workers',
    roles: ['administrator'],
    adminLevels: ['municipal'],
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2m-3 7l2 2 4-4"/></svg>',
  },
  {
    label: 'Reports',
    to: '/admin/reports',
    roles: ['administrator'],
    adminLevels: ['system', 'municipal'],
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>',
  },
  {
    label: 'System Settings',
    to: '/admin/settings',
    roles: ['administrator'],
    adminLevels: ['system'],
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>',
  },
  {
    label: 'My Tasks',
    to: '/fieldworker/dashboard',
    roles: ['field_worker'],
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2m-3 7l2 2 4-4"/></svg>',
  },
  {
    label: 'Work History',
    to: '/fieldworker/history',
    roles: ['field_worker'],
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
  },
  {
    label: 'Profile',
    to: '/profile',
    roles: ['citizen', 'administrator', 'field_worker'],
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>',
  },
  {
    label: 'Notifications',
    to: '/notifications',
    roles: ['citizen', 'administrator', 'field_worker'],
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>',
  },
]

const filteredLinks = computed(() =>
  allLinks.filter((link) => {
    if (!link.roles.includes(authStore.userRole)) {
      return false
    }
    if (!link.adminLevels) {
      return true
    }
    return link.adminLevels.includes(authStore.adminLevel)
  }),
)

function isActive(path) {
  return route.path.startsWith(path)
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
