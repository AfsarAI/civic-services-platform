<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 mb-1">Administrative Reports</h1>
        <p class="text-gray-500 text-sm">{{ scopeDescription }}</p>
      </div>
      <div class="flex gap-2 shrink-0">
        <button type="button" class="btn-primary px-4 py-2 text-sm" :disabled="loading || exporting || !hasReportData" @click="exportReport('csv')">
          {{ exporting === 'csv' ? 'Exporting…' : 'Export CSV' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="card border-red-200 bg-red-50 text-red-700 p-4 text-sm">{{ error }}</div>

    <!-- Filters -->
    <div class="card">
      <h2 class="font-semibold text-gray-900 mb-3 text-sm">Filters</h2>
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-4">
        <div>
          <label class="form-label text-xs" for="date_from">From</label>
          <input id="date_from" v-model="filters.date_from" type="date" class="form-input text-sm" />
        </div>
        <div>
          <label class="form-label text-xs" for="date_to">To</label>
          <input id="date_to" v-model="filters.date_to" type="date" class="form-input text-sm" />
        </div>
        <div>
          <label class="form-label text-xs" for="status">Status</label>
          <select id="status" v-model="filters.status" class="form-input text-sm">
            <option value="">All Statuses</option>
            <option v-for="s in statusOptions" :key="s" :value="s">{{ s.replaceAll('_', ' ') }}</option>
          </select>
        </div>
        <div>
          <label class="form-label text-xs" for="priority">Priority</label>
          <select id="priority" v-model="filters.priority" class="form-input text-sm">
            <option value="">All Priorities</option>
            <option v-for="p in priorityOptions" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>
        <div v-if="authStore.isSystemAdmin">
          <label class="form-label text-xs" for="location">Location</label>
          <select id="location" v-model="filters.location" class="form-input text-sm">
            <option value="">All Locations</option>
            <option v-for="loc in locationOptions" :key="loc.city_id" :value="loc.city_id">{{ loc.city_name }}</option>
          </select>
        </div>
        <div class="flex items-end gap-2">
          <button type="button" class="btn-primary flex-1 py-2 text-sm" :disabled="loading" @click="applyFilters">
            Apply Filters
          </button>
          <button type="button" class="btn-secondary flex-1 py-2 text-sm" :disabled="loading" @click="resetFilters">
            Reset
          </button>
        </div>
      </div>
    </div>

    <div v-if="validationError" class="card border-amber-200 bg-amber-50 text-amber-800 p-4 text-sm">
      {{ validationError }}
    </div>

    <div v-if="loading" class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-7" aria-label="Loading administrative report">
      <div v-for="n in 7" :key="n" class="card animate-pulse">
        <div class="mx-auto h-8 w-16 rounded bg-slate-100"></div>
        <div class="mx-auto mt-2 h-3 w-24 rounded bg-slate-100"></div>
      </div>
    </div>

    <!-- Summary cards -->
    <div v-else class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-7">
      <div v-for="stat in summaryCards" :key="stat.label" class="card text-center">
        <p class="text-2xl font-bold" :class="stat.color">{{ stat.value }}</p>
        <p class="text-xs text-gray-500 mt-1">{{ stat.label }}</p>
      </div>
    </div>

    <div v-if="!loading && !hasReportData" class="card py-10 text-center text-sm text-gray-500">
      No complaints match the currently applied filters.
    </div>

    <div v-if="!loading && hasReportData" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- By status -->
      <div class="card">
        <h2 class="font-semibold text-gray-900 mb-4">Complaints by Status</h2>
        <p v-if="!byStatus.length" class="text-gray-400 text-sm italic text-center py-8">No data yet.</p>
        <div v-else class="space-y-3">
          <div v-for="row in byStatus" :key="row.status">
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

      <!-- By category -->
      <div class="card">
        <h2 class="font-semibold text-gray-900 mb-4">Complaints by Category</h2>
        <p v-if="!byCategory.length" class="text-gray-400 text-sm italic text-center py-8">No data yet.</p>
        <div v-else class="space-y-3">
          <div v-for="row in byCategory" :key="row.category">
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="font-medium capitalize text-gray-700">{{ row.category.replaceAll('_', ' ') }}</span>
              <span class="text-gray-500">{{ row.count }} ({{ row.percentage }}%)</span>
            </div>
            <div class="h-2 rounded-full bg-slate-100 overflow-hidden">
              <div class="h-full rounded-full bg-emerald-500" :style="{ width: `${row.percentage}%` }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- By priority -->
      <div class="card">
        <h2 class="font-semibold text-gray-900 mb-4">Complaints by Priority</h2>
        <p v-if="!byPriority.length" class="text-gray-400 text-sm italic text-center py-8">No data yet.</p>
        <div v-else class="space-y-3">
          <div v-for="row in byPriority" :key="row.priority">
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="font-medium capitalize text-gray-700">{{ row.priority }}</span>
              <span class="text-gray-500">{{ row.count }} ({{ row.percentage }}%)</span>
            </div>
            <div class="h-2 rounded-full bg-slate-100 overflow-hidden">
              <div class="h-full rounded-full bg-amber-500" :style="{ width: `${row.percentage}%` }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- By location -->
      <div class="card">
        <h2 class="font-semibold text-gray-900 mb-4">Complaints by Location</h2>
        <p v-if="!byLocation.length" class="text-gray-400 text-sm italic text-center py-8">No data yet.</p>
        <div v-else class="space-y-3">
          <div v-for="row in byLocation" :key="row.city_id ?? 'unassigned'">
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="font-medium text-gray-700">{{ row.city_name }}</span>
              <span class="text-gray-500">{{ row.count }} ({{ row.percentage }}%)</span>
            </div>
            <div class="h-2 rounded-full bg-slate-100 overflow-hidden">
              <div class="h-full rounded-full bg-sky-500" :style="{ width: `${row.percentage}%` }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Trends -->
      <div class="card md:col-span-2">
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-semibold text-gray-900">Complaint Trends</h2>
          <select v-model="trendPeriod" class="form-input w-36 text-sm" @change="loadTrends">
            <option value="daily">Daily (30d)</option>
            <option value="weekly">Weekly (12w)</option>
            <option value="monthly">Monthly (12m)</option>
          </select>
        </div>
        <p v-if="!trends.length" class="text-gray-400 text-sm italic text-center py-8">No submissions recorded yet.</p>
        <div v-else class="flex items-end gap-1.5 h-40 overflow-x-auto pb-2">
          <div
            v-for="point in trends"
            :key="point.period"
            class="flex flex-col items-center justify-end gap-1 shrink-0"
            style="width: 28px"
          >
            <div
              class="w-full rounded-t bg-primary-500"
              :style="{ height: `${trendBarHeight(point.count)}px` }"
              :title="`${point.period}: ${point.count}`"
            ></div>
            <span class="text-[9px] text-gray-400 rotate-45 origin-top-left whitespace-nowrap">{{ point.period }}</span>
          </div>
        </div>
      </div>

      <!-- Worker performance -->
      <div class="card md:col-span-2">
        <h2 class="font-semibold text-gray-900 mb-4">Field Worker Performance</h2>
        <p v-if="!workerPerformance.length" class="text-gray-400 text-sm italic text-center py-8">No field workers yet.</p>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead>
              <tr class="text-gray-400 text-xs font-semibold uppercase tracking-wider">
                <th class="py-2 pr-4">Worker</th>
                <th class="py-2 pr-4">Total</th>
                <th class="py-2 pr-4">Completed</th>
                <th class="py-2 pr-4">Completion Rate</th>
                <th class="py-2 pr-4">Avg. Time (hrs)</th>
                <th class="py-2 pr-4">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="w in workerPerformance" :key="w.worker_id">
                <td class="py-2 pr-4 font-medium text-gray-900">{{ w.name }}</td>
                <td class="py-2 pr-4">{{ w.total_assignments }}</td>
                <td class="py-2 pr-4">{{ w.by_status?.completed || 0 }}</td>
                <td class="py-2 pr-4">{{ w.completion_rate }}%</td>
                <td class="py-2 pr-4">{{ w.avg_completion_hours ?? '—' }}</td>
                <td class="py-2 pr-4">
                  <span class="rounded-full px-2 py-0.5 text-[11px] font-semibold" :class="w.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-600'">
                    {{ w.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Citizen Feedback Summary (TPS-96) -->
      <div class="card md:col-span-2">
        <h2 class="font-semibold text-gray-900 mb-4">Citizen Feedback Summary</h2>
        <p v-if="!feedbackSummary.total" class="text-gray-400 text-sm italic text-center py-8">No feedback received yet.</p>
        <template v-else>
          <div class="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            <div class="text-center">
              <p class="text-2xl font-bold text-gray-800">{{ feedbackSummary.total }}</p>
              <p class="text-xs text-gray-500 mt-1">Total Responses</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-amber-500">{{ feedbackSummary.avg_rating ?? '—' }}</p>
              <p class="text-xs text-gray-500 mt-1">Average Rating</p>
            </div>
            <div class="text-center">
              <div class="flex items-center justify-center gap-0.5">
                <span
                  v-for="star in 5"
                  :key="star"
                  class="text-lg"
                  :class="star <= Math.round(feedbackSummary.avg_rating || 0) ? 'text-amber-400' : 'text-gray-300'"
                >★</span>
              </div>
              <p class="text-xs text-gray-500 mt-1">Rating</p>
            </div>
          </div>

          <!-- Rating Distribution -->
          <h3 class="text-sm font-semibold text-gray-700 mb-3">Rating Distribution</h3>
          <div class="space-y-2 mb-6">
            <div v-for="star in [5, 4, 3, 2, 1]" :key="star" class="flex items-center gap-3">
              <span class="text-xs font-medium text-gray-600 w-12">{{ star }} Star</span>
              <div class="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  class="h-full rounded-full bg-amber-400"
                  :style="{ width: `${ratingPercentage(star)}%` }"
                ></div>
              </div>
              <span class="text-xs text-gray-500 w-8 text-right">{{ feedbackSummary.distribution?.[star] || 0 }}</span>
            </div>
          </div>

          <!-- Recent Comments -->
          <div v-if="feedbackSummary.recent_comments?.length">
            <h3 class="text-sm font-semibold text-gray-700 mb-3">Recent Feedback</h3>
            <div class="space-y-3 max-h-64 overflow-y-auto">
              <div
                v-for="(fb, idx) in feedbackSummary.recent_comments"
                :key="idx"
                class="bg-slate-50 rounded-lg p-3"
              >
                <div class="flex items-center justify-between mb-1">
                  <div class="flex items-center gap-0.5">
                    <span
                      v-for="s in 5"
                      :key="s"
                      class="text-xs"
                      :class="s <= fb.rating ? 'text-amber-400' : 'text-gray-300'"
                    >★</span>
                  </div>
                  <span class="text-[10px] text-gray-400">{{ fb.created_at }}</span>
                </div>
                <p class="text-sm text-gray-700">{{ fb.comment }}</p>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import reportsService from '@/services/reports.service'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const error = ref('')
const loading = ref(false)
const summary = ref({})
const byStatus = ref([])
const byCategory = ref([])
const byPriority = ref([])
const byLocation = ref([])
const locationOptions = ref([])
const trends = ref([])
const trendPeriod = ref('daily')
const workerPerformance = ref([])
const feedbackSummary = ref({})
const exporting = ref(false)
const validationError = ref('')

const filters = reactive({
  date_from: '',
  date_to: '',
  status: '',
  priority: '',
  location: '',
})
const statusOptions = ['pending', 'assigned', 'in_progress', 'resolved', 'closed', 'rejected', 'cancelled']
const priorityOptions = ['low', 'medium', 'high', 'urgent']

const scopeDescription = computed(() => {
  if (authStore.isSystemAdmin) return 'Platform-wide analytics across all cities.'
  if (authStore.isMunicipalAdmin) return `Analytics scoped to ${authStore.cityName || 'your city'}.`
  return 'Complaint and repair-activity analytics.'
})

const activeFilters = computed(() => {
  const applied = {}

  if (filters.date_from) applied.date_from = filters.date_from
  if (filters.date_to) applied.date_to = filters.date_to
  if (filters.status) applied.status = filters.status
  if (filters.priority) applied.priority = filters.priority
  if (filters.location) applied.location = filters.location

  return applied
})

const summaryCards = computed(() => [
  { label: 'Total Complaints', value: summary.value.total ?? 0, color: 'text-gray-800' },
  { label: 'Open', value: summary.value.open ?? 0, color: 'text-amber-600' },
  { label: 'Assigned', value: summary.value.assigned ?? 0, color: 'text-sky-600' },
  { label: 'In Progress', value: summary.value.in_progress ?? 0, color: 'text-blue-600' },
  { label: 'Completed (Awaiting Verification)', value: summary.value.completed ?? 0, color: 'text-purple-600' },
  { label: 'Closed', value: summary.value.closed ?? 0, color: 'text-green-600' },
  { label: 'Avg. Resolution (hrs)', value: summary.value.avg_resolution_hours ?? '—', color: 'text-slate-600' },
])

function trendBarHeight(count) {
  const max = Math.max(...trends.value.map((p) => p.count), 1)
  return Math.max(4, Math.round((count / max) * 120))
}

function ratingPercentage(star) {
  const total = feedbackSummary.value.total || 0
  if (!total) return 0
  const count = feedbackSummary.value.distribution?.[star] || 0
  return Math.round((count / total) * 100)
}

async function loadSummary() {
  try {
    const response = await reportsService.getSummary(activeFilters.value)
    summary.value = response?.data || {}
  } catch (err) {
    error.value = err?.response?.data?.message || 'Could not load report summary.'
  }
}

async function loadByStatus() {
  try {
    const response = await reportsService.getByStatus(activeFilters.value)
    byStatus.value = response?.data?.breakdown || []
  } catch {
    byStatus.value = []
  }
}

async function loadByCategory() {
  try {
    const response = await reportsService.getByCategory(activeFilters.value)
    byCategory.value = response?.data?.breakdown || []
  } catch {
    byCategory.value = []
  }
}

async function loadByPriority() {
  try {
    const response = await reportsService.getByPriority(activeFilters.value)
    byPriority.value = response?.data?.breakdown || []
  } catch {
    byPriority.value = []
  }
}

async function loadByLocation() {
  try {
    const response = await reportsService.getByLocation(activeFilters.value)
    byLocation.value = response?.data?.breakdown || []
    // Populate the location dropdown for system admins (only from unfiltered call)
    if (authStore.isSystemAdmin && !filters.location) {
      locationOptions.value = (response?.data?.breakdown || []).filter(r => r.city_id)
    }
  } catch {
    byLocation.value = []
  }
}

async function loadTrends() {
  try {
    const response = await reportsService.getTrends(trendPeriod.value, activeFilters.value)
    trends.value = response?.data?.data || []
  } catch {
    trends.value = []
  }
}

async function loadWorkerPerformance() {
  try {
    const response = await reportsService.getWorkerPerformance(activeFilters.value)
    workerPerformance.value = response?.data?.workers || []
  } catch {
    workerPerformance.value = []
  }
}

async function loadFeedbackSummary() {
  try {
    const response = await reportsService.getFeedbackSummary(activeFilters.value)
    feedbackSummary.value = response?.data || {}
  } catch {
    feedbackSummary.value = {}
  }
}

async function loadAll() {
  loading.value = true
  error.value = ''
  await Promise.all([
    loadSummary(),
    loadByStatus(),
    loadByCategory(),
    loadByPriority(),
    loadByLocation(),
    loadTrends(),
    loadWorkerPerformance(),
    loadFeedbackSummary(),
  ])
  loading.value = false
}

function applyFilters() {
  validationError.value = ''
  if (filters.date_from && filters.date_to && filters.date_from > filters.date_to) {
    validationError.value = 'From date must be on or before to date.'
    return
  }
  loadAll()
}

function resetFilters() {
  filters.date_from = ''
  filters.date_to = ''
  filters.status = ''
  filters.priority = ''
filters.location = ''
  loadAll()
}

// Guards against CSV/formula injection (OWASP) if any client-side rendering
// of user-controlled strings (e.g. worker names) is ever added elsewhere.
const exportConfig = {
  csv: { call: (filters) => reportsService.exportCsv(filters), extension: 'csv' },
  excel: { call: (filters) => reportsService.exportExcel(filters), extension: 'xlsx' },
  pdf: { call: (filters) => reportsService.exportPdf(filters), extension: 'pdf' },
}

async function exportReport(format) {
  const config = exportConfig[format]
  if (!config || exporting.value) return

  exporting.value = format
  error.value = ''
  try {
    const response = await config.call(activeFilters.value)
    const blob = new Blob([response.data])
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    const stamp = new Date().toISOString().slice(0, 10)
    link.href = url
    link.setAttribute('download', `complaint-report-${stamp}.${config.extension}`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (err) {
    error.value = await extractBlobErrorMessage(err) || `Could not export report as ${format.toUpperCase()}.`
  } finally {
    exporting.value = false
  }
}

// With responseType: 'blob', axios also delivers JSON error bodies (e.g. 400
// invalid date) as a Blob instead of parsed JSON — read and parse it manually.
async function extractBlobErrorMessage(err) {
  const data = err?.response?.data
  if (!(data instanceof Blob)) return err?.response?.data?.message
  try {
    const text = await data.text()
    return JSON.parse(text)?.message
  } catch {
    return null
  }
}

onMounted(() => {
  loadAll()
})
</script>
