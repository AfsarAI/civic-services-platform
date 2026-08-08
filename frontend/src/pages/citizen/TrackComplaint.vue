<template>
  <div class="mx-auto max-w-6xl space-y-5">
    <section class="rounded-3xl border border-slate-200 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 px-5 py-6 text-white shadow-xl sm:px-6">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-[11px] font-semibold uppercase tracking-[0.22em] text-sky-200">Complaint tracker</p>
          <h1 class="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Track your pothole reports</h1>
          <p class="mt-3 max-w-2xl text-sm leading-6 text-slate-200 sm:text-base">
            Review every complaint you submitted, filter by status, and open the full detail page for timeline, photo, and location.
          </p>
        </div>

        <button type="button" class="btn-secondary w-fit px-4 py-2 text-sm" :disabled="loading" @click="loadComplaints()">
          {{ loading ? 'Refreshing...' : 'Refresh' }}
        </button>
      </div>

      <div class="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <article class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur-sm">
          <p class="text-[11px] uppercase tracking-wide text-slate-300">Total</p>
          <p class="mt-2 text-2xl font-semibold">{{ stats.total }}</p>
        </article>
        <article class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur-sm">
          <p class="text-[11px] uppercase tracking-wide text-slate-300">Open</p>
          <p class="mt-2 text-2xl font-semibold text-amber-300">{{ stats.open }}</p>
        </article>
        <article class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur-sm">
          <p class="text-[11px] uppercase tracking-wide text-slate-300">Resolved</p>
          <p class="mt-2 text-2xl font-semibold text-emerald-300">{{ stats.resolved }}</p>
        </article>
        <article class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur-sm">
          <p class="text-[11px] uppercase tracking-wide text-slate-300">Filtered</p>
          <p class="mt-2 text-2xl font-semibold text-sky-300">{{ filteredComplaints.length }}</p>
        </article>
      </div>
    </section>

    <section class="card space-y-4">
      <div class="grid gap-3 lg:grid-cols-[1fr_220px_160px]">
        <div>
          <label class="form-label" for="search">Search</label>
          <input
            id="search"
            v-model.trim="search"
            type="text"
            class="form-input"
            placeholder="Search by title, description, or complaint ID"
          />
        </div>

        <div>
          <label class="form-label" for="status">Status</label>
          <select id="status" v-model="statusFilter" class="form-input">
            <option value="">All statuses</option>
            <option v-for="status in statusOptions" :key="status.value" :value="status.value">
              {{ status.label }}
            </option>
          </select>
        </div>

        <div class="flex items-end gap-2">
          <button type="button" class="btn-secondary w-full px-4 py-3 text-sm" @click="clearFilters">
            Clear
          </button>
        </div>
      </div>

      <div v-if="error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {{ error }}
      </div>

      <transition name="fade">
        <div v-if="successMessage" class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {{ successMessage }}
        </div>
      </transition>

      <div v-if="loading" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <div v-for="skeleton in 6" :key="skeleton" class="animate-pulse rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div class="h-4 w-1/3 rounded bg-slate-200"></div>
          <div class="mt-3 h-5 w-3/4 rounded bg-slate-200"></div>
          <div class="mt-2 h-4 w-full rounded bg-slate-200"></div>
          <div class="mt-5 h-9 w-28 rounded bg-slate-200"></div>
        </div>
      </div>

      <div v-else-if="filteredComplaints.length === 0" class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center">
        <p class="text-base font-semibold text-slate-900">No complaints found</p>
        <p class="mt-2 text-sm text-slate-500">
          {{ complaints.length ? 'Try a different status or search term.' : 'You have not submitted any pothole complaints yet.' }}
        </p>
        <RouterLink to="/citizen/report" class="btn-primary mt-5 inline-flex">Report a pothole</RouterLink>
      </div>

      <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="complaint in paginatedComplaints"
          :key="complaint.id"
          class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
        >
          <div class="h-1.5" :class="statusAccentClass(complaint.status)"></div>
          <div class="space-y-4 p-4">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Complaint #{{ complaint.id }}</p>
                <h2 class="mt-1 text-lg font-semibold text-slate-900 line-clamp-2">{{ complaint.title }}</h2>
              </div>
              <span class="shrink-0 rounded-full px-3 py-1 text-[11px] font-semibold" :class="statusBadgeClass(complaint.status)">
                {{ statusLabel(complaint.status, complaint) }}
              </span>
            </div>

            <p class="line-clamp-3 text-sm text-slate-600">{{ complaint.description }}</p>

            <p v-if="complaint.status === 'in_progress' && complaint.assignment_status === 'completed'" class="rounded-lg bg-sky-50 px-3 py-2 text-xs text-sky-800">
              Repair marked complete by the field worker — awaiting administrator verification.
            </p>

            <p v-if="complaint.duplicate_of_id" class="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
              Linked to complaint #{{ complaint.duplicate_of_id }}, which is already being addressed.
            </p>

            <div class="grid grid-cols-2 gap-3 text-xs text-slate-600">
              <div>
                <p class="font-semibold text-slate-500">Priority</p>
                <p class="mt-1 capitalize text-slate-900">{{ complaint.priority || 'medium' }}</p>
              </div>
              <div>
                <p class="font-semibold text-slate-500">Category</p>
                <p class="mt-1 capitalize text-slate-900">{{ complaint.category || 'pothole' }}</p>
              </div>
              <div>
                <p class="font-semibold text-slate-500">Location</p>
                <p class="mt-1 text-slate-900">{{ complaint.city_name || '—' }}</p>
              </div>
              <div>
                <p class="font-semibold text-slate-500">Raised</p>
                <p class="mt-1 text-slate-900">{{ formatDate(complaint.created_at) }}</p>
              </div>
            </div>

            <div class="flex flex-wrap gap-2">
              <span v-if="complaint.pincode" class="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">{{ complaint.pincode }}</span>
              <span v-if="complaint.feedback" class="rounded-full bg-emerald-50 px-2.5 py-1 text-xs text-emerald-700">Feedback added</span>
            </div>

            <div class="flex items-center justify-between gap-3 pt-1">
              <RouterLink :to="{ name: 'complaint-details', params: { id: complaint.id } }" class="btn-primary px-4 py-2 text-sm">
                View details
              </RouterLink>

              <div class="flex gap-2">
                <RouterLink
                  v-if="canQuickFeedback(complaint)"
                  :to="{ name: 'complaint-details', params: { id: complaint.id } }"
                  class="btn-secondary px-4 py-2 text-sm"
                >
                  Add feedback
                </RouterLink>
                <button
                  v-if="complaint.status === 'pending'"
                  type="button"
                  class="btn-danger px-4 py-2 text-sm"
                  :disabled="cancellingId === complaint.id"
                  @click="handleCancel(complaint)"
                >
                  {{ cancellingId === complaint.id ? 'Cancelling...' : 'Cancel' }}
                </button>
              </div>
            </div>
          </div>
        </article>
      </div>

      <div v-if="filteredComplaints.length > pageSize" class="flex items-center justify-between gap-3 border-t border-slate-200 pt-4 text-sm text-slate-600">
        <p>
          Showing {{ pageStart + 1 }}-{{ pageEnd }} of {{ filteredComplaints.length }}
        </p>
        <div class="flex gap-2">
          <button type="button" class="btn-secondary px-4 py-2" :disabled="currentPage === 1" @click="currentPage--">Prev</button>
          <button type="button" class="btn-secondary px-4 py-2" :disabled="pageEnd >= filteredComplaints.length" @click="currentPage++">Next</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import complaintService from '@/services/complaint.service'

