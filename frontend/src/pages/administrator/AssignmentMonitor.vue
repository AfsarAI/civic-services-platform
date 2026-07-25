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
      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-100 text-left text-sm">
          <thead>
            <tr class="text-xs font-semibold uppercase tracking-wider text-slate-400">
              <th class="px-3 py-3">Complaint</th>
              <th class="px-3 py-3">Priority</th>
              <th class="px-3 py-3">Worker</th>
              <th class="px-3 py-3">Assigned</th>
              <th class="px-3 py-3">Expected completion</th>
              <th class="px-3 py-3">Last progress</th>
              <th class="px-3 py-3">Repair status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-slate-700">
            <tr
              v-for="assignment in assignments"
              :key="assignment.id"
              :class="assignment.is_overdue ? 'bg-rose-50/70' : 'hover:bg-slate-50/60'"
            >
              <td class="px-3 py-3">
                <RouterLink
                  :to="{ name: 'admin-complaint-details', params: { id: assignment.complaint.id } }"
                  class="font-semibold text-primary-700 hover:text-primary-800"
                >
                  #{{ assignment.complaint.id }} · {{ assignment.complaint.title }}
                </RouterLink>
                <p class="mt-0.5 text-xs capitalize text-slate-400">
                  Complaint: {{ label(assignment.complaint.status) }}
                  <span v-if="assignment.complaint.city_name"> · {{ assignment.complaint.city_name }}</span>
                </p>
              </td>
              <td class="px-3 py-3 text-xs font-semibold capitalize">{{ assignment.complaint.priority }}</td>
              <td class="px-3 py-3">{{ assignment.worker_name || `Worker #${assignment.worker_id}` }}</td>
              <td class="whitespace-nowrap px-3 py-3 text-xs">{{ formatDate(assignment.assigned_at) }}</td>
              <td class="whitespace-nowrap px-3 py-3 text-xs">
                <span :class="assignment.is_overdue ? 'font-bold text-rose-700' : ''">
                  {{ formatDate(assignment.expected_completion_at) }}
                </span>
                <span v-if="assignment.is_overdue" class="ml-2 rounded-full bg-rose-100 px-2 py-0.5 font-bold text-rose-700">
                  Overdue
                </span>
              </td>
              <td class="whitespace-nowrap px-3 py-3 text-xs">{{ formatDate(assignment.updated_at) }}</td>
              <td class="px-3 py-3">
                <span class="rounded-full px-2.5 py-1 text-xs font-semibold capitalize" :class="statusClass(assignment.status)">
                  {{ label(assignment.status) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
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

onMounted(() => loadAssignments(1))
</script>
