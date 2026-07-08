<template>
  <div class="mx-auto max-w-4xl space-y-5">
    <div class="flex items-center gap-2 text-sm">
      <RouterLink to="/citizen/track" class="text-primary-600 hover:underline">← Back to complaints</RouterLink>
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
        <p v-if="errorHint" class="mt-2 text-sm text-red-600/90">{{ errorHint }}</p>
      </div>

      <div class="flex flex-wrap gap-3">
        <RouterLink to="/citizen/track" class="btn-primary px-4 py-2">Back to tracking</RouterLink>
        <RouterLink v-if="!authStore.isAuthenticated" to="/login" class="rounded-full border border-red-200 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-100">
          Sign in
        </RouterLink>
      </div>
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
                {{ statusLabel(complaint.status) }}
              </span>
              <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                {{ complaint.priority || 'medium' }} priority
              </span>
            </div>
          </div>

          <div v-if="complaint.image_url" class="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50">
            <img :src="photoUrl(complaint.image_url)" alt="Complaint photo" class="h-72 w-full object-cover sm:h-96" />
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
                  <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Routing</p>
                  <p class="mt-2 text-sm font-medium text-slate-900">{{ complaint.pincode || 'No pincode' }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ coordinateLabel }}</p>
                </div>
              </div>

              <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Complaint Details</p>
                <dl class="mt-3 grid gap-3 sm:grid-cols-2">
                  <div>
                    <dt class="text-xs text-slate-500">Category</dt>
                    <dd class="mt-1 text-sm font-medium text-slate-900 capitalize">{{ complaint.category }}</dd>
                  </div>
                  <div>
                    <dt class="text-xs text-slate-500">Priority</dt>
                    <dd class="mt-1 text-sm font-medium text-slate-900 capitalize">{{ complaint.priority }}</dd>
                  </div>
                  <div>
                    <dt class="text-xs text-slate-500">Latitude</dt>
                    <dd class="mt-1 text-sm font-medium text-slate-900">{{ coordinateText(complaint.latitude) }}</dd>
                  </div>
                  <div>
                    <dt class="text-xs text-slate-500">Longitude</dt>
                    <dd class="mt-1 text-sm font-medium text-slate-900">{{ coordinateText(complaint.longitude) }}</dd>
                  </div>
                </dl>
              </div>
            </div>

            <aside class="space-y-4">
              <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <p class="text-sm font-semibold text-slate-900">Status timeline</p>
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

              <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <p class="text-sm font-semibold text-slate-900">Feedback</p>
                <template v-if="complaint.feedback">
                  <div class="mt-3 rounded-xl bg-emerald-50 p-4">
                    <p class="text-sm font-semibold text-emerald-800">{{ complaint.feedback.rating }} / 5</p>
                    <p class="mt-2 text-sm text-emerald-700 whitespace-pre-line">{{ complaint.feedback.comment || 'No comment provided.' }}</p>
                  </div>
                </template>
                <template v-else>
                  <p class="mt-2 text-sm text-slate-500">
                    {{ canSubmitFeedback ? 'This complaint is ready for feedback.' : 'Feedback becomes available after the complaint is resolved or closed.' }}
                  </p>

                  <form v-if="canSubmitFeedback" class="mt-4 space-y-3" @submit.prevent="submitFeedback">
                    <div>
                      <label class="form-label" for="rating">Rating</label>
                      <select id="rating" v-model="feedbackForm.rating" class="form-input">
                        <option value="5">5 - Excellent</option>
                        <option value="4">4 - Good</option>
                        <option value="3">3 - Okay</option>
                        <option value="2">2 - Poor</option>
                        <option value="1">1 - Very poor</option>
                      </select>
                    </div>

                    <div>
                      <label class="form-label" for="comment">Comment</label>
                      <textarea
                        id="comment"
                        v-model.trim="feedbackForm.comment"
                        rows="4"
                        class="form-input"
                        placeholder="Tell us how the repair went..."
                      ></textarea>
                    </div>

                    <button type="submit" class="btn-primary w-full py-3" :disabled="submittingFeedback">
                      {{ submittingFeedback ? 'Submitting...' : 'Submit feedback' }}
                    </button>
                  </form>
                </template>
              </div>
            </aside>
          </div>
        </div>
      </section>
    </template>

    <section v-else class="card border-red-200 bg-red-50 text-red-700 space-y-4">
      <div>
        <p class="font-semibold">Unable to load complaint</p>
        <p class="mt-1 text-sm">Complaint details are not available for this route.</p>
        <p class="mt-2 text-sm text-red-600/90">Check the link and try again from your complaints list.</p>
      </div>

      <div class="flex flex-wrap gap-3">
        <RouterLink to="/citizen/track" class="btn-primary px-4 py-2">Back to tracking</RouterLink>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import complaintService from '@/services/complaint.service'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
