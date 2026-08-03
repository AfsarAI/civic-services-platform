<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 mb-2">Administrator Dashboard</h1>
        <p class="text-gray-500">
          Signed in as
          <span class="font-medium capitalize">{{ authStore.adminLevel || 'administrator' }}</span>
          administrator.
        </p>
      </div>
      <div class="flex gap-2">
        <div class="flex gap-2 items-center">
          <label class="text-xs text-gray-600">From:</label>
          <input v-model="dateFrom" type="date" class="form-input text-xs px-2 py-1" />
        </div>
        <div class="flex gap-2 items-center">
          <label class="text-xs text-gray-600">To:</label>
          <input v-model="dateTo" type="date" class="form-input text-xs px-2 py-1" />
        </div>
        <button class="btn-primary px-3 py-1.5 text-xs" :disabled="loadingDashboard" @click="loadDashboard">
          {{ loadingDashboard ? 'Loading...' : 'Filter' }}
        </button>
        <button class="btn-secondary px-3 py-1.5 text-xs" @click="autoRefresh = !autoRefresh">
          {{ autoRefresh ? '⏸ Auto-Refresh On' : '▶ Auto-Refresh Off' }}
        </button>
      </div>
    </div>

    <!-- KPI Cards Grid -->
    <div v-if="!loadingDashboard" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <!-- Total Complaints -->
      <div class="card">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-500 uppercase tracking-wide font-semibold">Total Complaints</p>
          <svg class="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5z"/>
          </svg>
        </div>
        <p class="text-3xl font-bold text-blue-600">{{ dashboardData?.total_complaints || 0 }}</p>
        <p class="text-xs text-gray-400 mt-2">All-time submissions</p>
      </div>

      <!-- Open Complaints -->
      <div class="card">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-500 uppercase tracking-wide font-semibold">Open Complaints</p>
          <svg class="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 11-2 0 1 1 0 012 0z"/>
          </svg>
        </div>
        <p class="text-3xl font-bold text-yellow-600">{{ dashboardData?.open_complaints || 0 }}</p>
        <p class="text-xs text-gray-400 mt-2">Pending, assigned, in progress</p>
      </div>

      <!-- Closed Complaints -->
      <div class="card">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-500 uppercase tracking-wide font-semibold">Closed Complaints</p>
          <svg class="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/>
          </svg>
        </div>
        <p class="text-3xl font-bold text-green-600">{{ dashboardData?.closed_complaints || 0 }}</p>
        <p class="text-xs text-gray-400 mt-2">Resolved & closed</p>
      </div>

      <!-- Closure Rate -->
      <div class="card">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-500 uppercase tracking-wide font-semibold">Closure Rate</p>
          <svg class="w-4 h-4 text-purple-400" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
          </svg>
        </div>
        <p class="text-3xl font-bold text-purple-600">{{ dashboardData?.complaint_closure_rate_percentage?.toFixed(1) || 0 }}%</p>
        <p class="text-xs text-gray-400 mt-2">Success rate</p>
      </div>

      <!-- Citizen Satisfaction -->
      <div class="card">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-500 uppercase tracking-wide font-semibold">Satisfaction</p>
          <svg class="w-4 h-4 text-pink-400" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
          </svg>
        </div>
        <p class="text-3xl font-bold text-pink-600">{{ (dashboardData?.citizen_satisfaction_rating || 0).toFixed(1) }}/5</p>
        <p class="text-xs text-gray-400 mt-2">Average rating</p>
      </div>

      <!-- Avg Resolution Time -->
      <div class="card">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-500 uppercase tracking-wide font-semibold">Avg Resolution</p>
          <svg class="w-4 h-4 text-cyan-400" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"/>
          </svg>
        </div>
        <p class="text-3xl font-bold text-cyan-600">{{ (dashboardData?.avg_resolution_time_hours || 0).toFixed(1) }}h</p>
        <p class="text-xs text-gray-400 mt-2">From submission to resolution</p>
      </div>

      <!-- Avg Assignment Time -->
      <div class="card">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-500 uppercase tracking-wide font-semibold">Avg Assignment</p>
          <svg class="w-4 h-4 text-indigo-400" fill="currentColor" viewBox="0 0 20 20">
            <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v1h8v-1zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"/>
          </svg>
        </div>
        <p class="text-3xl font-bold text-indigo-600">{{ (dashboardData?.avg_assignment_time_hours || 0).toFixed(1) }}h</p>
        <p class="text-xs text-gray-400 mt-2">Worker acceptance time</p>
      </div>

      <!-- Field Worker Completion Rate -->
      <div class="card">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-500 uppercase tracking-wide font-semibold">Worker Completion</p>
          <svg class="w-4 h-4 text-orange-400" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 3.086v6.769a3 3 0 01-3 3H6a3 3 0 01-3-3v-6.769a3.066 3.066 0 012.812-3.086zM9 13a1 1 0 11-2 0 1 1 0 012 0z"/>
          </svg>
        </div>
        <p class="text-3xl font-bold text-orange-600">{{ (dashboardData?.field_worker_completion_rate_percentage || 0).toFixed(1) }}%</p>
        <p class="text-xs text-gray-400 mt-2">Assignment completion rate</p>
      </div>

      <!-- High Priority Pending -->
      <div class="card" :class="{ 'border-red-200 bg-red-50': (dashboardData?.high_priority_pending_count || 0) > 0 }">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-500 uppercase tracking-wide font-semibold">🚨 High Priority Pending</p>
          <svg class="w-4 h-4" :class="(dashboardData?.high_priority_pending_count || 0) > 0 ? 'text-red-400' : 'text-gray-400'" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"/>
          </svg>
        </div>
        <p class="text-3xl font-bold" :class="(dashboardData?.high_priority_pending_count || 0) > 0 ? 'text-red-600' : 'text-gray-600'">{{ dashboardData?.high_priority_pending_count || 0 }}</p>
        <p class="text-xs text-gray-400 mt-2">Urgent action needed</p>
      </div>
    </div>

    <!-- Loading State -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div v-for="n in 9" :key="n" class="card animate-pulse">
        <div class="h-8 bg-slate-100 rounded mb-2"></div>
        <div class="h-10 bg-slate-100 rounded"></div>

    <!-- Complaints by Status -->
    <div class="card mb-4">
      <h2 class="font-semibold text-gray-900 mb-4">Complaints by Status</h2>
      <p v-if="!statusBreakdown.length" class="text-gray-400 text-sm italic text-center py-8">No data yet.</p>
      <div v-else class="space-y-3">
        <div v-for="row in statusBreakdown" :key="row.status">
          <div class="flex items-center justify-between text-xs mb-1">
            <span class="font-medium capitalize text-gray-700">{{ row.status.replaceAll('_', ' ') }}</span>
            <span class="text-gray-500">{{ row.count }} ({{ row.percentage }}%)</span>
          </div>
          <div class="h-2 rounded-full bg-slate-100 overflow-hidden">
            <div class="h-full rounded-full bg-primary-500" :style="{ width: `${row.percentage}%` }"></div>
          </div>
        </div>
      </div>
    </div>
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

    <!-- Complaints Map -->
    <PublicComplaintMap
      class="mb-4"
      :markers="mapMarkers"
      :loading="loadingMap"
      :title="authStore.isSystemAdmin ? 'All India Complaint Map' : `Complaints Map \u2014 ${authStore.cityName || 'your city'}`"
      :subtitle="authStore.isSystemAdmin
        ? 'All complaints across every city on the platform, pinned by location. Click a pin to view full details.'
        : `All complaints reported in ${authStore.cityName || 'your city'}, pinned by location. Click a pin to view full details.`"
      empty-message="No complaints have a saved map location yet."
      show-view-details
      @pin-click="goToComplaint"
    />

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

      <!-- Card view (mobile / tablet / small laptop screens) -->
      <div v-else class="lg:hidden space-y-3">
        <div v-for="c in complaints" :key="c.id" class="rounded-xl border border-slate-100 p-4 space-y-2.5">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="font-semibold text-slate-900 text-sm truncate">{{ c.title }}</p>
              <p class="text-xs text-slate-400 mt-0.5">Ref: #{{ c.id }}{{ c.city_name ? ` \u00b7 ${c.city_name}` : '' }}</p>
            </div>
            <span :class="statusBadgeClass(c)" class="shrink-0">{{ statusLabel(c) }}</span>
          </div>
          <p v-if="isAwaitingVerification(c)" class="text-[11px] font-normal text-purple-600">
            Marked as fixed, pending verification.
          </p>
          <div class="flex flex-wrap items-center gap-2 text-xs">
            <span class="capitalize text-slate-500">{{ c.priority }}</span>
            <span class="text-slate-400">Reported: {{ formatDate(c.created_at) }}</span>
          </div>
          <div class="flex items-center gap-3">
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
          </div>
          <div v-if="assigningId === c.id" class="rounded-lg bg-slate-50 p-3 space-y-2">
            <select v-model="assignWorkerId" class="form-input w-full text-sm">
              <option value="">Select a field worker</option>
              <option v-for="w in activeFieldWorkers" :key="w.id" :value="w.id">
                {{ w.full_name }}{{ w.city_name ? ` (${w.city_name})` : '' }}
              </option>
            </select>
            <input
              v-model="expectedCompletionAt"
              type="datetime-local"
              class="form-input w-full text-sm"
              aria-label="Expected completion date"
            />
            <button class="btn-primary w-full py-2 text-xs" :disabled="!assignWorkerId || isAssigning" @click="handleAssign(c)">
              {{ isAssigning ? 'Assigning...' : 'Confirm assignment' }}
            </button>
            <p v-if="activeFieldWorkers.length === 0" class="text-xs text-slate-500">
              No active field workers available{{ authStore.isMunicipalAdmin ? ' in your city' : '' }}.
            </p>
          </div>
        </div>
      </div>

      <div v-if="!loadingComplaints && complaints.length > 0" class="hidden lg:block overflow-x-auto">
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
                    <input
                      v-model="expectedCompletionAt"
                      type="datetime-local"
                      class="form-input w-56 text-sm"
                      aria-label="Expected completion date"
                    />
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
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import complaintService from '@/services/complaint.service'
import adminService from '@/services/admin.service'
import PublicComplaintMap from '@/components/PublicComplaintMap.vue'

