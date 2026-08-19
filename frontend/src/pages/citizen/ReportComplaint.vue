<template>
  <div class="mx-auto max-w-3xl pb-24 sm:pb-8">
    <section class="mb-5 rounded-3xl bg-gradient-to-br from-slate-950 via-slate-900 to-primary-900 px-5 py-6 text-white shadow-xl sm:px-6">
      <p class="text-[11px] font-semibold uppercase tracking-[0.22em] text-sky-200">Pothole report</p>
      <h1 class="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Report a pothole in one minute</h1>
      <p class="mt-3 max-w-2xl text-sm leading-6 text-slate-200 sm:text-base">
        Take a photo, place the pin on the map, and submit from your phone. The location, pincode, and city will be filled automatically whenever possible.
      </p>

      <div class="mt-4 flex flex-wrap gap-2 text-xs font-semibold">
        <span class="rounded-full bg-white/10 px-3 py-1 backdrop-blur">Photo required</span>
        <span class="rounded-full bg-white/10 px-3 py-1 backdrop-blur">Map pin required</span>
        <span class="rounded-full bg-white/10 px-3 py-1 backdrop-blur">Pothole only</span>
      </div>
    </section>

    <form @submit.prevent="handleSubmit" class="space-y-4">
      <section class="card space-y-4">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-base font-semibold text-slate-900">Add a photo</h2>
            <p class="mt-1 text-xs text-slate-500">Use your camera or gallery. This is required before you can submit.</p>
          </div>
          <span class="rounded-full bg-amber-50 px-3 py-1 text-[11px] font-semibold text-amber-700">Required</span>
        </div>

        <div
          class="group flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center transition hover:border-primary-400 hover:bg-primary-50/40"
        >
          <input
            ref="cameraInputRef"
            type="file"
            accept="image/*"
            capture="environment"
            class="hidden"
            @change="handlePhotoSelected"
          />

          <input
            ref="galleryInputRef"
            type="file"
            accept="image/*"
            class="hidden"
            @change="handlePhotoSelected"
          />

          <div
            v-if="!photoPreviewUrl"
            class="flex flex-col items-center justify-center gap-3 text-slate-500"
          >
            <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-primary-600 shadow-sm ring-1 ring-slate-200">
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 16l3-3a2 2 0 012.828 0L12 16m-2-2l2-2a2 2 0 012.828 0L21 16m-9-9h.01M7 7h.01M12 19a9 9 0 100-18 9 9 0 000 18z"/>
              </svg>
            </div>
            <div>
              <p class="text-sm font-semibold text-slate-700">Add a pothole photo</p>
              <p class="mt-1 text-xs text-slate-500">Choose camera or gallery. Upload is required before submit.</p>
            </div>

            <div class="flex flex-wrap justify-center gap-2 pt-1">
              <button
                type="button"
                class="btn-primary px-4 py-2 text-xs sm:text-sm"
                :disabled="isUploadingPhoto"
                @click="openCameraPicker"
              >
                Take Photo
              </button>
              <button
                type="button"
                class="btn-secondary px-4 py-2 text-xs sm:text-sm"
                :disabled="isUploadingPhoto"
                @click="openGalleryPicker"
              >
                Upload Photo
              </button>
            </div>
          </div>

          <div v-else class="w-full space-y-3">
            <img :src="photoPreviewUrl" alt="Selected pothole photo preview" class="max-h-64 w-full rounded-2xl object-cover shadow-sm" />
            <div class="flex flex-wrap items-center justify-between gap-2 text-left">
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ photoName || 'Photo selected' }}</p>
                <p class="text-xs text-slate-500">{{ uploadStatusMessage }}</p>
              </div>
              <button
                type="button"
                class="btn-secondary px-3 py-2 text-xs"
                :disabled="isUploadingPhoto"
                @click.stop.prevent="clearPhoto"
              >
                Remove
              </button>
            </div>
          </div>
        </div>

        <p v-if="photoError" class="text-sm text-red-600">{{ photoError }}</p>
      </section>

      <section class="card space-y-4">
        <div class="flex items-center justify-between gap-3">
          <div>
            <h2 class="text-base font-semibold text-slate-900">Pin the pothole</h2>
            <p class="mt-1 text-xs text-slate-500">Use GPS, then tap or drag the pin if needed.</p>
          </div>
          <button
            type="button"
            class="btn-secondary px-3 py-2 text-xs"
            :disabled="isLocating || isResolvingLocation"
            @click="useCurrentLocation"
          >
            {{ isLocating ? 'Locating...' : 'Use current location' }}
          </button>
        </div>

        <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white">
          <div ref="mapRef" class="h-72 w-full sm:h-80"></div>
        </div>

        <p class="text-xs" :class="locationMessageClass">{{ locationMessage }}</p>
      </section>

      <section class="card space-y-4">
        <div class="grid gap-4 sm:grid-cols-2">
          <div class="sm:col-span-2">
            <label for="title" class="form-label">Title</label>
            <input
              id="title"
              v-model.trim="form.title"
              type="text"
              class="form-input"
              :class="fieldError('title') ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
              placeholder="Large pothole near the bus stop"
              @blur="touchField('title')"
              required
            />
            <p v-if="fieldError('title')" class="mt-1 text-xs text-red-600">{{ fieldError('title') }}</p>
          </div>

          <div class="sm:col-span-2">
            <label for="description" class="form-label">Description</label>
            <textarea
              id="description"
              v-model.trim="form.description"
              rows="4"
              class="form-input"
              :class="fieldError('description') ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
              placeholder="Tell us how deep it is, how it affects traffic, and any landmark nearby."
              @blur="touchField('description')"
              required
            ></textarea>
            <p v-if="fieldError('description')" class="mt-1 text-xs text-red-600">{{ fieldError('description') }}</p>
          </div>

          <div>
            <label for="priority" class="form-label">Priority</label>
            <select id="priority" v-model="form.priority" class="form-input">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>

          <div>
            <label class="form-label">Category</label>
            <input type="text" class="form-input bg-slate-50" value="Pothole" readonly />
          </div>
        </div>
      </section>

      <section class="card space-y-4">
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <label class="form-label">Latitude</label>
            <input :value="coordinateText(form.latitude)" type="text" class="form-input bg-slate-50" readonly />
          </div>
          <div>
            <label class="form-label">Longitude</label>
            <input :value="coordinateText(form.longitude)" type="text" class="form-input bg-slate-50" readonly />
          </div>
          <div>
            <label class="form-label">Pincode</label>
            <input
              v-model.trim="form.pincode"
              type="text"
              maxlength="6"
              class="form-input"
              placeholder="6-digit pincode"
              @input="handlePincodeInput"
              @blur="lookupByPincode"
            />
          </div>

          <div>
            <label class="form-label">City</label>
            <select v-model="form.city_id" class="form-input">
              <option value="">Select city</option>
              <option v-for="city in cityOptions" :key="city.city_id" :value="String(city.city_id)">
                {{ city.city_name }}{{ city.state ? `, ${city.state}` : '' }}
              </option>
            </select>
          </div>

          <div>
            <label class="form-label">Area</label>
            <input :value="locationHints.area || 'Not available yet'" type="text" class="form-input bg-slate-50" readonly />
          </div>
          <div>
            <label class="form-label">District</label>
            <input :value="locationHints.district || 'Not available yet'" type="text" class="form-input bg-slate-50" readonly />
          </div>

          <div class="sm:col-span-2 lg:col-span-3">
            <label for="address" class="form-label">Address / landmark</label>
            <textarea
              id="address"
              v-model.trim="form.address"
              rows="2"
              class="form-input"
              placeholder="Optional: add a nearby landmark for quicker routing"
            ></textarea>
          </div>
        </div>

        <div v-if="manualModeEnabled" class="rounded-2xl border border-amber-200 bg-amber-50 p-4">
          <p class="text-sm font-semibold text-amber-800">Manual fallback</p>
          <p class="mt-1 text-xs text-amber-700">
            Reverse geocoding failed. Enter a pincode, choose a city, or search manually.
          </p>

          <div class="mt-3 flex gap-2">
            <input v-model.trim="manualCityQuery" type="text" class="form-input" placeholder="Search city" />
            <button type="button" class="btn-secondary px-3 py-2 text-xs" :disabled="isSearchingCities" @click="searchCitiesManually">
              {{ isSearchingCities ? 'Searching...' : 'Search' }}
            </button>
          </div>
        </div>
      </section>

      <div v-if="error" class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
        {{ error }}
      </div>

      <div class="sticky bottom-0 z-20 -mx-4 border-t border-slate-200 bg-white/95 px-4 py-3 backdrop-blur sm:static sm:mx-0 sm:border-0 sm:bg-transparent sm:px-0 sm:py-0">
        <button type="submit" class="btn-primary w-full py-4 text-base" :disabled="isLoading || isCheckingDuplicates || !canSubmit">
          {{ isCheckingDuplicates ? 'Checking for similar reports...' : (isLoading ? 'Submitting...' : 'Submit pothole report') }}
        </button>
      </div>
    </form>

    <!-- Nearby duplicate warning -->
    <div v-if="showDuplicateModal" class="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/60 p-0 sm:items-center sm:p-4">
      <div class="max-h-[85vh] w-full overflow-y-auto rounded-t-3xl bg-white p-5 shadow-2xl sm:max-w-lg sm:rounded-3xl sm:p-6">
        <p class="text-xs font-semibold uppercase tracking-wide text-amber-600">Similar report found nearby</p>
        <h2 class="mt-1 text-lg font-bold text-slate-900">Is this the same pothole?</h2>
        <p class="mt-2 text-sm text-slate-600">
          {{ duplicateCandidates.length === 1 ? 'A similar report already exists nearby.' : `${duplicateCandidates.length} similar reports already exist nearby.` }}
          Compare the photo below — you can still submit if this is a different issue.
        </p>

        <div class="mt-4 space-y-3">
          <div
            v-for="candidate in duplicateCandidates"
            :key="candidate.id"
            class="flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-3"
          >
            <img
              v-if="candidate.image_url"
              :src="resolveMediaUrl(candidate.image_url)"
              alt="Nearby existing report photo"
              class="h-20 w-20 shrink-0 rounded-xl object-cover"
            />
            <div class="min-w-0 flex-1">
              <p class="text-sm font-semibold text-slate-900 truncate">{{ candidate.title }}</p>
              <p class="mt-0.5 text-xs text-slate-500">
                {{ candidate.distance_meters }}m away · {{ candidate.status?.replaceAll('_', ' ') }}
              </p>
              <p v-if="candidate.address" class="mt-1 text-xs text-slate-500 truncate">{{ candidate.address }}</p>
            </div>
          </div>
        </div>

        <div class="mt-5 flex flex-col gap-2 sm:flex-row">
          <button type="button" class="btn-secondary w-full py-2.5 text-sm" @click="dismissDuplicateWarning">
            Cancel, let me review
          </button>
          <button type="button" class="btn-primary w-full py-2.5 text-sm" :disabled="isLoading" @click="confirmSubmitAnyway">
            {{ isLoading ? 'Submitting...' : 'Submit anyway' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import L from 'leaflet'

import complaintService from '@/services/complaint.service'
import locationService from '@/services/location.service'

const router = useRouter()

const mapRef = ref(null)
const cameraInputRef = ref(null)
const galleryInputRef = ref(null)

const isLoading = ref(false)
const isLocating = ref(false)
const isResolvingLocation = ref(false)
const isUploadingPhoto = ref(false)
const isSearchingCities = ref(false)
const isCheckingDuplicates = ref(false)
const manualModeEnabled = ref(false)
const error = ref(null)
const photoError = ref('')
const locationMessage = ref('Take a photo, then tap the map or use GPS to place the pin.')
const locationMessageType = ref('info')
const photoPreviewUrl = ref('')
const photoName = ref('')
const uploadStatusMessage = ref('No photo uploaded yet.')
const manualCityQuery = ref('')
const duplicateCandidates = ref([])
const showDuplicateModal = ref(false)
const duplicateWarningAcknowledged = ref(false)
const touched = reactive({ title: false, description: false })

const form = reactive({
  title: '',
  description: '',
  priority: 'medium',
  address: '',
  latitude: null,
  longitude: null,
  pincode: '',
  city_id: '',
  image_url: '',
})

const locationHints = reactive({
  area: '',
  district: '',
  state: '',
})

const cityOptions = ref([])

let map = null
let marker = null
let currentObjectUrl = ''

const canSubmit = computed(() => {
  return Boolean(
    form.title.trim()
    && form.description.trim()
    && form.image_url
    && Number.isFinite(form.latitude)
    && Number.isFinite(form.longitude)
  )
})

const locationMessageClass = computed(() => {
  if (locationMessageType.value === 'error') return 'text-red-600'
  if (locationMessageType.value === 'success') return 'text-emerald-600'
  return 'text-slate-500'
})

function touchField(field) {
  touched[field] = true
}

function fieldError(field) {
  if (!touched[field] && !error.value) return null

  if (field === 'title') {
    if (!form.title || !form.title.trim()) return 'Please enter a title.'
    if (form.title.trim().length < 5) return 'Title must be at least 5 characters.'
    return null
  }

  if (field === 'description') {
    if (!form.description || !form.description.trim()) return 'Please enter a description.'
    if (form.description.trim().length < 10) return 'Description must be at least 10 characters.'
    return null
  }

  return null
}

function coordinateText(value) {
  return Number.isFinite(value) ? Number(value).toFixed(6) : ''
}

function resolveMediaUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1'
  return `${apiBase.replace(/\/api\/v1$/, '')}${url}`
}

function setLocationMessage(message, type = 'info') {
  locationMessage.value = message
  locationMessageType.value = type
}

function clearPhotoPreviewUrl() {
  if (currentObjectUrl) {
    URL.revokeObjectURL(currentObjectUrl)
    currentObjectUrl = ''
  }
}

function clearPickerValues() {
  if (cameraInputRef.value) {
    cameraInputRef.value.value = ''
  }
  if (galleryInputRef.value) {
    galleryInputRef.value.value = ''
  }
}

function openCameraPicker() {
  photoError.value = ''
  cameraInputRef.value?.click()
}

function openGalleryPicker() {
  photoError.value = ''
  galleryInputRef.value?.click()
}

function setMarker(latitude, longitude, shouldCenter = true) {
  const position = [latitude, longitude]

  if (!marker) {
    marker = L.marker(position, { draggable: true }).addTo(map)
    marker.on('dragend', async () => {
      const point = marker.getLatLng()
      await setLocationFromMap(point.lat, point.lng, false)
    })
  } else {
    marker.setLatLng(position)
  }

  if (shouldCenter) {
    map.setView(position, Math.max(map.getZoom(), 14))
  }
}

function initMap() {
  if (!mapRef.value || map) return

  map = L.map(mapRef.value, {
    minZoom: 4,
    maxZoom: 19,
  }).setView([22.5937, 78.9629], 5)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map)

  map.on('click', async (event) => {
    await setLocationFromMap(event.latlng.lat, event.latlng.lng, true)
  })
}

