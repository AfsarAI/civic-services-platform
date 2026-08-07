<template>
  <div class="space-y-6">
    <section class="card overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-primary-900 text-white">
      <div class="max-w-2xl">
        <p class="mb-3 inline-flex rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-200">
          {{ authStore.isMunicipalAdmin ? `${authStore.cityName || 'Your City'} Administration` : 'System Administration' }}
        </p>
        <h1 class="text-3xl font-bold tracking-tight">Manage Citizens</h1>
        <p class="mt-3 text-sm text-slate-200/85">
          Look up citizen accounts, update their details, and reset a password if a citizen has forgotten theirs.
        </p>
      </div>
    </section>

    <section class="card">
      <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 class="text-xl font-semibold text-gray-900">Citizens</h2>
          <p class="mt-1 text-sm text-gray-500">{{ pagination.total }} registered citizen account(s).</p>
        </div>
        <select v-model="statusFilter" class="form-input w-full sm:w-44 text-sm" @change="loadCitizens(1)">
          <option value="">All statuses</option>
          <option value="true">Active only</option>
          <option value="false">Inactive only</option>
        </select>
      </div>

      <div v-if="successMessage" class="mb-5 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800" role="status">
        {{ successMessage }}
      </div>
      <div v-if="serverError" class="mb-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
        {{ serverError }}
      </div>

      <div v-if="isLoadingList" class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
        Loading citizens...
      </div>
      <div v-else-if="citizens.length === 0" class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
        No citizens match the current filter.
      </div>

      <div v-else class="space-y-3">
        <article v-for="citizen in citizens" :key="citizen.id" class="rounded-2xl border border-slate-200 bg-white p-4">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="text-base font-semibold text-slate-900">{{ citizen.full_name }}</h3>
                <span
                  class="rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide"
                  :class="citizen.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-600'"
                >
                  {{ citizen.is_active ? 'Active' : 'Inactive' }}
                </span>
              </div>
              <p class="mt-1 text-sm text-slate-500">{{ citizen.email }}</p>
              <div class="mt-2 flex flex-wrap gap-2 text-xs text-slate-600">
                <span class="rounded-full bg-slate-100 px-3 py-1">Username: {{ citizen.username }}</span>
                <span class="rounded-full bg-slate-100 px-3 py-1">City: {{ citizen.city_name || '—' }}</span>
              </div>
            </div>

            <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="toggleEditDetails(citizen)">
              {{ editingId === citizen.id ? 'Cancel' : 'Edit Details' }}
            </button>
            <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="toggleResetPassword(citizen)">
              {{ resettingId === citizen.id ? 'Cancel' : 'Reset Password' }}
            </button>
          </div>

          <form
            v-if="editingId === citizen.id"
            class="mt-4 grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-2"
            @submit.prevent="handleSaveDetails(citizen)"
          >
            <div>
              <label class="form-label" :for="`edit-first-${citizen.id}`">First Name</label>
              <input :id="`edit-first-${citizen.id}`" v-model.trim="detailsForm.first_name" class="form-input" />
            </div>
            <div>
              <label class="form-label" :for="`edit-last-${citizen.id}`">Last Name</label>
              <input :id="`edit-last-${citizen.id}`" v-model.trim="detailsForm.last_name" class="form-input" />
            </div>
            <div>
              <label class="form-label" :for="`edit-email-${citizen.id}`">Email</label>
              <input :id="`edit-email-${citizen.id}`" v-model.trim="detailsForm.email" type="email" class="form-input" />
            </div>
            <div>
              <label class="form-label" :for="`edit-phone-${citizen.id}`">Phone</label>
              <input :id="`edit-phone-${citizen.id}`" v-model.trim="detailsForm.phone" class="form-input" />
            </div>
            <div class="sm:col-span-2 flex justify-end gap-2">
              <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="editingId = null">Cancel</button>
              <button type="submit" class="btn-primary px-4 py-2 text-sm" :disabled="isSavingDetails">
                {{ isSavingDetails ? 'Saving...' : 'Save details' }}
              </button>
            </div>
          </form>

          <form
            v-if="resettingId === citizen.id"
            class="mt-4 grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-2"
            @submit.prevent="handleResetPassword(citizen)"
          >
            <div>
              <label class="form-label" :for="`reset-password-${citizen.id}`">New Password</label>
              <input
                :id="`reset-password-${citizen.id}`"
                v-model="passwordResetForm.password"
                type="password"
                class="form-input"
                placeholder="NewSecret@123"
              />
            </div>
            <div>
              <label class="form-label" :for="`reset-confirm-${citizen.id}`">Confirm New Password</label>
              <input
                :id="`reset-confirm-${citizen.id}`"
                v-model="passwordResetForm.confirm_password"
                type="password"
                class="form-input"
                placeholder="Re-enter new password"
              />
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

      <div v-if="!isLoadingList && pagination.pages > 1" class="flex items-center justify-between pt-4 text-xs text-slate-500">
        <span>Page {{ pagination.page }} of {{ pagination.pages }} · {{ pagination.total }} total</span>
        <div class="flex gap-2">
          <button class="btn-secondary px-3 py-1.5 text-xs" :disabled="pagination.page <= 1" @click="loadCitizens(pagination.page - 1)">
            Previous
          </button>
          <button class="btn-secondary px-3 py-1.5 text-xs" :disabled="pagination.page >= pagination.pages" @click="loadCitizens(pagination.page + 1)">
            Next
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { useAuthStore } from '@/stores/auth'
import adminService from '@/services/admin.service'

