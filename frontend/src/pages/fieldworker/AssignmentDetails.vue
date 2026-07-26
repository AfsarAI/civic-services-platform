<template>
  <div class="mx-auto max-w-4xl space-y-5">
    <div class="flex items-center gap-2 text-sm">
      <RouterLink to="/fieldworker/dashboard" class="text-primary-600 hover:underline">← Back to my tasks</RouterLink>
    </div>

    <section v-if="loading" class="card space-y-4">
      <div class="h-6 w-40 animate-pulse rounded bg-slate-200"></div>
      <div class="h-8 w-3/4 animate-pulse rounded bg-slate-200"></div>
      <div class="h-40 animate-pulse rounded-2xl bg-slate-200"></div>
    </section>

    <section v-else-if="error" class="card border-red-200 bg-red-50 text-red-700 space-y-4">
      <div>
        <p class="font-semibold">Unable to load assignment</p>
        <p class="mt-1 text-sm">{{ error }}</p>
      </div>
      <RouterLink to="/fieldworker/dashboard" class="btn-primary px-4 py-2 inline-block">Back to my tasks</RouterLink>
    </section>

    <template v-else-if="assignment">
      <section class="rounded-3xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div class="h-2" :class="statusAccentClass(assignment.status)"></div>
        <div class="space-y-6 p-5 sm:p-6">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Assignment #{{ assignment.id }}</p>
              <h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">{{ complaint.title }}</h1>
              <p class="mt-2 text-sm text-slate-500">Assigned on {{ formatDate(assignment.assigned_at) }}</p>
              <p v-if="assignment.expected_completion_at" class="mt-1 text-sm font-medium text-slate-600">
                Expected completion: {{ formatDate(assignment.expected_completion_at) }}
              </p>
            </div>

            <div class="flex flex-wrap gap-2">
              <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="statusBadgeClass(assignment.status)">
                {{ (assignment.status || '').replaceAll('_', ' ') }}
              </span>
              <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                {{ complaint.priority || 'medium' }} priority
              </span>
            </div>
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
                  <a
                    v-if="mapLink"
                    :href="mapLink"
                    target="_blank"
                    rel="noopener"
                    class="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-primary-600 hover:underline"
                  >
                    Open in map →
                  </a>
                </div>
                <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Reported by</p>
                  <p class="mt-2 text-sm font-medium text-slate-900">{{ complaint.citizen_name || 'Citizen' }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ complaint.citizen_phone || 'Phone not provided' }}</p>
                </div>
              </div>

              <div v-if="assignment.notes" class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Latest notes</p>
                <p class="mt-2 text-sm text-slate-700 whitespace-pre-line">{{ assignment.notes }}</p>
              </div>

              <div v-if="assignment.evidence_url" class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Completion evidence</p>
                <img :src="mediaUrl(assignment.evidence_url)" alt="Repair evidence" class="mt-2 max-h-64 w-full rounded-xl object-cover" />
              </div>
            </div>

            <aside class="space-y-4">
              <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <p class="text-sm font-semibold text-slate-900">Task timeline</p>
                <div class="mt-4 space-y-4">
                  <div v-for="step in timeline" :key="step.key" class="flex gap-3">
                    <div class="mt-1 flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full" :class="timelineDotClass(step)"></div>
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

                <div v-if="complaintTerminal && isAssignmentActive" class="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                  This complaint was marked <span class="font-semibold">{{ complaint.status?.replaceAll('_', ' ') }}</span> by an administrator. No further action is needed on this task.
                </div>

                <!-- Accept -->
                <button
                  v-if="assignment.status === 'assigned' && !complaintTerminal"
                  class="btn-primary w-full py-2.5 text-sm"
                  :disabled="actionLoading"
                  @click="handleAccept"
                >
                  {{ actionLoading ? 'Accepting...' : 'Accept task' }}
                </button>

                <!-- Start work -->
                <div v-if="assignment.status === 'accepted' && !complaintTerminal" class="space-y-2">
                  <label class="form-label" for="progress-notes">Notes (optional)</label>
                  <textarea id="progress-notes" v-model.trim="notes" rows="3" class="form-input" placeholder="Materials ordered, work scheduled..."></textarea>
                  <button class="btn-primary w-full py-2.5 text-sm" :disabled="actionLoading" @click="handleStartProgress">
                    {{ actionLoading ? 'Updating...' : 'Start repair work' }}
                  </button>
                </div>

                <!-- Complete -->
                <div v-if="['accepted', 'in_progress'].includes(assignment.status) && !complaintTerminal" class="space-y-3 border-t border-slate-100 pt-3">
                  <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Mark as complete</p>
                  <input
                    ref="evidenceInputRef"
                    type="file"
                    accept="image/*"
                    capture="environment"
                    class="hidden"
                    @change="handleEvidenceSelected"
                  />
                  <div v-if="!evidencePreviewUrl" class="flex flex-col items-center gap-2 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-3 py-4 text-center">
                    <p class="text-xs text-slate-500">Upload photo evidence of completed repair (optional).</p>
                    <button type="button" class="btn-secondary px-3 py-1.5 text-xs" @click="evidenceInputRef?.click()">
                      Add photo evidence
                    </button>
                  </div>
                  <div v-else class="space-y-2">
                    <img :src="evidencePreviewUrl" alt="Evidence preview" class="max-h-40 w-full rounded-xl object-cover" />
                    <button type="button" class="btn-secondary w-full px-3 py-1.5 text-xs" @click="clearEvidence">Remove photo</button>
                  </div>
                  <button class="btn-primary w-full py-2.5 text-sm" :disabled="actionLoading || isUploadingEvidence" @click="handleComplete">
                    {{ actionLoading ? 'Completing...' : 'Mark as completed' }}
                  </button>
                </div>

                <!-- Reject -->
                <div v-if="['assigned', 'accepted', 'in_progress'].includes(assignment.status) && !complaintTerminal" class="space-y-2 border-t border-slate-100 pt-3">
                  <label class="form-label" for="reject-notes">Reason to reject (optional)</label>
                  <textarea id="reject-notes" v-model.trim="rejectNotes" rows="2" class="form-input" placeholder="Outside service area, duplicate task..."></textarea>
                  <button class="btn-danger w-full py-2.5 text-sm" :disabled="actionLoading" @click="handleReject">
                    {{ actionLoading ? 'Rejecting...' : 'Reject task' }}
                  </button>
                </div>

                <p v-if="['completed', 'rejected'].includes(assignment.status)" class="text-sm text-slate-500">
                  This task is {{ assignment.status }}. No further action is required.
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
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import fieldWorkerService from '@/services/fieldworker.service'