const authStore = useAuthStore()
const router = useRouter()

const complaints = ref([])
const mapComplaints = ref([])
const loadingComplaints = ref(true)
const loadingDashboard = ref(true)
const loadingMap = ref(true)
const error = ref('')
const statusFilter = ref('')
const categoryFilter = ref('')
const pagination = ref({ page: 1, per_page: 10, total: 0, pages: 0 })
const dashboardData = ref(null)
const autoRefresh = ref(true)
const dateFrom = ref('')
const dateTo = ref('')

const activeFieldWorkers = ref([])
const assigningId = ref(null)
const assignWorkerId = ref('')
const expectedCompletionAt = ref('')
const isAssigning = ref(false)

const mapMarkers = computed(() =>
  mapComplaints.value
    .filter((c) => c.latitude != null && c.longitude != null)
    .map((c) => ({
      id: c.id,
      latitude: c.latitude,
      longitude: c.longitude,
      title: c.title,
      category: c.category,
      status: c.status,
      city_name: c.city_name,
    }))
)

function goToComplaint(id) {
  router.push({ name: 'admin-complaint-details', params: { id } })
}

async function loadMapComplaints() {
  loadingMap.value = true
  try {
    const response = await complaintService.getAllComplaints({ per_page: 100 })
    mapComplaints.value = response?.data?.items || []
  } catch {
    // Non-critical: the map simply stays empty on failure, rest of the dashboard still works.
  } finally {
    loadingMap.value = false
  }
}


