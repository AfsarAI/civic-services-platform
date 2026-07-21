<template>
  <div class="mx-auto max-w-4xl space-y-6">
    <!-- Header -->
    <section class="card overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-primary-900 text-white">
      <div class="flex flex-col gap-6 sm:flex-row sm:items-center">
        <div class="relative shrink-0">
          <div class="flex h-20 w-20 items-center justify-center overflow-hidden rounded-full border-2 border-white/20 bg-white/10 text-2xl font-bold">
            <img v-if="avatarPreviewUrl" :src="avatarPreviewUrl" alt="Profile photo" class="h-full w-full object-cover" />
            <span v-else>{{ initials }}</span>
          </div>
          <span v-if="isUploadingAvatar" class="absolute inset-0 flex items-center justify-center rounded-full bg-black/40 text-xs">
            ...
          </span>
        </div>

        <div class="min-w-0">
          <p class="mb-2 inline-flex rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-200">
            {{ roleLabel }}
          </p>
          <h1 class="truncate text-2xl font-bold tracking-tight">{{ authStore.fullName || 'My Profile' }}</h1>
          <p class="mt-1 text-sm text-slate-300">{{ authStore.user?.email }}</p>
          <p v-if="authStore.cityName" class="mt-1 text-xs text-slate-400">City: {{ authStore.cityName }}</p>
        </div>
      </div>
    </section>

    <!-- Tabs -->
    <div class="flex gap-2 border-b border-slate-200">
      <button
        type="button"
        class="px-4 py-2.5 text-sm font-semibold transition-colors"
        :class="activeTab === 'details' ? 'border-b-2 border-primary-600 text-primary-700' : 'text-slate-500 hover:text-slate-700'"
        @click="activeTab = 'details'"
      >
        Profile Details
      </button>
      <button
        type="button"
        class="px-4 py-2.5 text-sm font-semibold transition-colors"
        :class="activeTab === 'password' ? 'border-b-2 border-primary-600 text-primary-700' : 'text-slate-500 hover:text-slate-700'"
        @click="activeTab = 'password'"
      >
        Change Password
      </button>
    </div>

    <!-- Alerts -->
    <transition name="fade">
      <div v-if="successMessage" class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800" role="status">
        {{ successMessage }}
      </div>
    </transition>
    <transition name="fade">
      <div v-if="serverError" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
        {{ serverError }}
      </div>
    </transition>

    <!-- Profile Details tab -->
    <section v-if="activeTab === 'details'" class="card space-y-6">
      <div>
        <h2 class="text-lg font-semibold text-slate-900">Profile Photo</h2>
        <p class="mt-1 text-sm text-slate-500">Upload a clear photo of yourself. JPG or PNG, camera or gallery.</p>

        <input
          ref="cameraInputRef"
          type="file"
          accept="image/*"
          capture="user"
          class="hidden"
          @change="handleAvatarSelected"
        />
        <input
          ref="galleryInputRef"
          type="file"
          accept="image/*"
          class="hidden"
          @change="handleAvatarSelected"
        />

        <div class="mt-4 flex flex-wrap gap-3">
          <button type="button" class="btn-secondary px-4 py-2 text-sm" :disabled="isUploadingAvatar" @click="cameraInputRef?.click()">
            Take Photo
          </button>
          <button type="button" class="btn-secondary px-4 py-2 text-sm" :disabled="isUploadingAvatar" @click="galleryInputRef?.click()">
            Upload Photo
          </button>
        </div>
        <p v-if="avatarError" class="mt-2 text-sm text-red-600">{{ avatarError }}</p>
      </div>

      <div class="border-t border-slate-100 pt-6">
        <h2 class="text-lg font-semibold text-slate-900">Account Details</h2>
        <p class="mt-1 text-sm text-slate-500">Your username cannot be changed.</p>

        <form class="mt-4 space-y-5" @submit.prevent="handleSaveProfile">
          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="form-label" for="username">Username</label>
              <input id="username" :value="authStore.user?.username" type="text" class="form-input bg-slate-50" readonly disabled />
            </div>
            <div>
              <label class="form-label" for="email">Email</label>
              <input id="email" :value="authStore.user?.email" type="email" class="form-input bg-slate-50" readonly disabled />
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="form-label" for="first_name">First Name</label>
              <input id="first_name" v-model.trim="profileForm.first_name" type="text" class="form-input" required />
            </div>
            <div>
              <label class="form-label" for="last_name">Last Name</label>
              <input id="last_name" v-model.trim="profileForm.last_name" type="text" class="form-input" required />
            </div>
          </div>

          <div>
            <label class="form-label" for="phone">Phone Number</label>
            <input id="phone" v-model.trim="profileForm.phone" type="tel" class="form-input" placeholder="+91-9876543210" />
          </div>

          <div v-if="authStore.adminLevel" class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-600">
            Administrator level: <span class="font-semibold capitalize">{{ authStore.adminLevel }}</span>
          </div>

          <button type="submit" class="btn-primary w-full py-3" :disabled="isSavingProfile">
            {{ isSavingProfile ? 'Saving...' : 'Save Changes' }}
          </button>
        </form>
      </div>
    </section>

    <!-- Change Password tab -->
    <section v-else class="card space-y-5">
      <div>
        <h2 class="text-lg font-semibold text-slate-900">Change Password</h2>
        <p class="mt-1 text-sm text-slate-500">
          Use at least 8 characters, including an uppercase letter, a digit, and a special character.
        </p>
      </div>

      <form class="space-y-5" @submit.prevent="handleChangePassword">
        <div>
          <label class="form-label" for="current_password">Current Password</label>
          <div class="relative">
            <input
              id="current_password"
              v-model="passwordForm.current_password"
              :type="showPassword.current ? 'text' : 'password'"
              class="form-input pr-12"
              required
            />
            <button type="button" class="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-700" @click="showPassword.current = !showPassword.current">
              {{ showPassword.current ? 'Hide' : 'Show' }}
            </button>
          </div>
        </div>

        <div>
          <label class="form-label" for="new_password">New Password</label>
          <div class="relative">
            <input
              id="new_password"
              v-model="passwordForm.new_password"
              :type="showPassword.new ? 'text' : 'password'"
              class="form-input pr-12"
              required
            />
            <button type="button" class="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-700" @click="showPassword.new = !showPassword.new">
              {{ showPassword.new ? 'Hide' : 'Show' }}
            </button>
          </div>
        </div>

        <div>
          <label class="form-label" for="confirm_password">Confirm New Password</label>
          <div class="relative">
            <input
              id="confirm_password"
              v-model="passwordForm.confirm_password"
              :type="showPassword.confirm ? 'text' : 'password'"
              class="form-input pr-12"
              required
            />
            <button type="button" class="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-700" @click="showPassword.confirm = !showPassword.confirm">
              {{ showPassword.confirm ? 'Hide' : 'Show' }}
            </button>
          </div>
        </div>

        <button type="submit" class="btn-primary w-full py-3" :disabled="isSavingPassword">
          {{ isSavingPassword ? 'Updating...' : 'Update Password' }}
        </button>
      </form>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import authService from '@/services/auth.service'