const route = useRoute()

const assignmentId = computed(() => {
  const rawId = route.params.id
  return Array.isArray(rawId) ? rawId[0] : rawId
})

const loading = ref(false)
const error = ref('')
const assignment = ref(null)

const actionLoading = ref(false)
const actionError = ref('')
const actionMessage = ref('')
const notes = ref('')
const rejectNotes = ref('')

const evidenceInputRef = ref(null)
const evidenceFile = ref(null)
const evidencePreviewUrl = ref('')
const evidenceUrl = ref('')
const isUploadingEvidence = ref(false)

const complaint = computed(() => assignment.value?.complaint || {})

// The complaint can move to a terminal state independently of the assignment
// (e.g. an administrator rejects or closes it) while this assignment is still
// `assigned`/`accepted`/`in_progress`. Once that happens, no further field
// worker action makes sense — the backend rejects it too (see
// FieldWorkerService._ensure_complaint_actionable).
const complaintTerminal = computed(() => {
  const status = complaint.value?.status
  return ['rejected', 'cancelled', 'resolved', 'closed'].includes(status)
})

const isAssignmentActive = computed(() => (
  ['assigned', 'accepted', 'in_progress'].includes(assignment.value?.status)
))

const statusSteps = [
  { key: 'assigned', label: 'Assigned', description: 'Task assigned to you by the administrator.' },
  { key: 'accepted', label: 'Accepted', description: 'You accepted the task.' },
  { key: 'in_progress', label: 'In Progress', description: 'Repair work is underway.' },
  { key: 'completed', label: 'Completed', description: 'Marked as complete with evidence (if provided).' },
]

const timeline = computed(() => {
  if (assignment.value?.status === 'rejected') {
    return [
      { key: 'assigned', label: 'Assigned', description: 'Task assigned to you by the administrator.', active: true },
      { key: 'rejected', label: 'Rejected', description: 'You rejected this task.', active: true },
    ]
  }
  const order = ['assigned', 'accepted', 'in_progress', 'completed']
  const currentIndex = order.indexOf(assignment.value?.status || 'assigned')
  return statusSteps.map((step) => ({
    ...step,
    active: order.indexOf(step.key) <= currentIndex && order.indexOf(step.key) >= 0,
  }))
})

const mapLink = computed(() => {
  const lat = complaint.value?.latitude
  const lng = complaint.value?.longitude
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return ''
  return `https://www.google.com/maps?q=${lat},${lng}`
})

function mediaUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1'
  return `${apiBase.replace(/\/api\/v1$/, '')}${url}`
}

function statusBadgeClass(status) {
  if (status === 'completed') return 'bg-emerald-50 text-emerald-700'
  if (status === 'rejected') return 'bg-rose-50 text-rose-700'
  if (['accepted', 'in_progress'].includes(status)) return 'bg-sky-50 text-sky-700'
  return 'bg-amber-50 text-amber-700'
}

