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

            <div class="flex flex-wrap items-center gap-2">
              <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="statusBadgeClass(complaint.status)">
                {{ statusLabel(complaint.status) }}
              </span>
              <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                {{ complaint.priority || 'medium' }} priority
              </span>
              <button
                v-if="complaint.status === 'pending' && !isEditing"
                type="button"
                class="btn-secondary px-4 py-1.5 text-xs"
                @click="startEdit"
              >
                Edit complaint
              </button>
              <button
                v-if="complaint.status === 'pending' && !isEditing"
                type="button"
                class="btn-danger px-4 py-1.5 text-xs"
                :disabled="isCancelling"
                @click="handleCancelComplaint"
              >
                {{ isCancelling ? 'Cancelling...' : 'Cancel complaint' }}
              </button>
            </div>
          </div>

          <div v-if="awaitingVerification" class="rounded-2xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-800" role="status">
            <span class="font-semibold">Repair completed</span> — the field worker finished this repair
            <template v-if="complaint.repair_completed_at"> on {{ formatDate(complaint.repair_completed_at) }}</template>.
            An administrator still needs to verify and resolve it before feedback opens up.
          </div>

          <transition name="fade">
            <div v-if="successMessage" class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800" role="status">
              {{ successMessage }}
            </div>
          </transition>
          <div v-if="editError" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
            {{ editError }}
          </div>

          <!-- Edit form (TPS-74) -->
          <section v-if="isEditing" class="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:p-5">
            <p class="text-sm font-semibold text-slate-900">Edit your complaint</p>
            <p class="text-xs text-slate-500">
              You can update the description, road/street name, pothole location, and photo while this complaint is still pending assignment.
            </p>

            <div>
              <label class="form-label" for="edit-description">Description</label>
              <textarea id="edit-description" v-model.trim="editForm.description" rows="4" class="form-input" required></textarea>
            </div>

            <div>
              <label class="form-label" for="edit-address">Road / Street Name</label>
              <textarea id="edit-address" v-model.trim="editForm.address" rows="2" class="form-input" placeholder="e.g. MG Road, near the bus stop"></textarea>
            </div>

            <div class="space-y-2">
              <p class="form-label">Pothole Location</p>
              <p class="text-xs text-slate-500">Tap the map or drag the pin to update the location.</p>
              <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white">
                <div ref="editMapRef" class="h-56 w-full sm:h-64"></div>
              </div>
              <p class="text-xs text-slate-500">{{ coordinateText(editForm.latitude) || '—' }}, {{ coordinateText(editForm.longitude) || '—' }}</p>
            </div>

            <div class="space-y-2">
              <p class="form-label">Photograph</p>
              <input ref="editCameraInputRef" type="file" accept="image/*" capture="environment" class="hidden" @change="handleEditPhotoSelected" />
              <input ref="editGalleryInputRef" type="file" accept="image/*" class="hidden" @change="handleEditPhotoSelected" />

              <img v-if="editForm.image_url" :src="photoUrl(editForm.image_url)" alt="Current complaint photo" class="h-40 w-full rounded-xl object-cover" />
              <div class="flex flex-wrap gap-2">
                <button type="button" class="btn-secondary px-3 py-2 text-xs" :disabled="isUploadingEditPhoto" @click="editCameraInputRef?.click()">
                  Take new photo
                </button>
                <button type="button" class="btn-secondary px-3 py-2 text-xs" :disabled="isUploadingEditPhoto" @click="editGalleryInputRef?.click()">
                  Upload new photo
                </button>
              </div>
              <p v-if="isUploadingEditPhoto" class="text-xs text-slate-500">Uploading photo...</p>
            </div>

            <div class="flex flex-wrap gap-3 pt-2">
              <button type="button" class="btn-primary px-4 py-2 text-sm" :disabled="isSavingEdit || isUploadingEditPhoto" @click="handleSaveEdit">
                {{ isSavingEdit ? 'Saving...' : 'Save changes' }}
              </button>
              <button type="button" class="btn-secondary px-4 py-2 text-sm" :disabled="isSavingEdit" @click="cancelEdit">
                Cancel
              </button>
            </div>
          </section>

          <div v-if="complaint.image_url && !isEditing" class="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50">
            <img :src="photoUrl(complaint.image_url)" alt="Complaint photo" class="h-72 w-full object-cover sm:h-96" />
          </div>

          <div v-if="!isEditing" class="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <div class="space-y-4">
              <div>
                <p class="form-label">Description</p>
                <p class="mt-1 text-sm leading-6 text-slate-700 whitespace-pre-line">{{ complaint.description }}</p>
              </div>

              <div v-if="complaint.repair_evidence_url" class="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
                <p class="text-xs font-semibold uppercase tracking-wide text-emerald-700">Repair Photo</p>
                <p class="mt-1 text-xs text-emerald-600">
                  Uploaded by the field worker<template v-if="complaint.repair_completed_at"> on {{ formatDate(complaint.repair_completed_at) }}</template> as proof of completed repair.
                </p>
                <img
                  :src="photoUrl(complaint.repair_evidence_url)"
                  alt="Repair completion photo uploaded by field worker"
                  class="mt-3 h-64 w-full rounded-xl border border-emerald-200 object-cover sm:h-80"
                />
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
                  <transition name="fade">
                    <div v-if="feedbackSuccessMessage" class="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700" role="status">
                      {{ feedbackSuccessMessage }}
                    </div>
                  </transition>
                  <div class="mt-3 rounded-xl bg-emerald-50 p-4">
                    <p class="text-sm font-semibold text-emerald-800">
                      <span class="text-amber-500">{{ '★'.repeat(complaint.feedback.rating) }}{{ '☆'.repeat(5 - complaint.feedback.rating) }}</span>
                      {{ complaint.feedback.rating }} / 5
                    </p>
                    <p class="mt-2 text-sm text-emerald-700 whitespace-pre-line">{{ complaint.feedback.comment || 'No comment provided.' }}</p>
                    <p class="mt-2 text-xs text-emerald-600">Submitted on {{ formatDate(complaint.feedback.created_at) }}</p>
                  </div>
                </template>
                <template v-else>
                  <p class="mt-2 text-sm text-slate-500">
                    {{ canSubmitFeedback
                      ? 'This complaint is ready for feedback.'
                      : awaitingVerification
                        ? 'The field worker has marked the repair complete. Feedback unlocks once an administrator verifies and resolves the complaint.'
                        : 'Feedback becomes available after the complaint is resolved or closed.' }}
                  </p>

                  <transition name="fade">
                    <div v-if="feedbackSuccessMessage" class="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700" role="status">
                      {{ feedbackSuccessMessage }}
                    </div>
                  </transition>
                  <div v-if="feedbackError" class="mt-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700" role="alert">
                    {{ feedbackError }}
                  </div>

                  <form v-if="canSubmitFeedback" class="mt-4 space-y-3" @submit.prevent="submitFeedback">
                    <div>
                      <p class="form-label">Rating</p>
                      <div class="flex items-center gap-1" role="radiogroup" aria-label="Rating out of 5 stars">
                        <button
                          v-for="star in 5"
                          :key="star"
                          type="button"
                          class="text-2xl leading-none transition-colors"
                          :class="star <= feedbackForm.rating ? 'text-amber-400' : 'text-slate-300 hover:text-amber-300'"
                          :aria-label="`Rate ${star} out of 5 stars`"
                          :aria-pressed="star === feedbackForm.rating"
                          @click="feedbackForm.rating = star"
                        >
                          ★
                        </button>
                        <span class="ml-2 text-xs font-medium text-slate-500">{{ feedbackForm.rating }} / 5</span>
                      </div>
                    </div>

                    <div>
                      <label class="form-label" for="comment">Comment (optional)</label>
                      <textarea
                        id="comment"
                        v-model.trim="feedbackForm.comment"
                        rows="4"
                        class="form-input"
                        maxlength="1000"
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
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import L from 'leaflet'

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
const successMessage = ref('')
const feedbackError = ref('')
const feedbackSuccessMessage = ref('')

