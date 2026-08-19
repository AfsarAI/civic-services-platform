<template>
  <div class="space-y-6">
    <section class="card overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-primary-900 text-white">
      <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div class="max-w-2xl">
          <p class="mb-3 inline-flex rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-200">
            {{ authStore.cityName || 'Your City' }} Administration
          </p>
          <h1 class="text-3xl font-bold tracking-tight">Manage Field Workers</h1>
          <p class="mt-3 text-sm text-slate-200/85">
            Add, edit, and activate or deactivate the field workers who repair complaints in {{ authStore.cityName || 'your city' }}.
          </p>
        </div>

        <div class="grid grid-cols-3 gap-3">
          <div class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur-sm">
            <p class="text-xs uppercase tracking-wide text-slate-300">Total</p>
            <p class="mt-2 text-2xl font-semibold">{{ stats.total }}</p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur-sm">
            <p class="text-xs uppercase tracking-wide text-slate-300">Active</p>
            <p class="mt-2 text-2xl font-semibold">{{ stats.active }}</p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur-sm">
            <p class="text-xs uppercase tracking-wide text-slate-300">Inactive</p>
            <p class="mt-2 text-2xl font-semibold">{{ stats.inactive }}</p>
          </div>
        </div>
      </div>
    </section>

    <div class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
      <section class="card">
        <div class="mb-6">
          <h2 class="text-xl font-semibold text-gray-900">Add Field Worker</h2>
          <p class="mt-1 text-sm text-gray-500">
            New accounts are automatically scoped to {{ authStore.cityName || 'your city' }} — no city selection needed.
          </p>
        </div>

        <div v-if="successMessage" class="mb-5 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800" role="status">
          {{ successMessage }}
        </div>
        <div v-if="serverError" class="mb-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
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
                :class="createInputErrorClass('first_name')"
                placeholder="Suresh"
                @blur="touchField(createTouched, 'first_name')"
              />
              <p v-if="createFieldError('first_name')" class="mt-1 text-xs text-red-600">{{ createFieldError('first_name') }}</p>
            </div>
            <div>
              <label class="form-label" for="last_name">Last Name</label>
              <input
                id="last_name"
                v-model.trim="form.last_name"
                class="form-input"
                :class="createInputErrorClass('last_name')"
                placeholder="Yadav"
                @blur="touchField(createTouched, 'last_name')"
              />
              <p v-if="createFieldError('last_name')" class="mt-1 text-xs text-red-600">{{ createFieldError('last_name') }}</p>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="form-label" for="username">Username</label>
              <input
                id="username"
                v-model.trim="form.username"
                class="form-input"
                :class="createInputErrorClass('username')"
                placeholder="suresh_worker"
                @blur="touchField(createTouched, 'username')"
              />
              <p v-if="createFieldError('username')" class="mt-1 text-xs text-red-600">{{ createFieldError('username') }}</p>
            </div>
            <div>
              <label class="form-label" for="email">Email</label>
              <input
                id="email"
                v-model.trim="form.email"
                type="email"
                class="form-input"
                :class="createInputErrorClass('email')"
                placeholder="suresh.worker@example.com"
                @blur="touchField(createTouched, 'email')"
              />
              <p v-if="createFieldError('email')" class="mt-1 text-xs text-red-600">{{ createFieldError('email') }}</p>
            </div>
          </div>

          <div>
            <label class="form-label" for="phone">Phone Number (optional)</label>
            <input
              id="phone"
              v-model.trim="form.phone"
              type="tel"
              class="form-input"
              :class="createInputErrorClass('phone')"
              placeholder="9876543210"
              @blur="touchField(createTouched, 'phone')"
            />
            <p v-if="createFieldError('phone')" class="mt-1 text-xs text-red-600">{{ createFieldError('phone') }}</p>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="form-label" for="password">Password</label>
              <input
                id="password"
                v-model="form.password"
                type="password"
                class="form-input"
                :class="createInputErrorClass('password')"
                placeholder="Worker@123"
                @blur="touchField(createTouched, 'password')"
              />
              <p v-if="createFieldError('password')" class="mt-1 text-xs text-red-600">{{ createFieldError('password') }}</p>
            </div>
            <div>
              <label class="form-label" for="confirm_password">Confirm Password</label>
              <input
                id="confirm_password"
                v-model="form.confirm_password"
                type="password"
                class="form-input"
                :class="createInputErrorClass('confirm_password')"
                placeholder="Re-enter password"
                @blur="touchField(createTouched, 'confirm_password')"
              />
              <p v-if="createFieldError('confirm_password')" class="mt-1 text-xs text-red-600">{{ createFieldError('confirm_password') }}</p>
            </div>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-600">
            Passwords must be at least 8 characters and include an uppercase letter, a digit, and a special character.
          </div>

          <button type="submit" class="btn-primary w-full" :disabled="isSubmitting">
            {{ isSubmitting ? 'Creating field worker...' : 'Create Field Worker' }}
          </button>
        </form>
      </section>

      <section class="card">
        <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 class="text-xl font-semibold text-gray-900">Field Workers</h2>
            <p class="mt-1 text-sm text-gray-500">Workers assigned to {{ authStore.cityName || 'your city' }}.</p>
          </div>
          <select v-model="statusFilter" class="form-input w-full sm:w-44 text-sm" @change="loadFieldWorkers">
            <option value="">All statuses</option>
            <option value="true">Active only</option>
            <option value="false">Inactive only</option>
          </select>
        </div>

        <div v-if="isLoadingList" class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
          Loading field workers...
        </div>
        <div v-else-if="fieldWorkers.length === 0" class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
          No field workers match the current filter.
        </div>

        <div v-else class="space-y-3">
          <article v-for="worker in fieldWorkers" :key="worker.id" class="rounded-2xl border border-slate-200 bg-white p-4">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <h3 class="text-base font-semibold text-slate-900">{{ worker.full_name }}</h3>
                  <span
                    class="rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide"
                    :class="worker.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-600'"
                  >
                    {{ worker.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </div>
                <p class="mt-1 text-sm text-slate-500">{{ worker.email }}</p>
                <p class="mt-1 text-xs text-slate-400">{{ worker.phone || 'No phone on file' }}</p>
              </div>

              <div class="flex flex-wrap items-center gap-2">
                <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="toggleEditDetails(worker)">
                  {{ editingId === worker.id ? 'Cancel' : 'Edit Details' }}
                </button>
                <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="toggleResetPassword(worker)">
                  {{ resettingId === worker.id ? 'Cancel' : 'Reset Password' }}
                </button>
                <button
                  type="button"
                  class="px-4 py-2 text-sm"
                  :class="worker.is_active ? 'btn-danger' : 'btn-primary'"
                  :disabled="togglingIds.has(worker.id)"
                  @click="handleToggleActive(worker)"
                >
                  {{ togglingIds.has(worker.id) ? 'Saving...' : (worker.is_active ? 'Deactivate' : 'Activate') }}
                </button>
              </div>
            </div>

            <form v-if="editingId === worker.id" class="mt-4 grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-2" @submit.prevent="handleSaveEdit(worker)">
              <div>
                <label class="form-label" :for="`edit-first-${worker.id}`">First Name</label>
                <input
                  :id="`edit-first-${worker.id}`"
                  v-model.trim="editForm.first_name"
                  class="form-input"
                  :class="editInputErrorClass('first_name')"
                  @blur="touchField(editTouched, 'first_name')"
                />
                <p v-if="editFieldError('first_name')" class="mt-1 text-xs text-red-600">{{ editFieldError('first_name') }}</p>
              </div>
              <div>
                <label class="form-label" :for="`edit-last-${worker.id}`">Last Name</label>
                <input
                  :id="`edit-last-${worker.id}`"
                  v-model.trim="editForm.last_name"
                  class="form-input"
                  :class="editInputErrorClass('last_name')"
                  @blur="touchField(editTouched, 'last_name')"
                />
                <p v-if="editFieldError('last_name')" class="mt-1 text-xs text-red-600">{{ editFieldError('last_name') }}</p>
              </div>
              <div>
                <label class="form-label" :for="`edit-email-${worker.id}`">Email</label>
                <input
                  :id="`edit-email-${worker.id}`"
                  v-model.trim="editForm.email"
                  type="email"
                  class="form-input"
                  :class="editInputErrorClass('email')"
                  @blur="touchField(editTouched, 'email')"
                />
                <p v-if="editFieldError('email')" class="mt-1 text-xs text-red-600">{{ editFieldError('email') }}</p>
              </div>
              <div>
                <label class="form-label" :for="`edit-phone-${worker.id}`">Phone</label>
                <input
                  :id="`edit-phone-${worker.id}`"
                  v-model.trim="editForm.phone"
                  class="form-input"
                  :class="editInputErrorClass('phone')"
                  @blur="touchField(editTouched, 'phone')"
                />
                <p v-if="editFieldError('phone')" class="mt-1 text-xs text-red-600">{{ editFieldError('phone') }}</p>
              </div>
              <div class="sm:col-span-2 flex justify-end gap-2">
                <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="editingId = null">Cancel</button>
                <button type="submit" class="btn-primary px-4 py-2 text-sm" :disabled="isSavingEdit">
                  {{ isSavingEdit ? 'Saving...' : 'Save details' }}
                </button>
              </div>
            </form>

            <form v-if="resettingId === worker.id" class="mt-4 grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-2" @submit.prevent="handleResetPassword(worker)">
              <div>
                <label class="form-label" :for="`reset-password-${worker.id}`">New Password</label>
                <input
                  :id="`reset-password-${worker.id}`"
                  v-model="passwordResetForm.password"
                  type="password"
                  class="form-input"
                  :class="resetInputErrorClass('password')"
                  placeholder="NewSecret@123"
                  @blur="touchField(resetTouched, 'password')"
                />
                <p v-if="resetFieldError('password')" class="mt-1 text-xs text-red-600">{{ resetFieldError('password') }}</p>
              </div>
              <div>
                <label class="form-label" :for="`reset-confirm-${worker.id}`">Confirm New Password</label>
                <input
                  :id="`reset-confirm-${worker.id}`"
                  v-model="passwordResetForm.confirm_password"
                  type="password"
                  class="form-input"
                  :class="resetInputErrorClass('confirm_password')"
                  placeholder="Re-enter new password"
                  @blur="touchField(resetTouched, 'confirm_password')"
                />
                <p v-if="resetFieldError('confirm_password')" class="mt-1 text-xs text-red-600">{{ resetFieldError('confirm_password') }}</p>
              </div>
              <div class="sm:col-span-2 flex justify-end gap-2">
                <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="resettingId = null">Cancel</button>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import adminService from '@/services/admin.service'
import { validateIndianMobile } from '@/utils/validation'

const authStore = useAuthStore()

const form = reactive({
  first_name: '',
  last_name: '',
  username: '',
  email: '',
  phone: '',
  password: '',
  confirm_password: '',
})

const fieldWorkers = ref([])
const statusFilter = ref('')
const isLoadingList = ref(true)
const isSubmitting = ref(false)
const successMessage = ref('')
const serverError = ref('')

const createTouched = reactive({})
const editTouched = reactive({})
const resetTouched = reactive({})

const editingId = ref(null)
const editForm = reactive({ first_name: '', last_name: '', email: '', phone: '' })
const isSavingEdit = ref(false)
const resettingId = ref(null)
const passwordResetForm = reactive({ password: '', confirm_password: '' })
const isResettingPassword = ref(false)
const togglingIds = reactive(new Set())

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function touchField(target, field) {
  target[field] = true
}

function validateCreateField(field) {
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

function createFieldError(field) {
  if (!createTouched[field]) return null
  return validateCreateField(field)
}

function createInputErrorClass(field) {
  return createFieldError(field) ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''
}

function validateEditField(field) {
  const value = editForm[field]
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

function editFieldError(field) {
  if (!editTouched[field]) return null
  return validateEditField(field)
}

function editInputErrorClass(field) {
  return editFieldError(field) ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''
}

function validateResetField(field) {
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

function resetFieldError(field) {
  if (!resetTouched[field]) return null
  return validateResetField(field)
}

function resetInputErrorClass(field) {
  return resetFieldError(field) ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''
}

const stats = computed(() => {
  const total = fieldWorkers.value.length
  const active = fieldWorkers.value.filter((w) => w.is_active).length
  return { total, active, inactive: total - active }
})

async function loadFieldWorkers() {
  isLoadingList.value = true
  try {
    const params = {}
    if (statusFilter.value !== '') params.is_active = statusFilter.value
    const response = await adminService.getFieldWorkers(params)
    fieldWorkers.value = response?.data?.field_workers || []
  } catch (err) {
    serverError.value = err?.response?.data?.message || 'Could not load field workers.'
  } finally {
    isLoadingList.value = false
  }
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
  })
}

async function handleCreate() {
  successMessage.value = ''
  serverError.value = ''

  Object.keys(createTouched).forEach((key) => delete createTouched[key])
  ;['first_name', 'last_name', 'username', 'email', 'phone', 'password', 'confirm_password'].forEach((field) => {
    createTouched[field] = true
  })

  const hasErrors = ['first_name', 'last_name', 'username', 'email', 'phone', 'password', 'confirm_password']
    .some((field) => createFieldError(field))

  if (hasErrors) {
    return
  }

  isSubmitting.value = true
  try {
    const response = await adminService.createFieldWorker({ ...form, email: form.email.trim().toLowerCase() })
    const createdUser = response?.data?.user
    successMessage.value = createdUser
      ? `${createdUser.full_name} was added as a field worker.`
      : 'Field worker created successfully.'
    resetForm()
    await loadFieldWorkers()
  } catch (err) {
    serverError.value = err?.response?.data?.message || 'Unable to create field worker.'
  } finally {
    isSubmitting.value = false
  }
}

function toggleEditDetails(worker) {
  serverError.value = ''
  resettingId.value = null
  if (editingId.value === worker.id) {
    editingId.value = null
    return
  }
  editingId.value = worker.id
  Object.assign(editForm, {
    first_name: worker.first_name,
    last_name: worker.last_name,
    email: worker.email,
    phone: worker.phone || '',
  })
}

async function handleSaveEdit(worker) {
  Object.keys(editTouched).forEach((key) => delete editTouched[key])
  ;['first_name', 'last_name', 'email', 'phone'].forEach((field) => {
    editTouched[field] = true
  })

  const hasErrors = ['first_name', 'last_name', 'email', 'phone'].some((field) => editFieldError(field))
  if (hasErrors) {
    return
  }

  isSavingEdit.value = true
  serverError.value = ''
  try {
    await adminService.updateFieldWorker(worker.id, { ...editForm })
    successMessage.value = `${worker.full_name}'s details were updated.`
    editingId.value = null
    await loadFieldWorkers()
  } catch (err) {
    serverError.value = err?.response?.data?.message || 'Unable to update field worker.'
  } finally {
    isSavingEdit.value = false
  }
}

function toggleResetPassword(worker) {
  serverError.value = ''
  editingId.value = null
  if (resettingId.value === worker.id) {
    resettingId.value = null
    return
  }
  resettingId.value = worker.id
  passwordResetForm.password = ''
  passwordResetForm.confirm_password = ''
}

async function handleResetPassword(worker) {
  serverError.value = ''
  resetTouched.password = true
  resetTouched.confirm_password = true

  if (resetFieldError('password') || resetFieldError('confirm_password')) {
    return
  }

  isResettingPassword.value = true
  try {
    await adminService.updateFieldWorker(worker.id, {
      password: passwordResetForm.password,
      confirm_password: passwordResetForm.confirm_password,
    })
    successMessage.value = `${worker.full_name}'s password was reset.`
    resettingId.value = null
  } catch (err) {
    serverError.value = err?.response?.data?.message || 'Unable to reset password.'
  } finally {
    isResettingPassword.value = false
  }
}

async function handleToggleActive(worker) {
  togglingIds.add(worker.id)
  serverError.value = ''
  try {
    await adminService.updateFieldWorker(worker.id, { is_active: !worker.is_active })
    successMessage.value = `${worker.full_name} was ${worker.is_active ? 'deactivated' : 'activated'}.`
    await loadFieldWorkers()
  } catch (err) {
    serverError.value = err?.response?.data?.message || 'Unable to update field worker status.'
  } finally {
    togglingIds.delete(worker.id)
  }
}

onMounted(() => {
  loadFieldWorkers()
})
</script>
