<template>
  <div class="mx-auto max-w-3xl space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 tracking-tight">Notifications</h1>
        <p class="text-slate-500 text-sm mt-0.5">Updates about your complaints and assignments.</p>
      </div>
      <button
        v-if="notifications.some((n) => !n.is_read)"
        type="button"
        class="btn-secondary px-4 py-2 text-sm"
        :disabled="isMarkingAll"
        @click="handleMarkAllRead"
      >
        {{ isMarkingAll ? 'Marking...' : 'Mark all read' }}
      </button>
    </div>

    <div class="card space-y-4">
      <div class="flex items-center justify-between gap-3">
        <h2 class="text-sm font-semibold text-slate-900">All Notifications</h2>
        <select v-model="unreadOnly" class="form-input w-40 text-sm" @change="loadNotifications(1)">
          <option :value="false">All</option>
          <option :value="true">Unread only</option>
        </select>
      </div>

      <div v-if="loading" class="space-y-3 py-6">
        <div v-for="n in 4" :key="n" class="animate-pulse flex gap-4">
          <div class="h-12 bg-slate-100 rounded-lg flex-1"></div>
        </div>
      </div>

      <div v-else-if="notifications.length === 0" class="text-center py-10">
        <p class="text-slate-500 text-sm font-medium">No notifications yet</p>
        <p class="text-slate-400 text-xs mt-1">You'll see updates here as your complaints progress.</p>
      </div>

      <ul v-else class="divide-y divide-slate-100">
        <li v-for="n in notifications" :key="n.id" class="py-3">
          <button
            type="button"
            class="flex w-full items-start justify-between gap-3 rounded-xl px-2 py-1 text-left transition-colors hover:bg-slate-50"
            :class="{ 'bg-primary-50/40': !n.is_read }"
            @click="handleNotifClick(n)"
          >
            <div class="min-w-0">
              <p class="text-sm font-semibold text-slate-900">{{ n.title }}</p>
              <p class="mt-1 text-sm text-slate-600">{{ n.message }}</p>
              <div class="mt-1 flex items-center gap-2">
                <span v-if="n.related_complaint_id" class="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-600">
                  Complaint #{{ n.related_complaint_id }}
                </span>
                <p class="text-xs text-slate-400">{{ formatDate(n.created_at) }}</p>
              </div>
            </div>
            <span v-if="!n.is_read" class="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-primary-500"></span>
          </button>
        </li>
      </ul>

      <div v-if="!loading && pagination.pages > 1" class="flex items-center justify-between pt-2 text-xs text-slate-500">
        <span>Page {{ pagination.page }} of {{ pagination.pages }} · {{ pagination.total }} total</span>
        <div class="flex gap-2">
          <button class="btn-secondary px-3 py-1.5 text-xs" :disabled="pagination.page <= 1" @click="loadNotifications(pagination.page - 1)">
            Previous
          </button>
          <button class="btn-secondary px-3 py-1.5 text-xs" :disabled="pagination.page >= pagination.pages" @click="loadNotifications(pagination.page + 1)">
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import notificationService from '@/services/notification.service'

const router = useRouter()
const authStore = useAuthStore()

const notifications = ref([])
const loading = ref(true)
const unreadOnly = ref(false)
const isMarkingAll = ref(false)
const pagination = ref({ page: 1, per_page: 15, total: 0, pages: 0 })

async function loadNotifications(page = 1) {
  loading.value = true
  try {
    const params = { page, per_page: pagination.value.per_page }
    if (unreadOnly.value) params.unread_only = 'true'
    const response = await notificationService.getNotifications(params)
    notifications.value = response?.data?.items || []
    pagination.value = response?.data?.pagination || pagination.value
  } finally {
    loading.value = false
  }
}

async function handleNotifClick(notification) {
  if (!notification.is_read) {
    try {
      await notificationService.markAsRead(notification.id)
      notification.is_read = true
    } catch {
      // Ignore — non-critical UI action.
    }
  }
  if (notification.related_complaint_id && authStore.userRole === 'citizen') {
    router.push({ name: 'complaint-details', params: { id: notification.related_complaint_id } })
  }
}

async function handleMarkAllRead() {
  isMarkingAll.value = true
  try {
    await notificationService.markAllAsRead()
    notifications.value = notifications.value.map((n) => ({ ...n, is_read: true }))
  } finally {
    isMarkingAll.value = false
  }
}

function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

onMounted(() => {
  loadNotifications(1)
})
</script>
