<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 tracking-tight">
          Welcome back, {{ authStore.fullName || 'Citizen' }}!
        </h1>
        <p class="text-slate-500 text-sm mt-0.5">
          Track issues you have reported and raise new complaints.
        </p>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="fetchDashboardData"
          class="btn-secondary py-2.5 px-4 flex items-center gap-2 text-sm"
          :disabled="loading"
          title="Refresh dashboard data"
        >
          <svg
            class="w-4 h-4"
            :class="{ 'animate-spin': loading }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89"/>
          </svg>
          Refresh
        </button>
        <RouterLink to="/citizen/report" class="btn-primary py-2.5 px-4 flex items-center gap-2 text-sm">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          Report Issue
        </RouterLink>
      </div>
    </div>

    <!-- Error Alert -->
    <transition name="fade">
      <div v-if="error" class="card border-red-200 bg-red-50 text-red-700 flex items-start gap-3 p-4">
        <svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <div class="flex-1">
          <h4 class="font-semibold text-sm">Failed to load dashboard</h4>
          <p class="text-xs mt-1">{{ error }}</p>
        </div>
      </div>
    </transition>

    <!-- Stats Cards (Loading skeletons or values) -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="stat in statsData"
        :key="stat.label"
        class="card relative overflow-hidden transition-all duration-300 hover:shadow-md"
      >
        <div v-if="loading" class="animate-pulse space-y-2">
          <div class="h-8 bg-slate-200 rounded w-1/3"></div>
          <div class="h-4 bg-slate-200 rounded w-2/3"></div>
        </div>
        <div v-else class="flex flex-col justify-between h-full">
          <div>
            <p class="text-3xl font-extrabold" :class="stat.colorClass">
              {{ stat.value }}
            </p>
            <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1.5">
              {{ stat.label }}
            </p>
          </div>
          <div class="absolute right-3 top-3 opacity-10">
            <span class="text-3xl" v-html="stat.icon"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Navigation / Welcome Box -->
    <div class="grid md:grid-cols-3 gap-4">
      <div class="card md:col-span-2 bg-gradient-to-br from-primary-900 to-slate-900 text-white p-6 relative overflow-hidden">
        <div class="relative z-10 max-w-lg">
          <span class="inline-flex rounded-full bg-primary-500/20 px-3 py-1 text-xs font-semibold text-primary-300 tracking-wide mb-3">
            Civic Sense Platform
          </span>
          <h3 class="text-lg font-bold">Have you noticed a pothole around you?</h3>
          <p class="text-slate-300 text-xs mt-2 leading-relaxed">
            Report potholes with a photo and map pin. The app is focused on one thing: getting road defects logged fast and routed to the right city team.
          </p>
          <RouterLink to="/citizen/report" class="inline-flex items-center gap-1 text-xs font-semibold text-primary-400 hover:text-primary-300 mt-4 transition-colors">
            Start a new report
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </RouterLink>
        </div>
        <div class="absolute -right-10 -bottom-10 opacity-10 text-9xl">
          🏛️
        </div>
      </div>

      <div class="card flex flex-col justify-between bg-white border-slate-200">
        <div>
          <h3 class="text-sm font-bold text-slate-900">Need to track?</h3>
          <p class="text-slate-500 text-xs mt-1.5 leading-normal">
            Search, filter, or look up details on any issue using its unique complaint reference identifier.
          </p>
        </div>
        <RouterLink to="/citizen/track" class="btn-secondary w-full py-2 text-center text-xs mt-4">
          Track by ID
        </RouterLink>
      </div>
    </div>

    <!-- Recent Complaints Table -->
    <div class="card space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-base font-bold text-slate-900 tracking-tight">
          Recent Complaint Submissions
        </h3>
        <RouterLink
          v-if="recentComplaints.length > 0"
          to="/citizen/track"
          class="text-xs font-semibold text-primary-600 hover:underline"
        >
          View all complaints
        </RouterLink>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="space-y-3 py-6">
        <div v-for="n in 3" :key="n" class="animate-pulse flex gap-4">
          <div class="h-10 bg-slate-100 rounded-lg flex-1"></div>
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="recentComplaints.length === 0"
        class="text-center py-10"
      >
        <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-50 text-slate-400 mb-3">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
        </div>
        <p class="text-slate-500 text-sm font-medium">No complaints reported yet</p>
        <p class="text-slate-400 text-xs mt-1">Raise your first complaint to start tracking status updates.</p>
        <RouterLink to="/citizen/report" class="btn-primary mt-4 py-2 px-4 text-xs">
          Report your first issue
        </RouterLink>
      </div>

      <!-- Table / List representation -->
      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-100 text-left text-sm">
          <thead>
            <tr class="text-slate-400 text-xs font-semibold uppercase tracking-wider">
              <th class="py-3 px-4">Title</th>
              <th class="py-3 px-4">Category</th>
              <th class="py-3 px-4">Priority</th>
              <th class="py-3 px-4">Status</th>
              <th class="py-3 px-4">Submitted</th>
              <th class="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 font-medium text-slate-700">
            <tr v-for="c in recentComplaints" :key="c.id" class="hover:bg-slate-50/50 transition-colors">
              <td class="py-3 px-4 max-w-xs truncate">
                <span class="block font-semibold text-slate-900">{{ c.title }}</span>
                <span class="block text-xs text-slate-400 mt-0.5">Ref: #{{ c.id }}</span>
              </td>
              <td class="py-3 px-4 capitalize text-xs text-slate-500">
                {{ c.category?.replace('_', ' ') }}
              </td>
              <td class="py-3 px-4 text-xs">
                <span :class="priorityClass(c.priority)">{{ c.priority }}</span>
              </td>
              <td class="py-3 px-4 text-xs">
                <span :class="statusBadgeClass(c.status)">
                  {{ c.status }}
                </span>
              </td>
              <td class="py-3 px-4 text-xs text-slate-500">
                {{ formatDate(c.created_at) }}
              </td>
              <td class="py-3 px-4 text-right">
                <RouterLink
                  :to="{ name: 'complaint-details', params: { id: c.id } }"
                  class="text-xs font-bold text-primary-600 hover:text-primary-700 transition-colors"
                >
                  View Details →
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import complaintService from '@/services/complaint.service'