const complaints = ref([])
const loading = ref(false)
const error = ref('')
const successMessage = ref('')
const cancellingId = ref(null)
const search = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = 6

const statusOptions = [
  { value: 'pending', label: 'Pending' },
  { value: 'assigned', label: 'Assigned' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'cancelled', label: 'Cancelled' },
]

const stats = computed(() => {
  const totals = {
    total: complaints.value.length,
    open: 0,
    resolved: 0,
  }

  for (const complaint of complaints.value) {
    if (['pending', 'assigned', 'in_progress'].includes(complaint.status)) totals.open += 1
    if (['resolved', 'closed'].includes(complaint.status)) totals.resolved += 1
  }

  return totals
})

const filteredComplaints = computed(() => {
  const query = search.value.trim().toLowerCase()

  return complaints.value.filter((complaint) => {
    const matchesStatus = !statusFilter.value || complaint.status === statusFilter.value
    const haystack = [complaint.id, complaint.title, complaint.description, complaint.city_name, complaint.pincode]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    const matchesQuery = !query || haystack.includes(query)
    return matchesStatus && matchesQuery
  })
})

const pageCount = computed(() => Math.max(1, Math.ceil(filteredComplaints.value.length / pageSize)))
const pageStart = computed(() => (currentPage.value - 1) * pageSize)
const pageEnd = computed(() => Math.min(pageStart.value + pageSize, filteredComplaints.value.length))
const paginatedComplaints = computed(() => filteredComplaints.value.slice(pageStart.value, pageEnd.value))

