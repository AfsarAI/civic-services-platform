<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 tracking-tight">
          Welcome back, {{ authStore.fullName || 'Field Worker' }}!
        </h1>
        <p class="text-slate-500 text-sm mt-0.5">
          View your assigned repair tasks and update progress as you work.
        </p>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="refreshAll"
          class="btn-secondary py-2.5 px-4 flex items-center gap-2 text-sm"
          :disabled="loadingStats || loadingList"
          title="Refresh dashboard data"
        >
          <svg
            class="w-4 h-4"
            :class="{ 'animate-spin': loadingStats || loadingList }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89"/>
          </svg>
          Refresh
        </button>
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

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="stat in statsData"
        :key="stat.label"
        class="card relative overflow-hidden transition-all duration-300 hover:shadow-md"
      >
        <div v-if="loadingStats" class="animate-pulse space-y-2">
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

    <!-- Your Assigned Complaints Map -->
    <PublicComplaintMap
      :markers="mapMarkers"
      :loading="loadingMap"
      title="Your Assigned Complaints Map"
      subtitle="All complaints assigned to you, pinned by location. Click a pin to view full details."
      empty-message="None of your assigned complaints have a saved map location yet."
      show-view-details
      @pin-click="goToAssignment"
    />

    <!-- Assigned Tasks -->
    <div class="card space-y-4">
      <div class="flex flex-col gap-3">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <h3 class="text-base font-bold text-slate-900 tracking-tight">
            Assigned Complaints
          </h3>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search by title, street, or complaint ID..."
            class="form-input w-full sm:w-64 text-sm"
            @input="onSearchInput"
          />
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <select v-model="statusFilter" class="form-input w-full sm:w-40 text-sm" @change="onFilterChange">
            <option value="">All Statuses</option>
            <option value="assigned">Assigned</option>
            <option value="accepted">Accepted</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="rejected">Rejected</option>
          </select>
          <select v-model="priorityFilter" class="form-input w-full sm:w-36 text-sm" @change="onFilterChange">
            <option value="">All Priorities</option>
            <option value="urgent">Urgent</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select v-model="sortBy" class="form-input w-full sm:w-44 text-sm" @change="onFilterChange">
            <option value="assigned_at">Sort: Assignment Date</option>
            <option value="priority">Sort: Priority</option>
          </select>
          <button
            type="button"
            class="btn-secondary px-3 py-2 text-xs"
            :title="sortOrder === 'desc' ? 'Descending' : 'Ascending'"
            @click="toggleSortOrder"
          >
            {{ sortOrder === 'desc' ? '↓ Desc' : '↑ Asc' }}
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loadingList" class="space-y-3 py-6">
        <div v-for="n in 3" :key="n" class="animate-pulse flex gap-4">
          <div class="h-10 bg-slate-100 rounded-lg flex-1"></div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="assignments.length === 0" class="text-center py-10">
        <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-50 text-slate-400 mb-3">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
        </div>
        <p class="text-slate-500 text-sm font-medium">No assignments found</p>
        <p class="text-slate-400 text-xs mt-1">
          {{ (statusFilter || priorityFilter || searchQuery) ? 'Try different search or filter criteria.' : 'New tasks assigned to you will appear here.' }}
        </p>
      </div>

      <!-- Card view (mobile / tablet / small laptop screens) -->
      <div v-else class="lg:hidden space-y-3">
        <div
          v-for="a in assignments"
          :key="a.id"
          class="rounded-xl border border-slate-100 p-4 space-y-2.5"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="font-semibold text-slate-900 text-sm truncate">{{ a.complaint?.title || `Complaint #${a.complaint_id}` }}</p>
              <p class="text-xs text-slate-400 mt-0.5">Ref: #{{ a.complaint_id }}</p>
            </div>
            <span :class="statusBadgeClass(a.status)" class="shrink-0">{{ a.status?.replaceAll('_', ' ') }}</span>
          </div>
          <p v-if="isComplaintTerminal(a)" class="text-[11px] font-semibold text-amber-600">
            Complaint {{ a.complaint?.status?.replaceAll('_', ' ') }} by admin — no action needed
          </p>
          <div class="text-xs text-slate-600">
            <span class="block font-medium text-slate-800">{{ a.complaint?.city_name || '—' }}</span>
            <span class="block text-slate-400 mt-0.5">{{ a.complaint?.address || 'No street name provided' }}</span>
          </div>
          <div class="flex flex-wrap items-center gap-2 text-xs">
            <span :class="priorityClass(a.complaint?.priority)">{{ a.complaint?.priority || '-' }}</span>
            <span class="text-slate-400">Reported: {{ formatDate(a.complaint?.created_at) }}</span>
            <span class="text-slate-400">Assigned: {{ formatDate(a.assigned_at) }}</span>
          </div>
          <div v-if="a.expected_completion_at" class="text-xs text-slate-400">
            Expected completion: {{ formatDate(a.expected_completion_at) }}
          </div>
          <RouterLink
            :to="{ name: 'fieldworker-assignment-details', params: { id: a.id } }"
            class="inline-block text-xs font-bold text-primary-600 hover:text-primary-700 transition-colors"
          >
            View Details →
          </RouterLink>
        </div>
      </div>

      <!-- Table (lg and up) -->
      <div v-if="!loadingList && assignments.length > 0" class="hidden lg:block overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-100 text-left text-sm">
          <thead>
            <tr class="text-slate-400 text-xs font-semibold uppercase tracking-wider">
              <th class="py-3 px-4">Complaint</th>
              <th class="py-3 px-4">Location</th>
              <th class="py-3 px-4">Priority</th>
              <th class="py-3 px-4">Status</th>
              <th class="py-3 px-4">Reported / Assigned</th>
              <th class="py-3 px-4">Expected Completion</th>
              <th class="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 font-medium text-slate-700">
            <tr v-for="a in assignments" :key="a.id" class="hover:bg-slate-50/50 transition-colors">
              <td class="py-3 px-4 max-w-xs truncate">
                <span class="block font-semibold text-slate-900">{{ a.complaint?.title || `Complaint #${a.complaint_id}` }}</span>
                <span class="block text-xs text-slate-400 mt-0.5">Ref: #{{ a.complaint_id }}</span>
                <span v-if="isComplaintTerminal(a)" class="mt-1 block text-[11px] font-semibold text-amber-600">
                  Complaint {{ a.complaint?.status?.replaceAll('_', ' ') }} by admin — no action needed
                </span>
              </td>
              <td class="py-3 px-4 text-xs text-slate-600">
                <span class="block font-medium text-slate-800">{{ a.complaint?.city_name || '—' }}</span>
                <span class="block text-slate-400 mt-0.5">{{ a.complaint?.address || 'No street name provided' }}</span>
              </td>
              <td class="py-3 px-4 text-xs">
                <span :class="priorityClass(a.complaint?.priority)">{{ a.complaint?.priority || '-' }}</span>
              </td>
              <td class="py-3 px-4 text-xs">
                <span :class="statusBadgeClass(a.status)">{{ a.status?.replaceAll('_', ' ') }}</span>
              </td>
              <td class="py-3 px-4 text-xs text-slate-500">
                <span class="block">Reported: {{ formatDate(a.complaint?.created_at) }}</span>
                <span class="block mt-0.5 text-slate-400">Assigned: {{ formatDate(a.assigned_at) }}</span>
              </td>
              <td class="py-3 px-4 text-xs text-slate-500">
                {{ a.expected_completion_at ? formatDate(a.expected_completion_at) : '—' }}
              </td>
              <td class="py-3 px-4 text-right">
                <RouterLink
                  :to="{ name: 'fieldworker-assignment-details', params: { id: a.id } }"
                  class="text-xs font-bold text-primary-600 hover:text-primary-700 transition-colors"
                >
                  View Details →
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="!loadingList && pagination.pages > 1" class="flex items-center justify-between pt-2 text-xs text-slate-500">
        <span>Page {{ pagination.page }} of {{ pagination.pages }} · {{ pagination.total }} total</span>
        <div class="flex gap-2">
          <button
            class="btn-secondary px-3 py-1.5 text-xs"
            :disabled="pagination.page <= 1"
            @click="goToPage(pagination.page - 1)"
          >
            Previous
          </button>
          <button
            class="btn-secondary px-3 py-1.5 text-xs"
            :disabled="pagination.page >= pagination.pages"
            @click="goToPage(pagination.page + 1)"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import fieldWorkerService from '@/services/fieldworker.service'