const stats = computed(() => {
  if (!dashboardData.value) return []

  if (authStore.isSystemAdmin) {
    return [
      { label: 'Total Complaints', value: dashboardData.value.total_complaints || 0, color: 'text-blue-600' },
      { label: 'Closure Rate', value: `${(dashboardData.value.complaint_closure_rate_percentage || 0).toFixed(1)}%`, color: 'text-green-600' },
      { label: 'Satisfaction', value: `${(dashboardData.value.citizen_satisfaction_rating || 0).toFixed(1)}/5`, color: 'text-pink-600' },
      { label: 'High Priority', value: dashboardData.value.high_priority_pending_count || 0, color: 'text-red-600' },
    ]
  }

  return [
    { label: 'City', value: authStore.cityName || '-', color: 'text-gray-800' },
    { label: 'Total Complaints', value: dashboardData.value.total_complaints || 0, color: 'text-blue-600' },
    { label: 'Closure Rate', value: `${(dashboardData.value.complaint_closure_rate_percentage || 0).toFixed(1)}%`, color: 'text-green-600' },
    { label: 'Satisfaction', value: `${(dashboardData.value.citizen_satisfaction_rating || 0).toFixed(1)}/5`, color: 'text-pink-600' },
  ]
})

const statusBreakdown = computed(() => {
  const byStatus = dashboardData.value?.by_status || {}
  const total = dashboardData.value?.total_complaints || 0
  const order = ['pending', 'assigned', 'in_progress', 'resolved', 'closed', 'rejected', 'cancelled']

  return order
    .filter((status) => status in byStatus)
    .map((status) => {
      const count = byStatus[status] || 0
      return {
        status,
        count,
        percentage: total ? Math.round((count / total) * 1000) / 10 : 0,
      }
    })
})

