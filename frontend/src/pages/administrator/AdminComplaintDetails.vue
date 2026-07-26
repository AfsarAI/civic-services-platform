<template>
  <div class="mx-auto max-w-4xl space-y-5">
    <div class="flex items-center gap-2 text-sm">
      <RouterLink to="/admin/dashboard" class="text-primary-600 hover:underline">← Back to dashboard</RouterLink>
    </div>

    <section v-if="loading" class="card space-y-4">
      <div class="h-6 w-40 animate-pulse rounded bg-slate-200"></div>
      <div class="h-8 w-3/4 animate-pulse rounded bg-slate-200"></div>
      <div class="h-40 animate-pulse rounded-2xl bg-slate-200"></div>
    </section>

    <section v-else-if="error" class="card border-red-200 bg-red-50 text-red-700 space-y-4">
      <div>
        <p class="font-semibold">Unable to load complaint</p>
        <p class="mt-1 text-sm">{{ error }}</p>
      </div>
      <RouterLink to="/admin/dashboard" class="btn-primary px-4 py-2 inline-block">Back to dashboard</RouterLink>
    </section>

    <template v-else-if="complaint">
      <section class="rounded-3xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div class="h-2" :class="statusAccentClass(complaint.status)"></div>
        <div class="space-y-6 p-5 sm:p-6">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Complaint #{{ complaint.id }}</p>
              <h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">{{ complaint.title }}</h1>
              <p class="mt-2 text-sm text-slate-500">Submitted on {{ formatDate(complaint.created_at) }}</p>
            </div>

            <div class="flex flex-wrap gap-2">
              <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="statusBadgeClass(complaint.status)">
                {{ statusLabel }}
              </span>
              <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 capitalize">
                {{ complaint.priority || 'medium' }} priority
              </span>
            </div>
          </div>

          <div v-if="awaitingVerification" class="rounded-2xl border border-purple-200 bg-purple-50 px-4 py-3 text-sm text-purple-800">
            <span class="font-semibold">Marked as fixed, pending verification.</span>
            The field worker completed this repair<template v-if="complaint.repair_completed_at"> on {{ formatDate(complaint.repair_completed_at) }}</template>.
            Review the completion evidence and field-worker remarks below before making a decision.
          </div>

          <div v-if="complaint.image_url" class="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50">
            <img :src="mediaUrl(complaint.image_url)" alt="Complaint photo" class="h-72 w-full object-cover sm:h-96" />
          </div>

          <div class="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <div class="space-y-4">
              <div>
                <p class="form-label">Description</p>
                <p class="mt-1 text-sm leading-6 text-slate-700 whitespace-pre-line">{{ complaint.description }}</p>
              </div>

              <div class="grid gap-3 sm:grid-cols-2">
                <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Location</p>
                  <p class="mt-2 text-sm font-medium text-slate-900">{{ complaint.city_name || 'Unknown city' }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ complaint.address || 'Address not provided' }}</p>
                </div>
                <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Reported by</p>
                  <p class="mt-2 text-sm font-medium text-slate-900">{{ complaint.citizen?.full_name || 'Citizen' }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ complaint.citizen?.phone || complaint.citizen?.email || '' }}</p>
                </div>
              </div>

              <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Assignment History</p>
                <div v-if="!complaint.assignments?.length" class="mt-2 text-sm text-slate-500">
                  Not yet assigned to a field worker.
                </div>
                <ul v-else class="mt-3 space-y-3">
                  <li v-for="a in complaint.assignments" :key="a.id" class="rounded-xl bg-white border border-slate-200 p-3">
                    <div class="flex items-center justify-between gap-2">
                      <span class="text-sm font-semibold text-slate-900">{{ a.worker_name || `Worker #${a.worker_id}` }}</span>
                      <span class="rounded-full px-2 py-0.5 text-[11px] font-semibold" :class="assignmentBadgeClass(a.status)">
                        {{ a.status?.replaceAll('_', ' ') }}
                      </span>
                    </div>
                    <p class="mt-1 text-xs text-slate-500">Assigned {{ formatDate(a.assigned_at) }}</p>
                    <p class="mt-1 text-xs text-slate-500">Expected completion: {{ formatDate(a.expected_completion_at) }}</p>
                    <p v-if="a.completed_at" class="mt-1 text-xs font-medium text-slate-600">
                      Repair completed: {{ formatDate(a.completed_at) }}
                    </p>
                    <p class="mt-1 text-xs text-slate-500">Last progress update: {{ formatDate(a.updated_at) }}</p>
                    <p v-if="a.notes" class="mt-1 text-xs text-slate-600">Notes: {{ a.notes }}</p>
                    <img v-if="a.evidence_url" :src="mediaUrl(a.evidence_url)" alt="Repair evidence" class="mt-2 max-h-48 w-full rounded-lg object-cover" />
                  </li>
                </ul>
              </div>

              <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div class="flex items-center justify-between gap-3">
                  <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Verification History</p>
                  <span class="rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize" :class="verificationBadgeClass(complaint.verification_status)">
                    {{ complaint.verification_status?.replaceAll('_', ' ') || 'pending' }}
                  </span>
                </div>
                <p v-if="!complaint.verification_history?.length" class="mt-2 text-sm text-slate-500">
                  No verification decisions recorded.
                </p>
                <ol v-else class="mt-3 space-y-3">
                  <li v-for="verification in complaint.verification_history" :key="verification.id" class="rounded-xl border border-slate-200 bg-white p-3">
                    <div class="flex flex-wrap items-center justify-between gap-2">
                      <span class="text-sm font-semibold capitalize" :class="verification.decision === 'approved' ? 'text-emerald-700' : 'text-amber-700'">
                        {{ verification.decision.replaceAll('_', ' ') }}
                      </span>
                      <span class="text-xs text-slate-500">{{ formatDate(verification.created_at) }}</span>
                    </div>
                    <p class="mt-1 text-xs text-slate-500">
                      Complaint #{{ verification.complaint_id }} · Assignment #{{ verification.assignment_id }}
                    </p>
                    <p class="mt-1 text-xs text-slate-500">
                      Administrator: {{ verification.administrator_name || `#${verification.administrator_id}` }}
                    </p>
                    <p v-if="verification.remarks" class="mt-2 text-sm text-slate-700">
                      {{ verification.remarks }}
                    </p>
                  </li>
                </ol>
              </div>

              <div v-if="complaint.feedback" class="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
                <p class="text-xs font-semibold uppercase tracking-wide text-emerald-700">Citizen Feedback</p>
                <p class="mt-2 text-sm font-semibold text-emerald-800">{{ complaint.feedback.rating }} / 5</p>
                <p class="mt-1 text-sm text-emerald-700">{{ complaint.feedback.comment || 'No comment provided.' }}</p>
              </div>
            </div>

            <aside class="space-y-4">
              <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <p class="text-sm font-semibold text-slate-900">Status timeline</p>
                <div class="mt-4 space-y-4">
                  <div v-for="step in timeline" :key="step.key" class="flex gap-3">
                    <div class="mt-1 flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full" :class="step.active ? statusAccentClass(step.key) : 'bg-slate-300'"></div>
                    <div>
                      <p class="text-sm font-medium text-slate-900">{{ step.label }}</p>
                      <p class="text-xs text-slate-500">{{ step.description }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm space-y-4">
                <p class="text-sm font-semibold text-slate-900">Actions</p>

                <transition name="fade">
                  <div v-if="actionError" class="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                    {{ actionError }}
                  </div>
                </transition>
                <transition name="fade">
                  <div v-if="actionMessage" class="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
                    {{ actionMessage }}
                  </div>
                </transition>

                <!-- Priority (TPS-81) -->
                <div class="space-y-2">
                  <label class="form-label" for="priority">Priority</label>
                  <select id="priority" v-model="priorityForm" class="form-input">
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                  <button
                    class="btn-secondary w-full py-2 text-sm"
                    :disabled="priorityForm === complaint.priority || actionLoading"
                    @click="handleUpdatePriority"
                  >
                    Update priority
                  </button>
                </div>

                <!-- Assign (pending/assigned) -->
                <div v-if="['pending', 'assigned'].includes(complaint.status)" class="space-y-2 border-t border-slate-100 pt-3">
                  <label class="form-label" for="worker">Assign to field worker</label>
                  <select id="worker" v-model="assignWorkerId" class="form-input">
                    <option value="">Select a field worker</option>
                    <option v-for="w in activeFieldWorkers" :key="w.id" :value="w.id">{{ w.full_name }}</option>
                  </select>
                  <label class="form-label" for="expected-completion">Expected completion</label>
                  <input
                    id="expected-completion"
                    v-model="expectedCompletionAt"
                    type="datetime-local"
                    class="form-input"
                  />
                  <button class="btn-primary w-full py-2 text-sm" :disabled="!assignWorkerId || actionLoading" @click="handleAssign">
                    Assign complaint
                  </button>
                </div>

                <!-- Verify completed repair (TPS-83) -->
                <div v-if="awaitingVerification" class="space-y-2 border-t border-slate-100 pt-3">
                  <p class="text-xs font-medium text-purple-700">
                    Field worker marked this repair complete. Record your verification decision.
                  </p>
                  <label class="form-label" for="verification-remarks">
                    Administrator remarks
                    <span class="font-normal text-slate-400">(required for rework)</span>
                  </label>
                  <textarea
                    id="verification-remarks"
                    v-model="verificationRemarks"
                    rows="3"
                    maxlength="2000"
                    class="form-input"
                    placeholder="Add verification notes or explain the required rework"
                  ></textarea>
                  <button
                    class="btn-primary w-full py-2.5 text-sm"
                    :disabled="actionLoading"
                    @click="handleVerification('approved')"
                  >
                    Approve Repair
                  </button>
                  <button
                    class="btn-secondary w-full py-2.5 text-sm"
                    :disabled="actionLoading || !verificationRemarks.trim()"
                    @click="handleVerification('rework_requested')"
                  >
                    Request Rework
                  </button>
                </div>

                <!-- Close (resolved -> closed) -->
                <button
                  v-if="complaint.status === 'resolved'"
                  class="btn-primary w-full py-2.5 text-sm"
                  :disabled="actionLoading"
                  @click="handleStatusChange('closed')"
                >
                  Close Complaint
                </button>

                <!-- Reject (any pre-terminal status) -->
                <button
                  v-if="['pending', 'assigned', 'in_progress'].includes(complaint.status)"
                  class="btn-danger w-full py-2.5 text-sm"
                  :disabled="actionLoading"
                  @click="handleStatusChange('rejected')"
                >
                  Reject Complaint
                </button>

                <p v-if="['closed', 'rejected'].includes(complaint.status)" class="text-sm text-slate-500">
                  This complaint is {{ complaint.status }}. No further status changes are possible.
                </p>
              </div>
            </aside>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import complaintService from '@/services/complaint.service'
import adminService from '@/services/admin.service'

const route = useRoute()

const complaintId = computed(() => {
  const rawId = route.params.id
  return Array.isArray(rawId) ? rawId[0] : rawId
})

const loading = ref(false)
const error = ref('')
const complaint = ref(null)

const actionLoading = ref(false)
const actionError = ref('')
const actionMessage = ref('')
const priorityForm = ref('medium')

const activeFieldWorkers = ref([])
const assignWorkerId = ref('')
const expectedCompletionAt = ref('')
const verificationRemarks = ref('')

// The complaint's own `status` intentionally stays `in_progress` even after the
// field worker's assignment reaches `completed` — an administrator must still
// verify the repair before marking the complaint `resolved`.
const awaitingVerification = computed(() => {
  if (!complaint.value) return false
  return complaint.value.status === 'in_progress' && complaint.value.assignment_status === 'completed'
})

const statusLabel = computed(() => {
  if (awaitingVerification.value) return 'Pending Verification'
  return complaint.value?.status?.replaceAll('_', ' ')
})

const statusSteps = [
  { key: 'pending', label: 'Pending', description: 'Awaiting review by the municipal team.' },
  { key: 'assigned', label: 'Assigned', description: 'Assigned to a field worker.' },
  { key: 'in_progress', label: 'In Progress', description: 'Repair work is underway.' },
  { key: 'resolved', label: 'Resolved', description: 'Verified as fixed; awaiting final closure.' },
  { key: 'closed', label: 'Closed', description: 'Verified and closed by an administrator.' },
]

const timeline = computed(() => {
  if (complaint.value?.status === 'rejected') {
    return [
      { key: 'pending', label: 'Pending', description: 'Complaint was submitted.', active: true },
      { key: 'rejected', label: 'Rejected', description: 'Rejected by an administrator.', active: true },
    ]
  }
  if (complaint.value?.status === 'cancelled') {
    return [
      { key: 'pending', label: 'Pending', description: 'Complaint was submitted.', active: true },
      { key: 'cancelled', label: 'Cancelled', description: 'Cancelled by the citizen before assignment.', active: true },
    ]
  }
  const order = ['pending', 'assigned', 'in_progress', 'resolved', 'closed']
  const currentIndex = order.indexOf(complaint.value?.status || 'pending')
  return statusSteps.map((step) => ({
    ...step,
    description: step.key === 'in_progress' && awaitingVerification.value
      ? 'Marked as fixed, pending verification.'
      : step.description,
    active: order.indexOf(step.key) <= currentIndex && order.indexOf(step.key) >= 0,
  }))
})

function mediaUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1'
  return `${apiBase.replace(/\/api\/v1$/, '')}${url}`
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

function assignmentBadgeClass(status) {
  if (status === 'completed') return 'bg-emerald-100 text-emerald-700'
  if (status === 'rejected') return 'bg-rose-100 text-rose-700'
  if (['accepted', 'in_progress'].includes(status)) return 'bg-sky-100 text-sky-700'
  return 'bg-amber-100 text-amber-700'
}

function verificationBadgeClass(status) {
  if (status === 'approved') return 'bg-emerald-100 text-emerald-700'
  if (status === 'rework_requested') return 'bg-amber-100 text-amber-700'
  return 'bg-purple-100 text-purple-700'
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function resetActionAlerts() {
  actionError.value = ''
  actionMessage.value = ''
}

async function loadComplaint() {
  loading.value = true
  error.value = ''

  if (!complaintId.value) {
    error.value = 'Complaint ID is missing from the route.'
    loading.value = false
    return
  }

  try {
    const response = await complaintService.getAdminComplaint(complaintId.value)
    complaint.value = response?.data?.complaint || null
    if (complaint.value) {
      priorityForm.value = complaint.value.priority || 'medium'
    } else {
      error.value = 'Complaint not found.'
    }
  } catch (err) {
    const status = err?.response?.status
    error.value = status === 404
      ? 'Complaint not found, or is outside your administrator scope.'
      : (err?.response?.data?.message || 'Could not load the complaint.')
  } finally {
    loading.value = false
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

async function handleUpdatePriority() {
  resetActionAlerts()
  actionLoading.value = true
  try {
    const response = await complaintService.updateAdminComplaint(complaint.value.id, { priority: priorityForm.value })
    complaint.value = response?.data?.complaint || complaint.value
    actionMessage.value = 'Priority updated.'
  } catch (err) {
    actionError.value = err?.response?.data?.message || 'Could not update priority.'
  } finally {
    actionLoading.value = false
  }
}

async function handleStatusChange(status) {
  resetActionAlerts()
  actionLoading.value = true
  try {
    const response = await complaintService.updateAdminComplaint(complaint.value.id, { status })
    complaint.value = response?.data?.complaint || complaint.value
    actionMessage.value = `Complaint status updated to ${status.replaceAll('_', ' ')}.`
  } catch (err) {
    actionError.value = err?.response?.data?.message || 'Could not update complaint status.'
  } finally {
    actionLoading.value = false
  }
}

async function handleVerification(decision) {
  if (decision === 'rework_requested' && !verificationRemarks.value.trim()) return
  resetActionAlerts()
  actionLoading.value = true
  try {
    const response = await complaintService.verifyRepair(complaint.value.id, {
      decision,
      remarks: verificationRemarks.value.trim() || undefined,
    })
    complaint.value = response?.data?.complaint || complaint.value
    verificationRemarks.value = ''
    actionMessage.value = decision === 'approved'
      ? 'Repair approved and complaint marked as resolved.'
      : 'Rework requested and field worker notified.'
  } catch (err) {
    actionError.value = err?.response?.data?.message || 'Could not record the verification decision.'
  } finally {
    actionLoading.value = false
  }
}

async function handleAssign() {
  if (!assignWorkerId.value) return
  resetActionAlerts()
  actionLoading.value = true
  try {
    await complaintService.assignComplaint(complaint.value.id, {
      worker_id: Number(assignWorkerId.value),
      expected_completion_at: expectedCompletionAt.value
        ? new Date(expectedCompletionAt.value).toISOString()
        : null,
    })
    assignWorkerId.value = ''
    expectedCompletionAt.value = ''
    actionMessage.value = 'Complaint assigned successfully.'
    await loadComplaint()
  } catch (err) {
    actionError.value = err?.response?.data?.message || 'Could not assign this complaint.'
  } finally {
    actionLoading.value = false
  }
}

watch(complaintId, () => {
  loadComplaint()
})

onMounted(() => {
  loadComplaint()
  loadActiveFieldWorkers()
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