const authStore = useAuthStore()

const activeTab = ref('details')
const successMessage = ref('')
const serverError = ref('')

const profileForm = reactive({
  first_name: authStore.user?.first_name || '',
  last_name: authStore.user?.last_name || '',
  phone: authStore.user?.phone || '',
})
const isSavingProfile = ref(false)

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})
const showPassword = reactive({ current: false, new: false, confirm: false })
const isSavingPassword = ref(false)

const cameraInputRef = ref(null)
const galleryInputRef = ref(null)
const isUploadingAvatar = ref(false)
const avatarError = ref('')

const roleLabel = computed(() => (authStore.userRole || '').replaceAll('_', ' ') || 'account')

const initials = computed(() => {
  const name = authStore.fullName || authStore.user?.username || ''
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('') || '?'
})

const avatarPreviewUrl = computed(() => {
  const url = authStore.user?.avatar_url
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1'
  return `${apiBase.replace(/\/api\/v1$/, '')}${url}`
})

function resetAlerts() {
  successMessage.value = ''
  serverError.value = ''
}

async function handleSaveProfile() {
  resetAlerts()
  isSavingProfile.value = true
  try {
    await authService.updateProfile({ ...profileForm })
    await authStore.fetchCurrentUser()
    successMessage.value = 'Profile updated successfully.'
  } catch (err) {
    serverError.value = err?.response?.data?.message || 'Could not update profile.'
  } finally {
    isSavingProfile.value = false
  }
}

async function handleChangePassword() {
  resetAlerts()
  isSavingPassword.value = true
  try {
    await authService.changePassword({ ...passwordForm })
    successMessage.value = 'Password updated successfully.'
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (err) {
    serverError.value = err?.response?.data?.message || 'Could not update password.'
  } finally {
    isSavingPassword.value = false
  }
}

async function handleAvatarSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return

  resetAlerts()
  avatarError.value = ''
  isUploadingAvatar.value = true
  try {
    await authService.uploadAvatar(file)
    await authStore.fetchCurrentUser()
    successMessage.value = 'Profile photo updated successfully.'
  } catch (err) {
    avatarError.value = err?.response?.data?.message || 'Could not upload profile photo.'
  } finally {
    isUploadingAvatar.value = false
    event.target.value = ''
  }
}
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

