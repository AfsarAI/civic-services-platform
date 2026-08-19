<template>
  <div class="space-y-6">
    <section class="card overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-primary-900 text-white">
      <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div class="max-w-2xl">
          <p class="mb-3 inline-flex rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-200">
            System Administration
          </p>
          <h1 class="text-3xl font-bold tracking-tight">Manage Municipal Administrators</h1>
          <p class="mt-3 text-sm text-slate-200/85">
            Register city-wise administrators, review their assigned municipality, and deactivate accounts that should no longer access complaint-management features.
          </p>
        </div>

        <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur-sm">
            <p class="text-xs uppercase tracking-wide text-slate-300">Total</p>
            <p class="mt-2 text-2xl font-semibold">{{ adminStats.total }}</p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur-sm">
            <p class="text-xs uppercase tracking-wide text-slate-300">Active</p>
            <p class="mt-2 text-2xl font-semibold">{{ adminStats.active }}</p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur-sm">
            <p class="text-xs uppercase tracking-wide text-slate-300">Cities</p>
            <p class="mt-2 text-2xl font-semibold">{{ cityInventory.length }}</p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur-sm">
            <p class="text-xs uppercase tracking-wide text-slate-300">Inactive</p>
            <p class="mt-2 text-2xl font-semibold">{{ adminStats.inactive }}</p>
          </div>
        </div>
      </div>
    </section>

    <div class="grid gap-6 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,1.35fr)]">
      <section class="card">
        <div class="mb-6 flex items-start justify-between gap-4">
          <div>
            <h2 class="text-xl font-semibold text-gray-900">Create Municipal Administrator</h2>
            <p class="mt-1 text-sm text-gray-500">
              Use the existing administrator auth system and assign exactly one city to the new account.
            </p>
          </div>
          <span class="rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-primary-700">
            Secure Registration
          </span>
        </div>

        <div
          v-if="successMessage"
          class="mb-5 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
          role="status"
        >
          {{ successMessage }}
        </div>

        <div
          v-if="serverError"
          class="mb-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
          role="alert"
        >
          {{ serverError }}
        </div>

        <form class="space-y-5" @submit.prevent="handleCreate">
          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="form-label" for="first_name">First Name</label>
              <input
                id="first_name"
                v-model.trim="form.first_name"
                class="form-input"
                :class="inputErrorClass('first_name')"
                placeholder="Aarav"
                @blur="touch('first_name')"
              />
              <p v-if="fieldError('first_name')" class="mt-1 text-xs text-red-600">{{ fieldError('first_name') }}</p>
            </div>
            <div>
              <label class="form-label" for="last_name">Last Name</label>
              <input
                id="last_name"
                v-model.trim="form.last_name"
                class="form-input"
                :class="inputErrorClass('last_name')"
                placeholder="Sharma"
                @blur="touch('last_name')"
              />
              <p v-if="fieldError('last_name')" class="mt-1 text-xs text-red-600">{{ fieldError('last_name') }}</p>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="form-label" for="username">Username</label>
              <input
                id="username"
                v-model.trim="form.username"
                class="form-input"
                :class="inputErrorClass('username')"
                placeholder="agra_admin"
                @blur="touch('username')"
              />
              <p v-if="fieldError('username')" class="mt-1 text-xs text-red-600">{{ fieldError('username') }}</p>
            </div>
            <div>
              <label class="form-label" for="email">Email</label>
              <input
                id="email"
                v-model.trim="form.email"
                type="email"
                class="form-input"
                :class="inputErrorClass('email')"
                placeholder="agra.admin@example.com"
                @blur="touch('email')"
              />
              <p v-if="fieldError('email')" class="mt-1 text-xs text-red-600">{{ fieldError('email') }}</p>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="form-label" for="phone">Phone Number</label>
              <input
                id="phone"
                v-model.trim="form.phone"
                type="tel"
                class="form-input"
                :class="inputErrorClass('phone')"
                placeholder="9876543210"
                @blur="touch('phone')"
              />
              <p v-if="fieldError('phone')" class="mt-1 text-xs text-red-600">{{ fieldError('phone') }}</p>
            </div>
            <div class="relative">
              <label class="form-label" for="pincode">Pincode</label>
              <input
                id="pincode"
                v-model.trim="form.pincode"
                class="form-input"
                :class="inputErrorClass('pincode')"
                placeholder="226001"
                maxlength="6"
                @input="handlePincodeInput"
                @focus="handlePincodeFocus"
                @blur="handlePincodeBlur"
              />
              <div
                v-if="isPincodeSuggesting"
                class="absolute right-3 top-[2.15rem] text-[11px] text-slate-400"
              >
                Searching...
              </div>

              <div
                v-if="showPincodeSuggestions && pincodeSuggestions.length"
                class="absolute z-20 mt-1 max-h-56 w-full overflow-y-auto rounded-xl border border-slate-200 bg-white p-1 shadow-xl"
              >
                <button
                  v-for="suggestion in pincodeSuggestions"
                  :key="`${suggestion.pincode}-${suggestion.city_id}-${suggestion.area_name}`"
                  type="button"
                  class="block w-full rounded-lg px-3 py-2 text-left text-xs text-slate-700 transition-colors hover:bg-slate-100"
                  @mousedown.prevent="applyPincodeSuggestion(suggestion)"
                >
                  <div class="font-semibold text-slate-900">{{ suggestion.pincode }} - {{ suggestion.area_name || suggestion.city_name }}</div>
                  <div class="mt-0.5 text-[11px] text-slate-500">
                    {{ suggestion.district || suggestion.city_name }}{{ suggestion.state ? `, ${suggestion.state}` : '' }}
                  </div>
                </button>
              </div>

              <p v-if="fieldError('pincode')" class="mt-1 text-xs text-red-600">{{ fieldError('pincode') }}</p>
              <p v-else class="mt-1 text-xs text-slate-500">Type at least 2 digits to see pincode suggestions.</p>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="form-label" for="city_id">City</label>
              <select
                id="city_id"
                v-model="form.city_id"
                class="form-input"
                :class="inputErrorClass('city_id')"
                @blur="touch('city_id')"
              >
                <option value="" disabled>Select city</option>
                <option v-for="city in cityOptions" :key="city.city_id" :value="city.city_id">
                  {{ city.city_name }}{{ city.state ? `, ${city.state}` : '' }}
                </option>
              </select>
              <p v-if="fieldError('city_id')" class="mt-1 text-xs text-red-600">{{ fieldError('city_id') }}</p>
              <p v-else-if="lookupMessage" class="mt-1 text-xs text-slate-500">{{ lookupMessage }}</p>
            </div>
            <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Authorization</p>
              <p class="mt-2 text-sm text-slate-700">
                New accounts are created with the shared <strong>administrator</strong> role and the
                <strong>municipal</strong> administrator level.
              </p>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="form-label" for="password">Password</label>
              <input
                id="password"
                v-model="form.password"
                type="password"
                class="form-input"
                :class="inputErrorClass('password')"
                placeholder="Municipal@123"
                @blur="touch('password')"
              />
              <p v-if="fieldError('password')" class="mt-1 text-xs text-red-600">{{ fieldError('password') }}</p>
            </div>
            <div>
              <label class="form-label" for="confirm_password">Confirm Password</label>
              <input
                id="confirm_password"
                v-model="form.confirm_password"
                type="password"
                class="form-input"
                :class="inputErrorClass('confirm_password')"
                placeholder="Re-enter password"
                @blur="touch('confirm_password')"
              />
              <p v-if="fieldError('confirm_password')" class="mt-1 text-xs text-red-600">{{ fieldError('confirm_password') }}</p>
            </div>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-600">
            Passwords must be at least 8 characters and include an uppercase letter, a digit, and a special character.
          </div>

          <button type="submit" class="btn-primary w-full" :disabled="isSubmitting">
            <svg v-if="isSubmitting" class="mr-2 h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            {{ isSubmitting ? 'Creating municipal administrator...' : 'Create Municipal Administrator' }}
          </button>
        </form>
      </section>

      <section class="card">
        <div class="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 class="text-xl font-semibold text-gray-900">Current Municipal Administrators</h2>
            <p class="mt-1 text-sm text-gray-500">
              Review city assignments and account status for all municipal-administrator accounts.
            </p>
          </div>

          <div class="flex flex-col gap-3 sm:flex-row">
            <input
              v-model.trim="filters.city_name"
              class="form-input w-full sm:w-52"
              placeholder="Filter by city"
              @input="handleFilterChange"
            />
            <select v-model="filters.is_active" class="form-input w-full sm:w-44" @change="loadMunicipalAdministrators">
              <option value="">All statuses</option>
              <option value="true">Active only</option>
              <option value="false">Inactive only</option>
            </select>
          </div>
        </div>

        <div v-if="isLoadingList" class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
          Loading municipal administrators...
        </div>

        <div v-else-if="municipalAdministrators.length === 0" class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
          No municipal administrators match the current filters.
        </div>

        <div v-else class="space-y-3">
          <article
            v-for="admin in municipalAdministrators"
            :key="admin.id"
            class="rounded-2xl border border-slate-200 bg-white p-4 transition-shadow hover:shadow-md"
          >
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <h3 class="text-base font-semibold text-slate-900">{{ admin.full_name }}</h3>
                  <span
                    class="rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide"
                    :class="admin.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-600'"
                  >
                    {{ admin.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </div>
                <p class="mt-1 text-sm text-slate-500">{{ admin.email }}</p>
                <div class="mt-3 flex flex-wrap gap-2 text-xs text-slate-600">
                  <span class="rounded-full bg-slate-100 px-3 py-1">City: {{ admin.city_name || '—' }}</span>
                  <span class="rounded-full bg-slate-100 px-3 py-1">Username: {{ admin.username }}</span>
                  <span class="rounded-full bg-slate-100 px-3 py-1">Role: {{ admin.admin_level }}</span>
                </div>
              </div>

              <div class="flex flex-col items-start gap-3 lg:items-end">
                <p class="text-xs text-slate-400">
                  Created {{ formatDate(admin.created_at) }}
                </p>
                <div class="flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="btn-secondary px-4 py-2 text-sm"
                    @click="toggleEditDetails(admin)"
                  >
                    {{ editingId === admin.id ? 'Cancel' : 'Edit Details' }}
                  </button>
                  <button
                    type="button"
                    class="btn-secondary px-4 py-2 text-sm"
                    @click="toggleResetPassword(admin)"
                  >
                    {{ resettingId === admin.id ? 'Cancel' : 'Reset Password' }}
                  </button>
                  <button
                    v-if="admin.is_active"
                    type="button"
                    class="btn-danger px-4 py-2 text-sm"
                    :disabled="deactivatingIds.has(admin.id)"
                    @click="handleDeactivate(admin)"
                  >
                    <svg v-if="deactivatingIds.has(admin.id)" class="mr-2 h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    {{ deactivatingIds.has(admin.id) ? 'Deactivating...' : 'Deactivate' }}
                  </button>
                </div>
              </div>
            </div>

            <form
              v-if="editingId === admin.id"
              class="mt-4 grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-2"
              @submit.prevent="handleSaveDetails(admin)"
            >
              <div>
                <label class="form-label" :for="`edit-first-${admin.id}`">First Name</label>
                <input
                  :id="`edit-first-${admin.id}`"
                  v-model.trim="detailsForm.first_name"
                  class="form-input"
                  :class="detailsInputErrorClass('first_name')"
                  @blur="detailsTouch('first_name')"
                />
                <p v-if="detailsFieldError('first_name')" class="mt-1 text-xs text-red-600">{{ detailsFieldError('first_name') }}</p>
              </div>
              <div>
                <label class="form-label" :for="`edit-last-${admin.id}`">Last Name</label>
                <input
                  :id="`edit-last-${admin.id}`"
                  v-model.trim="detailsForm.last_name"
                  class="form-input"
                  :class="detailsInputErrorClass('last_name')"
                  @blur="detailsTouch('last_name')"
                />
                <p v-if="detailsFieldError('last_name')" class="mt-1 text-xs text-red-600">{{ detailsFieldError('last_name') }}</p>
              </div>
              <div>
                <label class="form-label" :for="`edit-email-${admin.id}`">Email</label>
                <input
                  :id="`edit-email-${admin.id}`"
                  v-model.trim="detailsForm.email"
                  type="email"
                  class="form-input"
                  :class="detailsInputErrorClass('email')"
                  @blur="detailsTouch('email')"
                />
                <p v-if="detailsFieldError('email')" class="mt-1 text-xs text-red-600">{{ detailsFieldError('email') }}</p>
              </div>
              <div>
                <label class="form-label" :for="`edit-phone-${admin.id}`">Phone</label>
                <input
                  :id="`edit-phone-${admin.id}`"
                  v-model.trim="detailsForm.phone"
                  class="form-input"
                  :class="detailsInputErrorClass('phone')"
                  @blur="detailsTouch('phone')"
                />
                <p v-if="detailsFieldError('phone')" class="mt-1 text-xs text-red-600">{{ detailsFieldError('phone') }}</p>
              </div>
              <div class="sm:col-span-2 flex justify-end gap-2">
                <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="editingId = null">Cancel</button>
                <button type="submit" class="btn-primary px-4 py-2 text-sm" :disabled="isSavingDetails">
                  {{ isSavingDetails ? 'Saving...' : 'Save details' }}
                </button>
              </div>
            </form>

            <form
              v-if="resettingId === admin.id"
              class="mt-4 grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-2"
              @submit.prevent="handleResetPassword(admin)"
            >
              <div>
                <label class="form-label" :for="`reset-password-${admin.id}`">New Password</label>
                <input
                  :id="`reset-password-${admin.id}`"
                  v-model="passwordResetForm.password"
                  type="password"
                  class="form-input"
                  :class="resetInputErrorClass('password')"
                  placeholder="NewSecret@123"
                  @blur="resetTouch('password')"
                />
                <p v-if="resetFieldError('password')" class="mt-1 text-xs text-red-600">{{ resetFieldError('password') }}</p>
              </div>
              <div>
                <label class="form-label" :for="`reset-confirm-${admin.id}`">Confirm New Password</label>
                <input
                  :id="`reset-confirm-${admin.id}`"
                  v-model="passwordResetForm.confirm_password"
                  type="password"
                  class="form-input"
                  :class="resetInputErrorClass('confirm_password')"
                  placeholder="Re-enter new password"
                  @blur="resetTouch('confirm_password')"
                />
                <p v-if="resetFieldError('confirm_password')" class="mt-1 text-xs text-red-600">{{ resetFieldError('confirm_password') }}</p>
              </div>
              <div class="sm:col-span-2 flex justify-end gap-2">
                <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="cancelResetPassword">Cancel</button>
                <button type="submit" class="btn-primary px-4 py-2 text-sm" :disabled="isResettingPassword">
                  {{ isResettingPassword ? 'Saving...' : 'Save new password' }}
                </button>
              </div>
            </form>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

import adminService from '@/services/admin.service'
import { validateIndianMobile } from '@/utils/validation'

const form = reactive({
  first_name: '',
  last_name: '',
  username: '',
  email: '',
  phone: '',
  password: '',
  confirm_password: '',
  pincode: '',
  city_id: '',
})

const touched = reactive({})
const filters = reactive({
  city_name: '',
  is_active: '',
})

const cityInventory = ref([])
const cityOptions = ref([])
const municipalAdministrators = ref([])
const successMessage = ref('')
const serverError = ref('')
const lookupMessage = ref('')
const pincodeSuggestions = ref([])
const showPincodeSuggestions = ref(false)
const isPincodeSuggesting = ref(false)
const isSubmitting = ref(false)
const isLoadingList = ref(false)
const deactivatingIds = reactive(new Set())
const editingId = ref(null)
const detailsForm = reactive({ first_name: '', last_name: '', email: '', phone: '' })
const detailsTouched = reactive({})
const isSavingDetails = ref(false)
const resettingId = ref(null)
const passwordResetForm = reactive({ password: '', confirm_password: '' })
const resetTouched = reactive({})
const isResettingPassword = ref(false)
let filterDebounce = null
let pincodeSuggestDebounce = null

function detailsTouch(field) {
  detailsTouched[field] = true
}

function detailsFieldError(field) {
  if (!detailsTouched[field]) return null
  const value = detailsForm[field]
  switch (field) {
    case 'first_name':
    case 'last_name':
      if (!value?.trim()) return 'This field is required.'
      if (value.trim().length > 80) return 'Must be 80 characters or fewer.'
      return null
    case 'email':
      if (!value) return 'Email is required.'
      if (!EMAIL_RE.test(value)) return 'Enter a valid email address.'
      return null
    case 'phone':
      return validateIndianMobile(value)
    default:
      return null
  }
}

function detailsInputErrorClass(field) {
  return detailsFieldError(field) ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''
}

function resetTouch(field) {
  resetTouched[field] = true
}

function resetFieldError(field) {
  if (!resetTouched[field]) return null
  const value = passwordResetForm[field]
  switch (field) {
    case 'password':
      if (!value) return 'Password is required.'
      if (value.length < 8) return 'Password must be at least 8 characters.'
      if (!/[A-Z]/.test(value)) return 'Password must include an uppercase letter.'
      if (!/\d/.test(value)) return 'Password must include a digit.'
      if (!/[!@#$%^&*(),.?":{}|<>\-_]/.test(value)) return 'Password must include a special character.'
      return null
    case 'confirm_password':
      if (!value) return 'Confirm password is required.'
      if (value !== passwordResetForm.password) return 'Confirm password must match the new password.'
      return null
    default:
      return null
  }
}

function resetInputErrorClass(field) {
  return resetFieldError(field) ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''
}

const adminStats = computed(() => {
  const total = municipalAdministrators.value.length
  const active = municipalAdministrators.value.filter((admin) => admin.is_active).length
  return {
    total,
    active,
    inactive: total - active,
  }
})

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function touch(field) {
  touched[field] = true
}

function fieldError(field) {
  if (!touched[field]) {
    return null
  }
  return validateField(field)
}

function inputErrorClass(field) {
  return fieldError(field) ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''
}

function validateField(field) {
  const value = form[field]

  switch (field) {
    case 'first_name':
    case 'last_name':
      if (!value?.trim()) return 'This field is required.'
      if (value.trim().length > 80) return 'Must be 80 characters or fewer.'
      return null
    case 'username':
      if (!value) return 'Username is required.'
      if (value.length < 3) return 'Username must be at least 3 characters.'
      if (value.length > 80) return 'Username must be 80 characters or fewer.'
      return null
    case 'email':
      if (!value) return 'Email is required.'
      if (!EMAIL_RE.test(value)) return 'Enter a valid email address.'
      return null
    case 'phone':
      return validateIndianMobile(value)
    case 'pincode':
      if (!value) return 'Pincode is required.'
      if (!/^\d{6}$/.test(value)) return 'Pincode must be exactly 6 digits.'
      return null
    case 'city_id':
      if (!form.city_id) return 'Please select a city for this pincode.'
      return null
    case 'password':
      if (!value) return 'Password is required.'
      if (value.length < 8) return 'Password must be at least 8 characters.'
      if (!/[A-Z]/.test(value)) return 'Password must include an uppercase letter.'
      if (!/\d/.test(value)) return 'Password must include a digit.'
      if (!/[!@#$%^&*(),.?":{}|<>\-_]/.test(value)) return 'Password must include a special character.'
      return null
    case 'confirm_password':
      if (!value) return 'Confirm password is required.'
      if (value !== form.password) return 'Confirm password must match password.'
      return null
    default:
      return null
  }
}

function validateForm() {
  const fields = [
    'first_name',
    'last_name',
    'username',
    'email',
    'phone',
    'pincode',
    'city_id',
    'password',
    'confirm_password',
  ]

  let valid = true
  for (const field of fields) {
    touched[field] = true
    if (validateField(field)) {
      valid = false
    }
  }
  return valid
}

async function loadCities() {
  const response = await adminService.getCities()
  cityInventory.value = response?.data?.cities || []
}

async function handlePincodeBlur() {
  normalizePincode()
  touch('pincode')
  touch('city_id')
  lookupMessage.value = ''
  window.setTimeout(() => {
    showPincodeSuggestions.value = false
  }, 120)

  if (validateField('pincode')) {
    cityOptions.value = []
    form.city_id = ''
    return
  }

  try {
    const response = await adminService.lookupPincode(form.pincode)
    const matches = response?.data?.cities || []
    cityOptions.value = matches

    if (matches.length === 0) {
      form.city_id = ''
      lookupMessage.value = 'No city mapping found for this pincode.'
      return
    }

    if (matches.length === 1) {
      form.city_id = matches[0].city_id
      lookupMessage.value = `City resolved: ${matches[0].city_name}`
      return
    }

    if (!matches.some((city) => city.city_id === Number(form.city_id))) {
      form.city_id = ''
    }
    lookupMessage.value = 'Multiple city options found. Please select one.'
  } catch (error) {
    cityOptions.value = []
    form.city_id = ''
    lookupMessage.value = error?.response?.data?.message || 'Could not resolve pincode right now.'
  }
}

function normalizePincode() {
  form.pincode = (form.pincode || '').replace(/\D/g, '').slice(0, 6)
}

function handlePincodeInput() {
  normalizePincode()
  lookupMessage.value = ''

  if (form.pincode.length < 6) {
    cityOptions.value = []
    form.city_id = ''
  }

  if (form.pincode.length < 2) {
    pincodeSuggestions.value = []
    showPincodeSuggestions.value = false
    window.clearTimeout(pincodeSuggestDebounce)
    return
  }

  window.clearTimeout(pincodeSuggestDebounce)
  pincodeSuggestDebounce = window.setTimeout(() => {
    fetchPincodeSuggestions(form.pincode)
  }, 180)
}

function handlePincodeFocus() {
  if (form.pincode.length >= 2 && pincodeSuggestions.value.length) {
    showPincodeSuggestions.value = true
  }
}

async function fetchPincodeSuggestions(prefix) {
  isPincodeSuggesting.value = true
  try {
    const response = await adminService.searchPincodes(prefix, 8)
    if (prefix !== form.pincode) return
    pincodeSuggestions.value = response?.data?.items || []
    showPincodeSuggestions.value = pincodeSuggestions.value.length > 0
  } catch {
    pincodeSuggestions.value = []
    showPincodeSuggestions.value = false
  } finally {
    isPincodeSuggesting.value = false
  }
}

async function applyPincodeSuggestion(suggestion) {
  form.pincode = suggestion.pincode
  showPincodeSuggestions.value = false
  pincodeSuggestions.value = []
  await handlePincodeBlur()
}

async function loadMunicipalAdministrators() {
  isLoadingList.value = true
  try {
    const params = {}
    if (filters.city_name) params.city_name = filters.city_name
    if (filters.is_active !== '') params.is_active = filters.is_active

    const response = await adminService.getMunicipalAdministrators(params)
    municipalAdministrators.value = response?.data?.items || []
  } finally {
    isLoadingList.value = false
  }
}

function handleFilterChange() {
  window.clearTimeout(filterDebounce)
  filterDebounce = window.setTimeout(() => {
    loadMunicipalAdministrators()
  }, 250)
}

function resetForm() {
  Object.assign(form, {
    first_name: '',
    last_name: '',
    username: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
    pincode: '',
    city_id: '',
  })
  cityOptions.value = []
  pincodeSuggestions.value = []
  showPincodeSuggestions.value = false
  lookupMessage.value = ''
  for (const key of Object.keys(touched)) {
    touched[key] = false
  }
}

async function handleCreate() {
  successMessage.value = ''
  serverError.value = ''

  if (!validateForm()) {
    return
  }

  isSubmitting.value = true
  try {
    const response = await adminService.createMunicipalAdministrator({
      ...form,
      email: form.email.trim().toLowerCase(),
      city_id: Number(form.city_id),
    })
    const createdUser = response?.data?.user
    successMessage.value = createdUser
      ? `${createdUser.full_name} was registered for ${createdUser.city_name}.`
      : 'Municipal administrator created successfully.'
    resetForm()
    await Promise.all([loadCities(), loadMunicipalAdministrators()])
  } catch (error) {
    serverError.value = error?.response?.data?.message || 'Unable to create municipal administrator.'
  } finally {
    isSubmitting.value = false
  }
}

async function handleDeactivate(admin) {
  const confirmed = window.confirm(`Deactivate ${admin.full_name}?`)
  if (!confirmed) {
    return
  }

  serverError.value = ''
  successMessage.value = ''
  deactivatingIds.add(admin.id)
  try {
    await adminService.deactivateMunicipalAdministrator(admin.id)
    successMessage.value = `${admin.full_name} was deactivated successfully.`
    await loadMunicipalAdministrators()
  } catch (error) {
    serverError.value = error?.response?.data?.message || 'Unable to deactivate municipal administrator.'
  } finally {
    deactivatingIds.delete(admin.id)
  }
}

function toggleEditDetails(admin) {
  serverError.value = ''
  resettingId.value = null
  if (editingId.value === admin.id) {
    editingId.value = null
    return
  }
  editingId.value = admin.id
  Object.assign(detailsForm, {
    first_name: admin.first_name,
    last_name: admin.last_name,
    email: admin.email,
    phone: admin.phone || '',
  })
}

async function handleSaveDetails(admin) {
  const fields = ['first_name', 'last_name', 'email', 'phone']
  Object.keys(detailsTouched).forEach((key) => delete detailsTouched[key])
  fields.forEach((field) => {
    detailsTouched[field] = true
  })

  const hasErrors = fields.some((field) => detailsFieldError(field))
  if (hasErrors) {
    return
  }

  isSavingDetails.value = true
  serverError.value = ''
  try {
    await adminService.updateMunicipalAdministrator(admin.id, { ...detailsForm })
    successMessage.value = `${admin.full_name}'s details were updated.`
    editingId.value = null
    await loadMunicipalAdministrators()
  } catch (error) {
    serverError.value = error?.response?.data?.message || 'Unable to update municipal administrator details.'
  } finally {
    isSavingDetails.value = false
  }
}

function toggleResetPassword(admin) {
  serverError.value = ''
  editingId.value = null
  if (resettingId.value === admin.id) {
    resettingId.value = null
    return
  }
  resettingId.value = admin.id
  passwordResetForm.password = ''
  passwordResetForm.confirm_password = ''
}

function cancelResetPassword() {
  resettingId.value = null
}

async function handleResetPassword(admin) {
  serverError.value = ''
  resetTouched.password = true
  resetTouched.confirm_password = true

  if (resetFieldError('password') || resetFieldError('confirm_password')) {
    return
  }

  isResettingPassword.value = true
  try {
    await adminService.updateMunicipalAdministrator(admin.id, {
      password: passwordResetForm.password,
      confirm_password: passwordResetForm.confirm_password,
    })
    successMessage.value = `${admin.full_name}'s password was reset.`
    resettingId.value = null
  } catch (error) {
    serverError.value = error?.response?.data?.message || 'Unable to reset password.'
  } finally {
    isResettingPassword.value = false
  }
}

function formatDate(value) {
  if (!value) {
    return '—'
  }
  return new Date(value).toLocaleDateString()
}

onMounted(async () => {
  await Promise.all([loadCities(), loadMunicipalAdministrators()])
})

onBeforeUnmount(() => {
  window.clearTimeout(filterDebounce)
  window.clearTimeout(pincodeSuggestDebounce)
})
</script>