function statusLabel(status, complaint) {
  if (status === 'in_progress' && complaint?.assignment_status === 'completed') return 'Awaiting verification'
  if (status === 'rejected' && complaint?.duplicate_of_id) return 'Duplicate report'
  return (status || 'pending').replaceAll('_', ' ')
}

function statusBadgeClass(status) {
  if (['resolved', 'closed'].includes(status)) return 'bg-emerald-50 text-emerald-700'
  if (status === 'rejected') return 'bg-rose-50 text-rose-700'
  if (status === 'cancelled') return 'bg-slate-100 text-slate-500'
  if (['assigned', 'in_progress'].includes(status)) return 'bg-sky-50 text-sky-700'
  return 'bg-amber-50 text-amber-700'
}

function statusAccentClass(status) {
  if (['resolved', 'closed'].includes(status)) return 'bg-emerald-500'
  if (status === 'rejected') return 'bg-rose-500'
  if (status === 'cancelled') return 'bg-slate-400'
  if (['assigned', 'in_progress'].includes(status)) return 'bg-sky-500'
  return 'bg-amber-500'
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(date)
}

function clearFilters() {
  search.value = ''
  statusFilter.value = ''
  currentPage.value = 1
}

function canQuickFeedback(complaint) {
  return ['resolved', 'closed'].includes(complaint.status) && !complaint.feedback
}

async function loadComplaints() {
  loading.value = true
  error.value = ''

  try {
    const response = await complaintService.getMyComplaints({ page: 1, per_page: 100, status: statusFilter.value || undefined })
    complaints.value = response?.data?.items || []
    currentPage.value = 1
  } catch (err) {
    error.value = err?.response?.data?.message || 'Could not load your complaints right now.'
  } finally {
    loading.value = false
  }
}

async function handleCancel(complaint) {
  const confirmed = window.confirm(
    'Cancel complaint #' + complaint.id + ' - "' + complaint.title + '"? This cannot be undone.',
  )
  if (!confirmed) return

  error.value = ''
  successMessage.value = ''
  cancellingId.value = complaint.id
  try {
    const response = await complaintService.deleteComplaint(complaint.id)
    const updatedStatus = response?.data?.complaint?.status || 'cancelled'
    const target = complaints.value.find((c) => c.id === complaint.id)
    if (target) {
      target.status = updatedStatus
    }
    successMessage.value = response?.message || 'Complaint cancelled successfully.'
  } catch (err) {
    error.value = err?.response?.data?.message || 'Could not cancel this complaint.'
  } finally {
    cancellingId.value = null
  }
}

watch([search, statusFilter], () => {
  currentPage.value = 1
})

watch(pageCount, () => {
  if (currentPage.value > pageCount.value) {
    currentPage.value = pageCount.value
  }
})

onMounted(() => {
  loadComplaints()
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