function statusAccentClass(status) {
  if (status === 'completed') return 'bg-emerald-500'
  if (status === 'rejected') return 'bg-rose-500'
  if (['accepted', 'in_progress'].includes(status)) return 'bg-sky-500'
  return 'bg-amber-500'
}

function timelineDotClass(step) {
  if (step.key === 'rejected') return 'bg-rose-500'
  return step.active ? statusAccentClass(step.key) : 'bg-slate-300'
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

async function loadAssignment() {
  loading.value = true
  error.value = ''

  if (!assignmentId.value) {
    error.value = 'Assignment ID is missing from the route.'
    loading.value = false
    return
  }

  try {
    const response = await fieldWorkerService.getAssignment(assignmentId.value)
    assignment.value = response?.data?.assignment || null
    if (!assignment.value) {
      error.value = 'Assignment not found.'
    }
  } catch (err) {
    const status = err?.response?.status
    const message = err?.response?.data?.message || ''
    if (status === 401) {
      error.value = 'Your session has expired. Sign in again to view this task.'
    } else if (status === 404) {
      error.value = 'This task was not found or is not assigned to you.'
    } else {
      error.value = message || 'Could not load the assignment details.'
    }
  } finally {
    loading.value = false
  }
}

function resetActionAlerts() {
  actionError.value = ''
  actionMessage.value = ''
}

async function handleAccept() {
  resetActionAlerts()
  actionLoading.value = true
  try {
    const response = await fieldWorkerService.acceptAssignment(assignment.value.id)
    assignment.value = response?.data?.assignment || assignment.value
    actionMessage.value = 'Task accepted. You can now start the repair work.'
  } catch (err) {
    actionError.value = err?.response?.data?.message || 'Could not accept this task.'
  } finally {
    actionLoading.value = false
  }
}

async function handleStartProgress() {
  resetActionAlerts()
  actionLoading.value = true
  try {
    const response = await fieldWorkerService.updateProgress(assignment.value.id, {
      status: 'in_progress',
      notes: notes.value || undefined,
    })
    assignment.value = response?.data?.assignment || assignment.value
    notes.value = ''
    actionMessage.value = 'Repair work marked as in progress.'
  } catch (err) {
    actionError.value = err?.response?.data?.message || 'Could not update progress.'
  } finally {
    actionLoading.value = false
  }
}

async function handleReject() {
  resetActionAlerts()
  actionLoading.value = true
  try {
    const response = await fieldWorkerService.updateProgress(assignment.value.id, {
      status: 'rejected',
      notes: rejectNotes.value || undefined,
    })
    assignment.value = response?.data?.assignment || assignment.value
    rejectNotes.value = ''
    actionMessage.value = 'Task rejected and returned to the administrator for reassignment.'
  } catch (err) {
    actionError.value = err?.response?.data?.message || 'Could not reject this task.'
  } finally {
    actionLoading.value = false
  }
}

function handleEvidenceSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return

  if (evidencePreviewUrl.value) {
    URL.revokeObjectURL(evidencePreviewUrl.value)
  }

  evidenceFile.value = file
  evidenceUrl.value = ''
  evidencePreviewUrl.value = URL.createObjectURL(file)
}

function clearEvidence() {
  if (evidencePreviewUrl.value) {
    URL.revokeObjectURL(evidencePreviewUrl.value)
  }

  evidenceFile.value = null
  evidenceUrl.value = ''
  evidencePreviewUrl.value = ''
  if (evidenceInputRef.value) evidenceInputRef.value.value = ''
}

async function handleComplete() {
  resetActionAlerts()
  actionLoading.value = true
  try {
    let resolvedEvidenceUrl = evidenceUrl.value

    if (evidenceFile.value && !resolvedEvidenceUrl) {
      isUploadingEvidence.value = true
      const uploadResponse = await fieldWorkerService.uploadEvidencePhoto(evidenceFile.value)
      resolvedEvidenceUrl = uploadResponse?.data?.evidence_url || ''
      evidenceUrl.value = resolvedEvidenceUrl
      isUploadingEvidence.value = false
    }

    const response = await fieldWorkerService.completeAssignment(assignment.value.id, {
      evidence_url: resolvedEvidenceUrl || undefined,
    })
    assignment.value = response?.data?.assignment || assignment.value
    actionMessage.value = 'Task marked as completed.'
  } catch (err) {
    isUploadingEvidence.value = false
    actionError.value = err?.response?.data?.message || 'Could not complete this task.'
  } finally {
    actionLoading.value = false
  }
}

onMounted(() => {
  loadAssignment()
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
