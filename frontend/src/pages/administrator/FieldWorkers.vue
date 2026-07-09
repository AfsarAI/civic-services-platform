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
              <input id="first_name" v-model.trim="form.first_name" class="form-input" placeholder="Suresh" />
            </div>
            <div>
              <label class="form-label" for="last_name">Last Name</label>
              <input id="last_name" v-model.trim="form.last_name" class="form-input" placeholder="Yadav" />
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="form-label" for="username">Username</label>
              <input id="username" v-model.trim="form.username" class="form-input" placeholder="suresh_worker" />
            </div>
            <div>
              <label class="form-label" for="email">Email</label>
              <input id="email" v-model.trim="form.email" type="email" class="form-input" placeholder="suresh.worker@example.com" />
            </div>
          </div>

          <div>
            <label class="form-label" for="phone">Phone Number (optional)</label>
            <input id="phone" v-model.trim="form.phone" type="tel" class="form-input" placeholder="+91-9876543210" />
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="form-label" for="password">Password</label>
              <input id="password" v-model="form.password" type="password" class="form-input" placeholder="Worker@123" />
            </div>
            <div>
              <label class="form-label" for="confirm_password">Confirm Password</label>
              <input id="confirm_password" v-model="form.confirm_password" type="password" class="form-input" placeholder="Re-enter password" />
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
                <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="startEdit(worker)">
                  Edit
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

            <form v-if="editingId === worker.id" class="mt-4 grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-3" @submit.prevent="handleSaveEdit(worker)">
              <div>
                <label class="form-label" :for="`edit-first-${worker.id}`">First Name</label>
                <input :id="`edit-first-${worker.id}`" v-model.trim="editForm.first_name" class="form-input" />
              </div>
              <div>
                <label class="form-label" :for="`edit-last-${worker.id}`">Last Name</label>
                <input :id="`edit-last-${worker.id}`" v-model.trim="editForm.last_name" class="form-input" />
              </div>
              <div>
                <label class="form-label" :for="`edit-phone-${worker.id}`">Phone</label>
                <input :id="`edit-phone-${worker.id}`" v-model.trim="editForm.phone" class="form-input" />
              </div>
              <div class="sm:col-span-3 flex justify-end gap-2">
                <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="cancelEdit">Cancel</button>
                <button type="submit" class="btn-primary px-4 py-2 text-sm" :disabled="isSavingEdit">
                  {{ isSavingEdit ? 'Saving...' : 'Save changes' }}
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

const editingId = ref(null)
const editForm = reactive({ first_name: '', last_name: '', phone: '' })
const isSavingEdit = ref(false)
const togglingIds = reactive(new Set())

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

function startEdit(worker) {
  editingId.value = worker.id
  Object.assign(editForm, {
    first_name: worker.first_name,
    last_name: worker.last_name,
    phone: worker.phone || '',
  })
}

function cancelEdit() {
  editingId.value = null
}

async function handleSaveEdit(worker) {
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