const complaintId = computed(() => {
  const rawId = route.params.id
  if (Array.isArray(rawId)) return rawId[0] ?? null
  return rawId ?? null
})
const loading = ref(false)
const submittingFeedback = ref(false)
const error = ref('')
const errorHint = ref('')
const complaint = ref(null)

const feedbackForm = reactive({
  rating: '5',
  comment: '',
})

const statusSteps = [
  { key: 'pending', label: 'Pending', description: 'Awaiting review by the municipal team.' },
  { key: 'assigned', label: 'Assigned', description: 'Assigned to a field worker.' },
  { key: 'in_progress', label: 'In Progress', description: 'Work is actively underway.' },
  { key: 'resolved', label: 'Resolved', description: 'Marked as fixed and ready for verification.' },
  { key: 'closed', label: 'Closed', description: 'Complaint closed after resolution.' },
]

const timeline = computed(() => statusSteps.map((step) => ({
  ...step,
  active: isStepReached(step.key),
})))

const canSubmitFeedback = computed(() => {
  if (!complaint.value) return false
  return ['resolved', 'closed'].includes(complaint.value.status) && !complaint.value.feedback
})

const coordinateLabel = computed(() => {
  const lat = coordinateText(complaint.value?.latitude)
  const lng = coordinateText(complaint.value?.longitude)
  if (!lat && !lng) return 'Coordinates not available'
  return `${lat || '—'}, ${lng || '—'}`
})

function coordinateText(value) {
  return Number.isFinite(value) ? Number(value).toFixed(6) : ''
}

function photoUrl(imageUrl) {
  if (!imageUrl) return ''
  if (/^https?:\/\//i.test(imageUrl)) return imageUrl
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1'
  return `${apiBase.replace(/\/api\/v1$/, '')}${imageUrl}`
}

function statusLabel(status) {
  return (status || 'pending').replaceAll('_', ' ')
}

function statusBadgeClass(status) {
  if (['resolved', 'closed'].includes(status)) return 'bg-emerald-50 text-emerald-700'
  if (status === 'rejected') return 'bg-rose-50 text-rose-700'
  if (['assigned', 'in_progress'].includes(status)) return 'bg-sky-50 text-sky-700'
  return 'bg-amber-50 text-amber-700'
}

function statusAccentClass(status) {
  if (['resolved', 'closed'].includes(status)) return 'bg-emerald-500'
  if (status === 'rejected') return 'bg-rose-500'
  if (['assigned', 'in_progress'].includes(status)) return 'bg-sky-500'
  return 'bg-amber-500'
}

function isStepReached(step) {
  const order = ['pending', 'assigned', 'in_progress', 'resolved', 'closed']
  const currentIndex = order.indexOf(complaint.value?.status || 'pending')
  const stepIndex = order.indexOf(step)
  return stepIndex <= currentIndex && stepIndex >= 0
}

function timelineDotClass(step) {
  return step.active ? statusAccentClass(step.key) : 'bg-slate-300'
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

async function loadComplaint() {
  loading.value = true
  error.value = ''
  errorHint.value = ''

  if (!complaintId.value) {
    complaint.value = null
    error.value = 'Complaint ID is missing from the route.'
    errorHint.value = 'Open the complaint from the tracking page instead of typing the URL manually.'
    loading.value = false
    return
  }

  try {
    const response = await complaintService.getComplaint(complaintId.value)
    complaint.value = response?.data?.complaint || null
    if (!complaint.value) {
      error.value = 'Complaint not found.'
    }
  } catch (err) {
    const status = err?.response?.status
    const message = err?.response?.data?.message || ''

    if (status === 401) {
      error.value = 'Your session has expired.'
      errorHint.value = 'Sign in again to view complaint details.'
    } else if (message.toLowerCase().includes('permission')) {
      error.value = 'This complaint is not available in your account.'
      errorHint.value = 'Only the complaint owner can view this record. Open it from the correct citizen account.'
    } else if (status === 404) {
      error.value = 'Complaint not found.'
      errorHint.value = 'The complaint may have been deleted or the link may be invalid.'
    } else {
      error.value = message || 'Could not load the complaint details.'
      errorHint.value = 'Please try again from the complaints list.'
    }
  } finally {
    loading.value = false
  }
}

async function submitFeedback() {
  if (!complaint.value) return

  submittingFeedback.value = true
  error.value = ''

  try {
    const response = await complaintService.submitFeedback(complaint.value.id, {
      rating: Number(feedbackForm.rating),
      comment: feedbackForm.comment,
    })
    complaint.value.feedback = response?.data?.feedback || complaint.value.feedback
    feedbackForm.comment = ''
  } catch (err) {
    error.value = err?.response?.data?.message || 'Could not submit feedback.'
  } finally {
    submittingFeedback.value = false
  }
}

watch(
  complaintId,
  () => {
    loadComplaint()
  },
)

onMounted(() => {
  loadComplaint()
})
</script>