async function setLocationFromMap(latitude, longitude, shouldCenter = true) {
  if (!map) return

  error.value = null
  form.latitude = Number(latitude)
  form.longitude = Number(longitude)
  setMarker(form.latitude, form.longitude, shouldCenter)

  await resolveLocationDetails(form.latitude, form.longitude)
}

function clearLocationHints() {
  locationHints.area = ''
  locationHints.district = ''
  locationHints.state = ''
}

async function resolveLocationDetails(latitude, longitude) {
  isResolvingLocation.value = true
  try {
    const response = await locationService.reverseGeocode(latitude, longitude)
    const data = response?.data || {}

    manualModeEnabled.value = false
    form.address = data.address || form.address
    form.pincode = data.pincode || form.pincode
    locationHints.area = data.area || ''
    locationHints.district = data.district || ''
    locationHints.state = data.state || ''

    cityOptions.value = data.city_options || []
    if (data.city_id) {
      form.city_id = String(data.city_id)
    } else if (cityOptions.value.length === 1) {
      form.city_id = String(cityOptions.value[0].city_id)
    } else if (!cityOptions.value.some((city) => String(city.city_id) === String(form.city_id))) {
      form.city_id = ''
    }

    if (data.pincode) {
      setLocationMessage('Location captured from map pin.', 'success')
    } else {
      setLocationMessage('Location captured, but pincode was not detected. Please fill it manually if needed.', 'error')
    }
  } catch {
    manualModeEnabled.value = true
    clearLocationHints()
    cityOptions.value = []
    form.city_id = ''
    setLocationMessage('Reverse geocoding failed. You can still submit by entering pincode and selecting a city.', 'error')
  } finally {
    isResolvingLocation.value = false
  }
}