const feedbackForm = reactive({
  rating: 5,
  comment: '',
})

// ── Edit complaint (TPS-74) ────────────────────────────────────────────────
const isEditing = ref(false)
const isSavingEdit = ref(false)
const editError = ref('')
const editMapRef = ref(null)
const editCameraInputRef = ref(null)
const editGalleryInputRef = ref(null)
const isUploadingEditPhoto = ref(false)

// ── Cancel complaint (TPS-75) ──────────────────────────────────────────────
const isCancelling = ref(false)

const editForm = reactive({
  description: '',
  address: '',
  latitude: null,
  longitude: null,
  image_url: '',
})

let editMap = null
let editMarker = null

function startEdit() {
  if (!complaint.value) return
  editError.value = ''
  successMessage.value = ''
  Object.assign(editForm, {
    description: complaint.value.description || '',
    address: complaint.value.address || '',
    latitude: complaint.value.latitude ?? null,
    longitude: complaint.value.longitude ?? null,
    image_url: complaint.value.image_url || '',
  })
  isEditing.value = true
  nextTick(() => initEditMap())
}

function cancelEdit() {
  isEditing.value = false
  editError.value = ''
  destroyEditMap()
}

function initEditMap() {
  if (!editMapRef.value || editMap) return

  const hasCoords = Number.isFinite(editForm.latitude) && Number.isFinite(editForm.longitude)
  const center = hasCoords ? [editForm.latitude, editForm.longitude] : [22.5937, 78.9629]

  editMap = L.map(editMapRef.value, { minZoom: 4, maxZoom: 19 }).setView(center, hasCoords ? 15 : 5)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(editMap)

  if (hasCoords) {
    setEditMarker(editForm.latitude, editForm.longitude)
  }

  editMap.on('click', (event) => {
    setEditMarker(event.latlng.lat, event.latlng.lng)
  })
}

function setEditMarker(latitude, longitude) {
  editForm.latitude = Number(latitude)
  editForm.longitude = Number(longitude)

  if (!editMarker) {
    editMarker = L.marker([latitude, longitude], { draggable: true }).addTo(editMap)
    editMarker.on('dragend', () => {
      const point = editMarker.getLatLng()
      editForm.latitude = point.lat
      editForm.longitude = point.lng
    })
  } else {
    editMarker.setLatLng([latitude, longitude])
  }
}

