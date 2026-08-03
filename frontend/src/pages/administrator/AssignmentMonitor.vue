<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Monitor Complaint Progress</h1>
        <p class="mt-1 text-sm text-gray-500">
          Track assigned repairs, deadlines, and the latest field-worker progress.
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <select v-model="statusFilter" class="form-input w-44 text-sm" @change="loadAssignments(1)">
          <option value="">All repair statuses</option>
          <option value="assigned">Assigned</option>
          <option value="accepted">Accepted</option>
          <option value="in_progress">In progress</option>
          <option value="completed">Completed</option>
          <option value="rejected">Rejected</option>
        </select>
        <label class="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-600">
          <input v-model="overdueOnly" type="checkbox" @change="loadAssignments(1)" />
          Overdue only
        </label>
      </div>
    </div>

    <div v-if="error" class="card mb-4 border-red-200 bg-red-50 text-sm text-red-700">{{ error }}</div>

    <div class="card">
      <div v-if="loading" class="space-y-3 py-6">
        <div v-for="n in 4" :key="n" class="h-12 animate-pulse rounded-lg bg-slate-100"></div>
      </div>
      <p v-else-if="assignments.length === 0" class="py-10 text-center text-sm italic text-slate-400">
        No assignments match the current filters.
      </p>
      <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="assignment in assignments"
          :key="assignment.id"
          class="overflow-hidden rounded-2xl border bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
          :class="assignment.is_overdue ? 'border-rose-200 bg-rose-50/40' : 'border-slate-200'"
        >
          <div class="h-1.5" :class="statusAccentClass(assignment.status)"></div>
          <div class="space-y-4 p-4">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Complaint #{{ assignment.complaint.id }}</p>
                <RouterLink
                  :to="{ name: 'admin-complaint-details', params: { id: assignment.complaint.id } }"
                  class="mt-1 block text-base font-semibold text-primary-700 line-clamp-2 hover:text-primary-800"
                >
                  {{ assignment.complaint.title }}
                </RouterLink>
              </div>
              <span class="shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold capitalize" :class="statusClass(assignment.status)">
                {{ label(assignment.status) }}
              </span>
            </div>

            <span v-if="assignment.is_overdue" class="inline-flex rounded-full bg-rose-100 px-2.5 py-1 text-xs font-bold text-rose-700">
              Overdue
            </span>

            <div class="grid grid-cols-2 gap-3 text-xs text-slate-600">
              <div>
                <p class="font-semibold text-slate-500">Priority</p>
                <p class="mt-1 capitalize text-slate-900">{{ assignment.complaint.priority }}</p>
              </div>
              <div>
                <p class="font-semibold text-slate-500">Worker</p>
                <p class="mt-1 text-slate-900">{{ assignment.worker_name || `Worker #${assignment.worker_id}` }}</p>
              </div>
              <div>
                <p class="font-semibold text-slate-500">Assigned</p>
                <p class="mt-1 text-slate-900">{{ formatDate(assignment.assigned_at) }}</p>
              </div>
              <div>
                <p class="font-semibold text-slate-500">Expected completion</p>
                <p class="mt-1" :class="assignment.is_overdue ? 'font-bold text-rose-700' : 'text-slate-900'">
                  {{ formatDate(assignment.expected_completion_at) }}
                </p>
              </div>
            </div>

            <p class="text-xs text-slate-500">
              Complaint status: <span class="capitalize">{{ label(assignment.complaint.status) }}</span>
              <template v-if="assignment.complaint.city_name"> · {{ assignment.complaint.city_name }}</template>
            </p>
            <p class="text-xs text-slate-400">Last progress: {{ formatDate(assignment.updated_at) }}</p>
          </div>
        </article>
      </div>

      <div v-if="!loading && pagination.pages > 1" class="flex items-center justify-between pt-4 text-xs text-slate-500">
        <span>Page {{ pagination.page }} of {{ pagination.pages }} · {{ pagination.total }} total</span>
        <div class="flex gap-2">
          <button class="btn-secondary px-3 py-1.5 text-xs" :disabled="pagination.page <= 1" @click="loadAssignments(pagination.page - 1)">Previous</button>
          <button class="btn-secondary px-3 py-1.5 text-xs" :disabled="pagination.page >= pagination.pages" @click="loadAssignments(pagination.page + 1)">Next</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import complaintService from '@/services/complaint.service'

const assignments = ref([])
const loading = ref(true)
const error = ref('')
const statusFilter = ref('')
const overdueOnly = ref(false)
const pagination = ref({ page: 1, per_page: 20, total: 0, pages: 0 })

async function loadAssignments(page = 1) {
  loading.value = true
  error.value = ''
  try {
    const params = { page, per_page: pagination.value.per_page }
    if (statusFilter.value) params.status = statusFilter.value
    if (overdueOnly.value) params.overdue = true
    const response = await complaintService.getAssignmentMonitor(params)
    assignments.value = response?.data?.items || []
    pagination.value = response?.data?.pagination || pagination.value
  } catch (err) {
    error.value = err?.response?.data?.message || 'Could not load assignment progress.'
  } finally {
    loading.value = false
  }
}

function formatDate(value) {
  if (!value) return 'Not set'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Not set'
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function label(value) {
  return value?.replaceAll('_', ' ') || 'Unknown'
}

function statusClass(status) {
  if (status === 'completed') return 'bg-emerald-100 text-emerald-700'
  if (status === 'rejected') return 'bg-rose-100 text-rose-700'
  if (['accepted', 'in_progress'].includes(status)) return 'bg-sky-100 text-sky-700'
  return 'bg-amber-100 text-amber-700'
}

function statusAccentClass(status) {
  if (status === 'completed') return 'bg-emerald-500'
  if (status === 'rejected') return 'bg-rose-500'
  if (['accepted', 'in_progress'].includes(status)) return 'bg-sky-500'
  return 'bg-amber-500'
}

onMounted(() => loadAssignments(1))
</script>