async function useCurrentLocation() {
  if (!navigator.geolocation) {
    setLocationMessage('Geolocation is not supported on this device. Tap the map to place the pin.', 'error')
    return
  }

  isLocating.value = true
  setLocationMessage('Detecting current location...', 'info')

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      isLocating.value = false
      await setLocationFromMap(position.coords.latitude, position.coords.longitude, true)
    },
    () => {
      isLocating.value = false
      setLocationMessage('GPS was not available. Tap the map to drop a pin manually.', 'error')
    },
    {
      enableHighAccuracy: true,
      timeout: 12000,
      maximumAge: 30000,
    },
  )
}

function handlePincodeInput() {
  form.pincode = (form.pincode || '').replace(/\D/g, '').slice(0, 6)
}

async function lookupByPincode() {
  if (!/^\d{6}$/.test(form.pincode || '')) {
    if (!form.pincode) {
      cityOptions.value = []
    }
    return
  }

  try {
    const response = await locationService.lookupPincode(form.pincode)
    const cities = response?.data?.cities || []
    cityOptions.value = cities

    if (cities.length === 1) {
      form.city_id = String(cities[0].city_id)
      setLocationMessage('Pincode resolved to a single city.', 'success')
      return
    }

    if (cities.length > 1 && !cities.some((city) => String(city.city_id) === String(form.city_id))) {
      form.city_id = ''
      setLocationMessage('Multiple cities match this pincode. Please select one.', 'info')
      return
    }

    if (cities.length === 0) {
      form.city_id = ''
      setLocationMessage('No city mapping found for this pincode.', 'error')
    }
  } catch {
    cityOptions.value = []
    form.city_id = ''
    setLocationMessage('Could not resolve city from pincode right now.', 'error')
  }
}