import PublicComplaintMap from '@/components/PublicComplaintMap.vue'

const authStore = useAuthStore()
const router = useRouter()

const loadingStats = ref(true)
const loadingList = ref(true)
const loadingMap = ref(true)
const error = ref(null)

const stats = ref({
  total_assignments: 0,
  active_assignments: 0,
  by_status: {
    assigned: 0,
    accepted: 0,
    in_progress: 0,
    completed: 0,
    rejected: 0,
  },
})

const assignments = ref([])
const mapAssignments = ref([])
const statusFilter = ref('')
const priorityFilter = ref('')
const searchQuery = ref('')
const sortBy = ref('assigned_at')
const sortOrder = ref('desc')
const pagination = ref({ page: 1, per_page: 10, total: 0, pages: 0 })
let searchDebounceTimer = null

const mapMarkers = computed(() =>
  mapAssignments.value
    .filter((a) => a.complaint?.latitude != null && a.complaint?.longitude != null)
    .map((a) => ({
      id: a.id,
      latitude: a.complaint.latitude,
      longitude: a.complaint.longitude,
      title: a.complaint.title,
      category: a.complaint.category,
      status: mapAssignmentStatusForPin(a.status),
      city_name: a.complaint.city_name,
    }))
)

// Reuses the map's existing open/resolved/rejected colour scheme, mapped from
// this assignment's own progress status rather than the complaint's status.
function mapAssignmentStatusForPin(status) {
  if (status === 'completed') return 'resolved'
  if (status === 'rejected') return 'rejected'
  return 'pending'
}

