<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900 mb-2">Reports &amp; Analytics</h1>
      <p class="text-gray-500 text-sm">Platform-wide analytics available only to the System Administrator.</p>
    </div>

    <div v-if="error" class="card border-red-200 bg-red-50 text-red-700 p-4 text-sm">{{ error }}</div>

    <!-- Summary cards -->
    <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
      <div v-for="stat in summaryCards" :key="stat.label" class="card text-center">
        <p class="text-2xl font-bold" :class="stat.color">{{ stat.value }}</p>
        <p class="text-xs text-gray-500 mt-1">{{ stat.label }}</p>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
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
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import reportsService from '@/services/reports.service'

const error = ref('')
const summary = ref({})
const byStatus = ref([])
const byCategory = ref([])
const trends = ref([])
const trendPeriod = ref('daily')
const workerPerformance = ref([])

const summaryCards = computed(() => [
  { label: 'Total Complaints', value: summary.value.total ?? 0, color: 'text-gray-800' },
  { label: 'Open', value: summary.value.open ?? 0, color: 'text-amber-600' },
  { label: 'Resolved', value: summary.value.resolved ?? 0, color: 'text-green-600' },
  { label: 'Resolution Rate', value: `${summary.value.resolution_rate ?? 0}%`, color: 'text-primary-600' },
  { label: 'Avg. Resolution (hrs)', value: summary.value.avg_resolution_hours ?? '—', color: 'text-slate-600' },
])

function trendBarHeight(count) {
  const max = Math.max(...trends.value.map((p) => p.count), 1)
  return Math.max(4, Math.round((count / max) * 120))
}

async function loadSummary() {
  try {
    const response = await reportsService.getSummary()
    summary.value = response?.data || {}
  } catch (err) {
    error.value = err?.response?.data?.message || 'Could not load report summary.'
  }
}

async function loadByStatus() {
  try {
    const response = await reportsService.getByStatus()
    byStatus.value = response?.data?.breakdown || []
  } catch {
    byStatus.value = []
  }
}

async function loadByCategory() {
  try {
    const response = await reportsService.getByCategory()
    byCategory.value = response?.data?.breakdown || []
  } catch {
    byCategory.value = []
  }
}

async function loadTrends() {
  try {
    const response = await reportsService.getTrends(trendPeriod.value)
    trends.value = response?.data?.data || []
  } catch {
    trends.value = []
  }
}

async function loadWorkerPerformance() {
  try {
    const response = await reportsService.getWorkerPerformance()
    workerPerformance.value = response?.data?.workers || []
  } catch {
    workerPerformance.value = []
  }
}

onMounted(() => {
  loadSummary()
  loadByStatus()
  loadByCategory()
  loadTrends()
  loadWorkerPerformance()
})
</script>

