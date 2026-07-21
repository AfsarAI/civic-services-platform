<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-2">Administrator Dashboard</h1>
    <p class="text-gray-500 mb-6">
      Signed in as
      <span class="font-medium capitalize">{{ authStore.adminLevel || 'administrator' }}</span>
      administrator.
    </p>

    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
      <div v-for="stat in stats" :key="stat.label" class="card text-center">
        <p class="text-3xl font-bold" :class="stat.color">{{ stat.value }}</p>
        <p class="text-sm text-gray-500 mt-1">{{ stat.label }}</p>
      </div>
    </div>

    <div v-if="authStore.isSystemAdmin" class="card mb-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-gray-900">System Administrator Scope</h2>
        <RouterLink
          to="/admin/municipal-administrators"
          class="btn-secondary px-4 py-2 text-sm"
        >
          Manage Municipal Admins
        </RouterLink>
      </div>
      <p class="text-gray-600 text-sm">
        You can create, manage, and disable municipal administrators and access platform-wide reports.
      </p>
    </div>

    <div v-else-if="authStore.isMunicipalAdmin" class="card mb-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-gray-900">Municipal Administrator Scope</h2>
        <RouterLink to="/admin/field-workers" class="btn-secondary px-4 py-2 text-sm">
          Manage Field Workers
        </RouterLink>
      </div>
      <p class="text-gray-600 text-sm">
        Your account is assigned to
        <span class="font-medium">{{ authStore.cityName || 'a city' }}</span>.
        You only see complaints reported in this city and can only assign them to field workers who belong to it.
        Global reports and cross-city administration remain restricted to the system administrator.
      </p>
    </div>

    <!-- Error Alert -->
    <transition name="fade">
      <div v-if="error" class="card border-red-200 bg-red-50 text-red-700 flex items-start gap-3 p-4 mb-4">
        <p class="text-sm">{{ error }}</p>
      </div>
    </transition>

    <div class="card mb-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-gray-900">
          {{ authStore.isMunicipalAdmin ? `Complaints in ${authStore.cityName || 'your city'}` : 'Recent Complaints' }}
        </h2>
        <div class="flex gap-2">
          <select v-model="statusFilter" class="form-input w-36 text-sm" @change="loadComplaints(1)">
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="assigned">Assigned</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
            <option value="rejected">Rejected</option>          <option value="cancelled">Cancelled</option>          </select>
          <select v-model="categoryFilter" class="form-input w-36 text-sm" @change="loadComplaints(1)">
            <option value="">All Categories</option>
            <option value="pothole">Pothole</option>
          </select>
        </div>
      </div>

      <div v-if="loadingComplaints" class="space-y-3 py-6">
        <div v-for="n in 3" :key="n" class="animate-pulse flex gap-4">
          <div class="h-10 bg-slate-100 rounded-lg flex-1"></div>
        </div>
      </div>

      <p v-else-if="complaints.length === 0" class="text-gray-400 italic text-sm text-center py-8">
        No complaints match the current filters.
      </p>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-100 text-left text-sm">
          <thead>
            <tr class="text-slate-400 text-xs font-semibold uppercase tracking-wider">
              <th class="py-3 px-4">Title</th>
              <th class="py-3 px-4">Priority</th>
              <th class="py-3 px-4">Status</th>
              <th class="py-3 px-4">Reported</th>
              <th class="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 font-medium text-slate-700">
            <template v-for="c in complaints" :key="c.id">
              <tr class="hover:bg-slate-50/50 transition-colors">
                <td class="py-3 px-4 max-w-xs truncate">
                  <span class="block font-semibold text-slate-900">{{ c.title }}</span>
                  <span class="block text-xs text-slate-400 mt-0.5">Ref: #{{ c.id }}{{ c.city_name ? ` · ${c.city_name}` : '' }}</span>
                </td>
                <td class="py-3 px-4 text-xs capitalize">{{ c.priority }}</td>
                <td class="py-3 px-4 text-xs">
                  <span :class="statusBadgeClass(c)">{{ statusLabel(c) }}</span>
                  <span v-if="isAwaitingVerification(c)" class="mt-1 block text-[11px] font-normal normal-case text-purple-600">
                    Marked as fixed, pending verification.
                  </span>
                </td>
                <td class="py-3 px-4 text-xs text-slate-500">{{ formatDate(c.created_at) }}</td>
                <td class="py-3 px-4 text-right space-x-3 whitespace-nowrap">
                  <RouterLink
                    :to="{ name: 'admin-complaint-details', params: { id: c.id } }"
                    class="text-xs font-bold text-slate-600 hover:text-slate-800"
                  >
                    View
                  </RouterLink>
                  <button
                    v-if="['pending', 'assigned'].includes(c.status)"
                    class="text-xs font-bold text-primary-600 hover:text-primary-700"
                    @click="toggleAssignRow(c)"
                  >
                    {{ assigningId === c.id ? 'Cancel' : 'Assign' }}
                  </button>
                </td>
              </tr>
              <tr v-if="assigningId === c.id">
                <td colspan="5" class="bg-slate-50 px-4 py-3">
                  <div class="flex flex-wrap items-center gap-3">
                    <select v-model="assignWorkerId" class="form-input w-64 text-sm">
                      <option value="">Select a field worker</option>
                      <option v-for="w in activeFieldWorkers" :key="w.id" :value="w.id">
                        {{ w.full_name }}{{ w.city_name ? ` (${w.city_name})` : '' }}
                      </option>
                    </select>
                    <button class="btn-primary px-4 py-2 text-xs" :disabled="!assignWorkerId || isAssigning" @click="handleAssign(c)">
                      {{ isAssigning ? 'Assigning...' : 'Confirm assignment' }}
                    </button>
                    <span v-if="activeFieldWorkers.length === 0" class="text-xs text-slate-500">
                      No active field workers available{{ authStore.isMunicipalAdmin ? ' in your city' : '' }}.
                    </span>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <div v-if="!loadingComplaints && pagination.pages > 1" class="flex items-center justify-between pt-4 text-xs text-slate-500">
        <span>Page {{ pagination.page }} of {{ pagination.pages }} · {{ pagination.total }} total</span>
        <div class="flex gap-2">
          <button class="btn-secondary px-3 py-1.5 text-xs" :disabled="pagination.page <= 1" @click="loadComplaints(pagination.page - 1)">
            Previous
          </button>
          <button class="btn-secondary px-3 py-1.5 text-xs" :disabled="pagination.page >= pagination.pages" @click="loadComplaints(pagination.page + 1)">
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import complaintService from '@/services/complaint.service'
import adminService from '@/services/admin.service'