async function loadDashboard() {
  loadingDashboard.value = true
  error.value = ''
  try {
    const params = {}
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    
    const response = await adminService.getDashboard(params)
    dashboardData.value = response?.data || {}
  } catch (err) {
    error.value = err?.response?.data?.message || 'Could not load dashboard data.'
    console.error('Dashboard error:', err)
  } finally {
    loadingDashboard.value = false
  }
}

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
    expectedCompletionAt.value = ''
    return
  }
  assigningId.value = complaint.id
  assignWorkerId.value = ''
  expectedCompletionAt.value = ''
  loadActiveFieldWorkers()
}

async function handleAssign(complaint) {
  if (!assignWorkerId.value) return
  isAssigning.value = true
  error.value = ''
  try {
    await complaintService.assignComplaint(complaint.id, {
      worker_id: Number(assignWorkerId.value),
      expected_completion_at: expectedCompletionAt.value
        ? new Date(expectedCompletionAt.value).toISOString()
        : null,
    })
    assigningId.value = null
    assignWorkerId.value = ''
    expectedCompletionAt.value = ''
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

let refreshInterval = null

onMounted(() => {
  loadDashboard()
  loadComplaints(1)
  loadMapComplaints()

  // Setup auto-refresh every 30 seconds
  if (autoRefresh.value) {
    refreshInterval = setInterval(() => {
      if (autoRefresh.value) {
        loadDashboard()
        loadMapComplaints()
      }
    }, 30000)
  }
})

// Watch for auto-refresh toggle
watch(autoRefresh, (newValue) => {
  if (newValue && !refreshInterval) {
    refreshInterval = setInterval(() => {
      if (autoRefresh.value) {
        loadDashboard()
        loadMapComplaints()
      }
    }, 30000)
  } else if (!newValue && refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
})

onBeforeUnmount(() => {
  if (refreshInterval) clearInterval(refreshInterval)
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