async function searchCitiesManually() {
  if (!manualCityQuery.value || manualCityQuery.value.trim().length < 2) {
    setLocationMessage('Type at least 2 characters to search a city.', 'info')
    return
  }

  isSearchingCities.value = true
  try {
    const response = await locationService.searchCities(manualCityQuery.value.trim(), 12)
    const items = (response?.data?.items || []).map((city) => ({
      city_id: city.id,
      city_name: city.name,
      state: city.state || null,
    }))
    cityOptions.value = items
    if (items.length === 1) {
      form.city_id = String(items[0].city_id)
    }
    setLocationMessage(items.length ? `Found ${items.length} city option(s).` : 'No city matches found.', items.length ? 'success' : 'error')
  } catch {
    setLocationMessage('City search failed. Try again in a moment.', 'error')
  } finally {
    isSearchingCities.value = false
  }
}

async function handlePhotoSelected(event) {
  photoError.value = ''
  const file = event.target.files?.[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    photoError.value = 'Please choose an image file.'
    return
  }

  if (file.size > 8 * 1024 * 1024) {
    photoError.value = 'Photo must be 8 MB or smaller.'
    return
  }

  clearPhotoPreviewUrl()
  currentObjectUrl = URL.createObjectURL(file)
  photoPreviewUrl.value = currentObjectUrl
  photoName.value = file.name
  uploadStatusMessage.value = 'Uploading photo...'
  isUploadingPhoto.value = true

  try {
    const response = await complaintService.uploadComplaintPhoto(file)
    form.image_url = response?.data?.image_url || ''
    uploadStatusMessage.value = 'Photo uploaded and ready to submit.'
    if (response?.data?.image_url) {
      photoPreviewUrl.value = response.data.image_url
    }
  } catch (uploadError) {
    form.image_url = ''
    uploadStatusMessage.value = 'Photo upload failed.'
    photoError.value = uploadError?.response?.data?.message || uploadError?.message || 'Unable to upload photo.'
    clearPhotoPreviewUrl()
    photoPreviewUrl.value = ''
    photoName.value = ''
    clearPickerValues()
  } finally {
    isUploadingPhoto.value = false
  }
}