function destroyEditMap() {
  if (editMap) {
    editMap.remove()
    editMap = null
    editMarker = null
  }
}

async function handleEditPhotoSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return

  editError.value = ''
  isUploadingEditPhoto.value = true
  try {
    const response = await complaintService.uploadComplaintPhoto(file)
    editForm.image_url = response?.data?.image_url || editForm.image_url
  } catch (err) {
    editError.value = err?.response?.data?.message || 'Could not upload the new photo.'
  } finally {
    isUploadingEditPhoto.value = false
    event.target.value = ''
  }
}

async function handleSaveEdit() {
  if (!complaint.value) return
  editError.value = ''
  isSavingEdit.value = true

  try {
    const response = await complaintService.updateComplaint(complaint.value.id, {
      description: editForm.description,
      address: editForm.address,
      latitude: editForm.latitude,
      longitude: editForm.longitude,
      image_url: editForm.image_url,
    })
    complaint.value = response?.data?.complaint || complaint.value
    isEditing.value = false
    destroyEditMap()
    successMessage.value = 'Complaint updated successfully.'
  } catch (err) {
    editError.value = err?.response?.data?.message || 'Could not update the complaint.'
  } finally {
    isSavingEdit.value = false
  }
}

async function handleCancelComplaint() {
  if (!complaint.value) return

  const confirmed = window.confirm(
    'Cancel complaint #' + complaint.value.id + ' - "' + complaint.value.title + '"? This cannot be undone.',
  )
  if (!confirmed) return

  editError.value = ''
  successMessage.value = ''
  isCancelling.value = true
  try {
    const response = await complaintService.deleteComplaint(complaint.value.id)
    complaint.value = response?.data?.complaint || { ...complaint.value, status: 'cancelled' }
    successMessage.value = response?.message || 'Complaint cancelled successfully.'
  } catch (err) {
    editError.value = err?.response?.data?.message || 'Could not cancel this complaint.'
  } finally {
    isCancelling.value = false
  }
}


const statusSteps = [
  { key: 'pending', label: 'Pending', description: 'Awaiting review by the municipal team.' },
  { key: 'assigned', label: 'Assigned', description: 'Assigned to a field worker.' },
  { key: 'in_progress', label: 'In Progress', description: 'Work is actively underway.' },
  { key: 'resolved', label: 'Resolved', description: 'Marked as fixed and ready for verification.' },
  { key: 'closed', label: 'Closed', description: 'Complaint closed after resolution.' },
]

const timeline = computed(() => {
  if (complaint.value?.status === 'cancelled') {
    return [
      { key: 'pending', label: 'Pending', description: 'Complaint was submitted.', active: true },
      { key: 'cancelled', label: 'Cancelled', description: 'You cancelled this complaint.', active: true },
    ]
  }
  return statusSteps.map((step) => ({
    ...step,
    active: isStepReached(step.key),
  }))
})

const canSubmitFeedback = computed(() => {
  if (!complaint.value) return false
  return ['resolved', 'closed'].includes(complaint.value.status) && !complaint.value.feedback
})

// The field worker's task status (`assignment_status`) is tracked separately from
// the complaint's own status. A complaint can stay `in_progress` even after the
// repair work itself is done, while an administrator verifies and resolves it.
const awaitingVerification = computed(() => {
  if (!complaint.value) return false
  return complaint.value.status === 'in_progress' && complaint.value.assignment_status === 'completed'
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
  if (status === 'in_progress' && awaitingVerification.value) return 'Awaiting verification'
  return (status || 'pending').replaceAll('_', ' ')
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

function isStepReached(step) {
  const order = ['pending', 'assigned', 'in_progress', 'resolved', 'closed']
  const currentIndex = order.indexOf(complaint.value?.status || 'pending')
  const stepIndex = order.indexOf(step)
  return stepIndex <= currentIndex && stepIndex >= 0
}

function timelineDotClass(step) {
  if (step.key === 'cancelled') return 'bg-slate-400'
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
  feedbackError.value = ''
  feedbackSuccessMessage.value = ''

  try {
    const response = await complaintService.submitFeedback(complaint.value.id, {
      rating: Number(feedbackForm.rating),
      comment: feedbackForm.comment,
    })
    complaint.value.feedback = response?.data?.feedback || complaint.value.feedback
    feedbackForm.rating = 5
    feedbackForm.comment = ''
    feedbackSuccessMessage.value = response?.message || 'Feedback submitted successfully.'
  } catch (err) {
    feedbackError.value = err?.response?.data?.message || 'Could not submit feedback.'
  } finally {
    submittingFeedback.value = false
  }
}

watch(
  complaintId,
  () => {
    isEditing.value = false
    successMessage.value = ''
    destroyEditMap()
    loadComplaint()
  },
)

onMounted(() => {
  loadComplaint()
})

onBeforeUnmount(() => {
  destroyEditMap()
})
</script>