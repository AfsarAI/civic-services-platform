<template>
  <div class="space-y-6">
    <section class="card overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-primary-900 text-white">
      <p class="mb-3 inline-flex rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-200">
        System Administration
      </p>
      <h1 class="text-3xl font-bold tracking-tight">System Settings</h1>
      <p class="mt-3 max-w-2xl text-sm text-slate-200/85">
        Configure platform-wide options. Changes take effect immediately and are logged in the audit trail.
      </p>
    </section>

    <div v-if="successMessage" class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800" role="status">
      {{ successMessage }}
    </div>
    <div v-if="serverError" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
      {{ serverError }}
    </div>

    <section v-if="loading" class="card">
      <p class="text-sm text-slate-500">Loading settings...</p>
    </section>

    <form v-else class="card space-y-6" @submit.prevent="handleSave">
      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <label class="form-label" for="site_name">Site Name</label>
          <input id="site_name" v-model.trim="form.site_name" type="text" class="form-input" required />
        </div>
        <div>
          <label class="form-label" for="support_email">Support Email</label>
          <input id="support_email" v-model.trim="form.support_email" type="email" class="form-input" placeholder="support@civicservices.local" />
        </div>
      </div>

      <div>
        <label class="form-label" for="default_priority">Default Complaint Priority</label>
        <select id="default_priority" v-model="form.default_complaint_priority" class="form-input sm:w-64">
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="urgent">Urgent</option>
        </select>
      </div>

      <div>
        <label class="form-label" for="duplicate_radius">Duplicate Detection Radius (meters)</label>
        <input
          id="duplicate_radius"
          v-model.number="form.duplicate_detection_radius_meters"
          type="number"
          min="10"
          max="2000"
          class="form-input sm:w-64"
        />
        <p class="mt-1 text-xs text-slate-500">
          Complaints reported within this distance of each other are flagged as possible duplicates
          (citizen submission warning + administrator review panel).
        </p>
      </div>

      <div class="space-y-4 border-t border-slate-100 pt-5">
        <div class="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
          <div>
            <p class="text-sm font-semibold text-slate-900">Maintenance Mode</p>
            <p class="text-xs text-slate-500">Blocks citizen and field worker logins immediately. Administrators can still sign in.</p>
          </div>
          <input v-model="form.maintenance_mode" type="checkbox" class="h-5 w-5 rounded border-slate-300 text-primary-600 focus:ring-primary-500" />
        </div>

        <div class="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
          <div>
            <p class="text-sm font-semibold text-slate-900">Status-Change Notifications</p>
            <p class="text-xs text-slate-500">When enabled, citizens and field workers receive notifications for assignment, resolution, closure, and rejection events.</p>
          </div>
          <input v-model="form.notify_on_status_change" type="checkbox" class="h-5 w-5 rounded border-slate-300 text-primary-600 focus:ring-primary-500" />
        </div>
      </div>

      <div v-if="settings?.updated_at" class="text-xs text-slate-400">
        Last updated {{ formatDate(settings.updated_at) }}
      </div>

      <button type="submit" class="btn-primary w-full py-3" :disabled="isSaving">
        {{ isSaving ? 'Saving...' : 'Save Settings' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import adminService from '@/services/admin.service'

const loading = ref(true)
const isSaving = ref(false)
const successMessage = ref('')
const serverError = ref('')
const settings = ref(null)

const form = reactive({
  site_name: '',
  support_email: '',
  maintenance_mode: false,
  notify_on_status_change: true,
  default_complaint_priority: 'medium',
  duplicate_detection_radius_meters: 50,
})

async function loadSettings() {
  loading.value = true
  try {
    const response = await adminService.getSystemSettings()
    settings.value = response?.data?.settings || null
    if (settings.value) {
      Object.assign(form, {
        site_name: settings.value.site_name || '',
        support_email: settings.value.support_email || '',
        maintenance_mode: !!settings.value.maintenance_mode,
        notify_on_status_change: !!settings.value.notify_on_status_change,
        default_complaint_priority: settings.value.default_complaint_priority || 'medium',        duplicate_detection_radius_meters: settings.value.duplicate_detection_radius_meters || 50,      })
    }
  } catch (err) {
    serverError.value = err?.response?.data?.message || 'Could not load system settings.'
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  successMessage.value = ''
  serverError.value = ''
  isSaving.value = true
  try {
    const response = await adminService.updateSystemSettings({
      ...form,
      support_email: form.support_email || null,
    })
    settings.value = response?.data?.settings || settings.value
    successMessage.value = 'Settings updated successfully.'
  } catch (err) {
    serverError.value = err?.response?.data?.message || 'Could not update system settings.'
  } finally {
    isSaving.value = false
  }
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

onMounted(() => {
  loadSettings()
})
</script>