const authStore = useAuthStore()

const loading = ref(true)
const error = ref(null)
const stats = ref({
  total_complaints: 0,
  by_status: {
    pending: 0,
    assigned: 0,
    in_progress: 0,
    resolved: 0,
    closed: 0,
    rejected: 0,
    cancelled: 0
  }
})
const recentComplaints = ref([])

const statsData = computed(() => [
  {
    label: 'Total Reports',
    value: stats.value.total_complaints,
    colorClass: 'text-primary-600',
    icon: '📊'
  },
  {
    label: 'Pending / In Progress',
    value:
      (stats.value.by_status?.pending || 0) +
      (stats.value.by_status?.assigned || 0) +
      (stats.value.by_status?.in_progress || 0),
    colorClass: 'text-amber-600',
    icon: '⏳'
  },
  {
    label: 'Resolved',
    value: stats.value.by_status?.resolved || 0,
    colorClass: 'text-green-600',
    icon: '✅'
  },
  {
    label: 'Closed / Cancelled',
    value:
      (stats.value.by_status?.closed || 0) +
      (stats.value.by_status?.rejected || 0) +
      (stats.value.by_status?.cancelled || 0),
    colorClass: 'text-slate-600',
    icon: '📁'
  }
])

async function fetchDashboardData() {
  loading.value = true
  error.value = null
  try {
    const res = await complaintService.getDashboardSummary()
    if (res?.success && res?.data) {
      stats.value.total_complaints = res.data.total_complaints || 0
      stats.value.by_status = {
        pending: 0,
        assigned: 0,
        in_progress: 0,
        resolved: 0,
        closed: 0,
        rejected: 0,
        cancelled: 0,
        ...(res.data.by_status || {})
      }
      recentComplaints.value = res.data.recent_complaints || []
    } else {
      throw new Error(res?.message || 'Invalid API response format.')
    }
  } catch (err) {
    error.value = err.message || 'Error occurred while loading citizen dashboard details.'
  } finally {
    loading.value = false
  }
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  } catch {
    return isoStr
  }
}

function priorityClass(p) {
  switch (p?.toLowerCase()) {
    case 'urgent':
    case 'high':
      return 'text-red-600 bg-red-50 px-2 py-0.5 rounded font-semibold'
    case 'medium':
      return 'text-amber-600 bg-amber-50 px-2 py-0.5 rounded font-semibold'
    default:
      return 'text-slate-500 bg-slate-50 px-2 py-0.5 rounded'
  }
}

function statusBadgeClass(status) {
  switch (status?.toLowerCase()) {
    case 'pending':
      return 'badge-pending'
    case 'assigned':
      return 'badge-assigned'
    case 'in_progress':
      return 'badge-progress'
    case 'resolved':
      return 'badge-resolved'
    case 'closed':
      return 'badge-closed'
    case 'rejected':
      return 'badge-rejected'
    case 'cancelled':
      return 'badge-cancelled'
    default:
      return 'inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700'
  }
}

onMounted(() => {
  fetchDashboardData()
})
</script>