const authStore = useAuthStore()

const citizens = ref([])
const statusFilter = ref('')
const isLoadingList = ref(false)
const successMessage = ref('')
const serverError = ref('')
const pagination = ref({ page: 1, per_page: 20, total: 0, pages: 0 })

const editingId = ref(null)
const detailsForm = reactive({ first_name: '', last_name: '', email: '', phone: '' })
const isSavingDetails = ref(false)

const resettingId = ref(null)
const passwordResetForm = reactive({ password: '', confirm_password: '' })
const isResettingPassword = ref(false)

async function loadCitizens(page = 1) {
  isLoadingList.value = true
  serverError.value = ''
  try {
    const params = { page, per_page: pagination.value.per_page, role: 'citizen' }
    if (statusFilter.value !== '') params.is_active = statusFilter.value
    const response = await adminService.getUsers(params)
    citizens.value = response?.data?.items || []
    pagination.value = response?.data?.pagination || pagination.value
  } catch (err) {
    serverError.value = err?.response?.data?.message || 'Could not load citizens.'
  } finally {
    isLoadingList.value = false
  }
}

function toggleEditDetails(citizen) {
  serverError.value = ''
  resettingId.value = null
  if (editingId.value === citizen.id) {
    editingId.value = null
    return
  }
  editingId.value = citizen.id
  Object.assign(detailsForm, {
    first_name: citizen.first_name,
    last_name: citizen.last_name,
    email: citizen.email,
    phone: citizen.phone || '',
  })
}

async function handleSaveDetails(citizen) {
  isSavingDetails.value = true
  serverError.value = ''
  try {
    await adminService.updateUser(citizen.id, { ...detailsForm })
    successMessage.value = `${citizen.full_name}'s details were updated.`
    editingId.value = null
    await loadCitizens(pagination.value.page || 1)
  } catch (err) {
    serverError.value = err?.response?.data?.message || 'Unable to update citizen details.'
  } finally {
    isSavingDetails.value = false
  }
}

function toggleResetPassword(citizen) {
  serverError.value = ''
  editingId.value = null
  if (resettingId.value === citizen.id) {
    resettingId.value = null
    return
  }
  resettingId.value = citizen.id
  passwordResetForm.password = ''
  passwordResetForm.confirm_password = ''
}

async function handleResetPassword(citizen) {
  serverError.value = ''
  if (passwordResetForm.password !== passwordResetForm.confirm_password) {
    serverError.value = 'Confirm password must match the new password.'
    return
  }

  isResettingPassword.value = true
  try {
    await adminService.updateUser(citizen.id, {
      password: passwordResetForm.password,
      confirm_password: passwordResetForm.confirm_password,
    })
    successMessage.value = `${citizen.full_name}'s password was reset.`
    resettingId.value = null
  } catch (err) {
    serverError.value = err?.response?.data?.message || 'Unable to reset password.'
  } finally {
    isResettingPassword.value = false
  }
}

onMounted(() => {
  loadCitizens(1)
})
</script>