const authStore = useAuthStore()

const complaints = ref([])
const loadingComplaints = ref(true)
const error = ref('')
const statusFilter = ref('')
const categoryFilter = ref('')
const pagination = ref({ page: 1, per_page: 10, total: 0, pages: 0 })

const activeFieldWorkers = ref([])
const assigningId = ref(null)
const assignWorkerId = ref('')
const isAssigning = ref(false)

const stats = computed(() => {
  if (authStore.isSystemAdmin) {
    return [
      { label: 'Cities', value: 0, color: 'text-gray-800' },
      { label: 'Municipal Admins', value: 0, color: 'text-blue-600' },
      { label: 'Open Complaints', value: pagination.value.total, color: 'text-yellow-600' },
      { label: 'Resolved', value: 0, color: 'text-green-600' },
    ]
  }

  return [
    { label: 'Assigned City', value: authStore.cityName || '-', color: 'text-gray-800' },
    { label: 'Access Scope', value: 'City', color: 'text-blue-600' },
    { label: 'Total Complaints', value: pagination.value.total, color: 'text-yellow-600' },
    { label: 'Account Status', value: 'Active', color: 'text-green-600' },
  ]
})

async function loadComplaints(page = 1) {
  loadingComplaints.value = true
  error.value = ''
  try {
    const params = { page, per_page: pagination.value.per_page }
    if (statusFilter.value) params.status = statusFilter.value
    if (categoryFilter.value) params.category = categoryFilter.value

    const response = await complaintService.getAllComplaints(params)
    complaints.value = response?.data?.items || []
    pagination.value = response?.data?.pagination || pagination.value
  } catch (err) {
    error.value = err?.response?.data?.message || 'Could not load complaints.'
  } finally {
    loadingComplaints.value = false
  }
}

async function loadActiveFieldWorkers() {
  try {
    const response = await adminService.getFieldWorkers({ is_active: 'true' })
    activeFieldWorkers.value = response?.data?.field_workers || []
  } catch {
    activeFieldWorkers.value = []
  }
}

function toggleAssignRow(complaint) {
  if (assigningId.value === complaint.id) {
    assigningId.value = null
    assignWorkerId.value = ''
    return
  }
  assigningId.value = complaint.id
  assignWorkerId.value = ''
  loadActiveFieldWorkers()
}

async function handleAssign(complaint) {
  if (!assignWorkerId.value) return
  isAssigning.value = true
  error.value = ''
  try {
    await complaintService.assignComplaint(complaint.id, { worker_id: Number(assignWorkerId.value) })
    assigningId.value = null
    assignWorkerId.value = ''
    await loadComplaints(pagination.value.page || 1)
  } catch (err) {
    error.value = err?.response?.data?.message || 'Could not assign this complaint.'
  } finally {
    isAssigning.value = false
  }
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function statusBadgeClass(complaint) {
  if (isAwaitingVerification(complaint)) return 'badge-verify'
  switch (complaint.status?.toLowerCase()) {
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

// A complaint's own `status` stays `in_progress` until an administrator verifies
// and resolves it, even after the field worker's assignment reaches `completed`.
function isAwaitingVerification(complaint) {
  return complaint.status === 'in_progress' && complaint.assignment_status === 'completed'
}

function statusLabel(complaint) {
  if (isAwaitingVerification(complaint)) return 'Pending Verification'
  return complaint.status?.replaceAll('_', ' ')
}

onMounted(() => {
  loadComplaints(1)
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

