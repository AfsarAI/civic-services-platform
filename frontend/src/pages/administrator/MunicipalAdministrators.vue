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
            <p class="mt-2 text-2xl font-semibold">{{ cityOptions.length }}</p>
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
                placeholder="+91-9876543210"
                @blur="touch('phone')"
              />
              <p v-if="fieldError('phone')" class="mt-1 text-xs text-red-600">{{ fieldError('phone') }}</p>
            </div>
            <div>
              <label class="form-label" for="city_name">City</label>
              <input
                id="city_name"
                v-model.trim="form.city_name"
                list="city-options"
                class="form-input"
                :class="inputErrorClass('city_name')"
                placeholder="Lucknow"
                @blur="touch('city_name')"
              />
              <datalist id="city-options">
                <option v-for="city in cityOptions" :key="city.id" :value="city.name">
                  {{ city.name }}
                </option>
              </datalist>
              <p v-if="fieldError('city_name')" class="mt-1 text-xs text-red-600">{{ fieldError('city_name') }}</p>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="form-label" for="city_state">State</label>
              <input
                id="city_state"
                v-model.trim="form.city_state"
                class="form-input"
                :class="inputErrorClass('city_state')"
                placeholder="Uttar Pradesh"
                @blur="touch('city_state')"
              />
              <p v-if="fieldError('city_state')" class="mt-1 text-xs text-red-600">{{ fieldError('city_state') }}</p>
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
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import adminService from '@/services/admin.service'

const form = reactive({
  first_name: '',
  last_name: '',
  username: '',
  email: '',
  phone: '',
  password: '',
  confirm_password: '',
  city_name: '',
  city_state: '',
})

const touched = reactive({})
const filters = reactive({
  city_name: '',
  is_active: '',
})

const cityOptions = ref([])
const municipalAdministrators = ref([])
const successMessage = ref('')
const serverError = ref('')
const isSubmitting = ref(false)
const isLoadingList = ref(false)
const deactivatingIds = reactive(new Set())
let filterDebounce = null

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
const PHONE_RE = /^\+?(\d[\s-]?){9,14}\d$/

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
      if (!value) return null
      if (!PHONE_RE.test(value)) return 'Enter a valid phone number.'
      return null
    case 'city_name':
      if (!value?.trim()) return 'City is required.'
      if (value.trim().length < 2) return 'City name must be at least 2 characters.'
      return null
    case 'city_state':
      if (!value) return null
      if (value.trim().length > 120) return 'State must be 120 characters or fewer.'
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
    'city_name',
    'city_state',
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
  cityOptions.value = response?.data?.cities || []
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
    city_name: '',
    city_state: '',
  })
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

function formatDate(value) {
  if (!value) {
    return '—'
  }
  return new Date(value).toLocaleDateString()
}

onMounted(async () => {
  await Promise.all([loadCities(), loadMunicipalAdministrators()])
})
</script>
