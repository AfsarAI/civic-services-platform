<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-slate-900 tracking-tight">Work History</h1>
      <p class="text-slate-500 text-sm mt-0.5">
        Review your assigned, completed, and pending repair tasks.
      </p>
    </div>

    <!-- Error Alert -->
    <transition name="fade">
      <div v-if="error" class="card border-red-200 bg-red-50 text-red-700 flex items-start gap-3 p-4">
        <svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <div class="flex-1">
          <h4 class="font-semibold text-sm">Failed to load work history</h4>
          <p class="text-xs mt-1">{{ error }}</p>
        </div>
      </div>
    </transition>

    <div class="card space-y-4">
      <div class="flex flex-col gap-3">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by title, street, or complaint ID..."
          class="form-input w-full sm:w-72 text-sm"
          @input="onSearchInput"
        />
        <div class="flex flex-wrap items-center gap-2">
          <select v-model="statusFilter" class="form-input w-full sm:w-40 text-sm" @change="onFilterChange">
            <option value="">All Statuses</option>
            <option value="assigned">Assigned</option>
            <option value="accepted">Accepted</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="rejected">Rejected</option>
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
      <div v-if="loading" class="space-y-3 py-6">
        <div v-for="n in 4" :key="n" class="animate-pulse flex gap-4">
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
        <p class="text-slate-500 text-sm font-medium">No work history found</p>
        <p class="text-slate-400 text-xs mt-1">
          {{ (statusFilter || searchQuery) ? 'Try different search or filter criteria.' : 'Your assigned and completed repair tasks will appear here.' }}
        </p>
      </div>

      <!-- Card view (all screen sizes) -->
      <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="a in assignments"
          :key="a.id"
          class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
        >
          <div class="h-1.5" :class="statusAccentClass(a.status)"></div>
          <div class="space-y-4 p-4">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Ref: #{{ a.complaint_id }}</p>
                <h2 class="mt-1 text-base font-semibold text-slate-900 line-clamp-2">
                  {{ a.complaint?.title || `Complaint #${a.complaint_id}` }}
                </h2>
              </div>
              <span class="shrink-0" :class="statusBadgeClass(a.status)">{{ a.status?.replaceAll('_', ' ') }}</span>
            </div>

            <div class="grid grid-cols-2 gap-3 text-xs text-slate-600">
              <div>
                <p class="font-semibold text-slate-500">Priority</p>
                <p class="mt-1"><span :class="priorityClass(a.complaint?.priority)">{{ a.complaint?.priority || '-' }}</span></p>
              </div>
              <div>
                <p class="font-semibold text-slate-500">Location</p>
                <p class="mt-1 text-slate-900">{{ a.complaint?.city_name || '—' }}</p>
              </div>
              <div>
                <p class="font-semibold text-slate-500">Assigned</p>
                <p class="mt-1 text-slate-900">{{ formatDate(a.assigned_at) }}</p>
              </div>
              <div>
                <p class="font-semibold text-slate-500">Completed</p>
                <p class="mt-1 text-slate-900">{{ a.completed_at ? formatDate(a.completed_at) : '—' }}</p>
              </div>
            </div>

            <p class="text-xs text-slate-500">{{ a.complaint?.address || 'No street name provided' }}</p>

            <div v-if="a.notes" class="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
              <p class="font-semibold text-slate-500">Repair Remarks</p>
              <p class="mt-1 line-clamp-3">{{ a.notes }}</p>
            </div>

            <div class="pt-1">
              <RouterLink
                :to="{ name: 'fieldworker-assignment-details', params: { id: a.id } }"
                class="btn-primary w-full py-2 text-center text-sm"
              >
                View Details →
              </RouterLink>
            </div>
          </div>
        </article>
      </div>

      <!-- Pagination -->
      <div v-if="!loading && pagination.pages > 1" class="flex items-center justify-between pt-2 text-xs text-slate-500">
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
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import fieldWorkerService from '@/services/fieldworker.service'

const loading = ref(true)
const error = ref(null)

const assignments = ref([])
const statusFilter = ref('')
const searchQuery = ref('')
const sortBy = ref('assigned_at')
const sortOrder = ref('desc')
const pagination = ref({ page: 1, per_page: 15, total: 0, pages: 0 })
let searchDebounceTimer = null

async function fetchHistory(page = 1) {
  loading.value = true
  error.value = null
  try {
    const params = {
      page,
      per_page: pagination.value.per_page,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    }
    if (statusFilter.value) params.status = statusFilter.value
    if (searchQuery.value.trim()) params.search = searchQuery.value.trim()

    const res = await fieldWorkerService.getAssignments(params)
    if (res?.success && res?.data) {
      assignments.value = res.data.items || []
      pagination.value = res.data.pagination || pagination.value
    } else {
      throw new Error(res?.message || 'Invalid API response format.')
    }
  } catch (err) {
    error.value = err.message || 'Error occurred while loading work history.'
  } finally {
    loading.value = false
  }
}

function onFilterChange() {
  fetchHistory(1)
}

function onSearchInput() {
  clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    fetchHistory(1)
  }, 350)
}

function toggleSortOrder() {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  fetchHistory(1)
}

function goToPage(page) {
  fetchHistory(page)
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

function statusAccentClass(status) {
  switch (status?.toLowerCase()) {
    case 'completed':
      return 'bg-emerald-500'
    case 'rejected':
      return 'bg-rose-500'
    case 'in_progress':
    case 'accepted':
      return 'bg-sky-500'
    default:
      return 'bg-amber-500'
  }
}

onMounted(() => {
  fetchHistory(1)
})
</script>