function goToAssignment(id) {
  router.push({ name: 'fieldworker-assignment-details', params: { id } })
}

const statsData = computed(() => [
  {
    label: 'Total Assigned',
    value: stats.value.total_assignments,
    colorClass: 'text-primary-600',
    icon: '📋',
  },
  {
    label: 'Active Tasks',
    value: stats.value.active_assignments,
    colorClass: 'text-amber-600',
    icon: '🛠️',
  },
  {
    label: 'Completed',
    value: stats.value.by_status?.completed || 0,
    colorClass: 'text-green-600',
    icon: '✅',
  },
  {
    label: 'Rejected',
    value: stats.value.by_status?.rejected || 0,
    colorClass: 'text-slate-600',
    icon: '↩️',
  },
])

async function fetchStats() {
  loadingStats.value = true
  try {
    const res = await fieldWorkerService.getDashboardSummary()
    if (res?.success && res?.data) {
      stats.value = {
        total_assignments: res.data.total_assignments || 0,
        active_assignments: res.data.active_assignments || 0,
        by_status: {
          assigned: 0,
          accepted: 0,
          in_progress: 0,
          completed: 0,
          rejected: 0,
          ...(res.data.by_status || {}),
        },
      }
    } else {
      throw new Error(res?.message || 'Invalid API response format.')
    }
  } catch (err) {
    error.value = err.message || 'Error occurred while loading dashboard statistics.'
  } finally {
    loadingStats.value = false
  }
}

async function fetchAssignments(page = 1) {
  loadingList.value = true
  error.value = null
  try {
    const params = {
      page,
      per_page: pagination.value.per_page,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    }
    if (statusFilter.value) params.status = statusFilter.value
    if (priorityFilter.value) params.priority = priorityFilter.value
    if (searchQuery.value.trim()) params.search = searchQuery.value.trim()

    const res = await fieldWorkerService.getAssignments(params)
    if (res?.success && res?.data) {
      assignments.value = res.data.items || []
      pagination.value = res.data.pagination || pagination.value
    } else {
      throw new Error(res?.message || 'Invalid API response format.')
    }
  } catch (err) {
    error.value = err.message || 'Error occurred while loading assignments.'
  } finally {
    loadingList.value = false
  }
}

function onFilterChange() {
  fetchAssignments(1)
}

async function fetchMapAssignments() {
  loadingMap.value = true
  try {
    const res = await fieldWorkerService.getAssignments({ per_page: 100 })
    if (res?.success && res?.data) {
      mapAssignments.value = res.data.items || []
    }
  } catch {
    // Non-critical: the map simply stays empty on failure, rest of the dashboard still works.
  } finally {
    loadingMap.value = false
  }
}

function onSearchInput() {
  clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    fetchAssignments(1)
  }, 350)
}

function toggleSortOrder() {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  fetchAssignments(1)
}

function goToPage(page) {
  fetchAssignments(page)
}

function refreshAll() {
  fetchStats()
  fetchAssignments(pagination.value.page || 1)
  fetchMapAssignments()
}

function formatDate(isoStr) {
  if (!isoStr) return '—'
  try {
    const d = new Date(isoStr)
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
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
    case 'assigned':
      return 'badge-assigned'
    case 'accepted':
      return 'badge-progress'
    case 'in_progress':
      return 'badge-progress'
    case 'completed':
      return 'badge-resolved'
    case 'rejected':
      return 'badge-rejected'
    default:
      return 'inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700'
  }
}

// The complaint can be rejected/closed by an administrator independently of
// this assignment's own status (still `assigned`/`accepted`/`in_progress`).
function isComplaintTerminal(assignment) {
  const complaintStatus = assignment.complaint?.status
  const assignmentActive = ['assigned', 'accepted', 'in_progress'].includes(assignment.status)
  return assignmentActive && ['rejected', 'cancelled', 'resolved', 'closed'].includes(complaintStatus)
}

onMounted(() => {
  fetchStats()
  fetchAssignments(1)
  fetchMapAssignments()
})
</script>