function clearPhoto() {
  form.image_url = ''
  photoName.value = ''
  uploadStatusMessage.value = 'No photo uploaded yet.'
  photoPreviewUrl.value = ''
  clearPhotoPreviewUrl()
  clearPickerValues()
}

async function handleSubmit() {
  touched.title = true
  touched.description = true

  const titleError = fieldError('title')
  const descriptionError = fieldError('description')
  if (titleError || descriptionError) {
    error.value = titleError || descriptionError
    return
  }

  if (!form.image_url) {
    error.value = 'Please upload a photo before submitting.'
    return
  }

  if (!Number.isFinite(form.latitude) || !Number.isFinite(form.longitude)) {
    error.value = 'Please place the pothole pin on the map.'
    return
  }

  if (form.pincode && !/^\d{6}$/.test(form.pincode)) {
    error.value = 'Pincode must be exactly 6 digits.'
    return
  }

  if (!form.pincode && !form.city_id) {
    error.value = 'Please enter a pincode or select a city for routing.'
    return
  }

  if (!duplicateWarningAcknowledged.value) {
    error.value = null
    isCheckingDuplicates.value = true
    try {
      const response = await complaintService.checkNearbyDuplicates(
        Number(form.latitude), Number(form.longitude),
      )
      const candidates = response?.data?.candidates || []
      if (candidates.length > 0) {
        duplicateCandidates.value = candidates
        showDuplicateModal.value = true
        return
      }
    } catch {
      // Non-critical: if the advisory check fails, proceed with submission.
    } finally {
      isCheckingDuplicates.value = false
    }
  }

  await performSubmit()
}

function dismissDuplicateWarning() {
  showDuplicateModal.value = false
}

async function confirmSubmitAnyway() {
  duplicateWarningAcknowledged.value = true
  showDuplicateModal.value = false
  await performSubmit()
}

async function performSubmit() {
  isLoading.value = true
  error.value = null

  try {
    const payload = {
      title: form.title.trim(),
      description: form.description.trim(),
      category: 'pothole',
      priority: form.priority,
      address: form.address.trim() || null,
      latitude: Number(form.latitude),
      longitude: Number(form.longitude),
      pincode: form.pincode || null,
      city_id: form.city_id ? Number(form.city_id) : null,
      image_url: form.image_url,
    }

    const response = await complaintService.submitComplaint(payload)
    const complaintId = response?.data?.complaint?.id
    if (complaintId) {
      await router.push({ name: 'complaint-details', params: { id: complaintId } })
      return
    }

    await router.push({ name: 'citizen-dashboard' })
  } catch (submitError) {
    error.value = submitError?.response?.data?.message || submitError?.message || 'Failed to submit complaint.'
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  await nextTick()
  initMap()
  await useCurrentLocation()
})

onBeforeUnmount(() => {
  clearPhotoPreviewUrl()
  if (map) {
    map.remove()
    map = null
    marker = null
  }
})
</script>