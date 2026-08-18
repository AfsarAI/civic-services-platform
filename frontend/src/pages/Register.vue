<template>
  <div class="w-full">
    <!-- Header -->
    <div class="text-center mb-6">
      <h1 class="text-2xl font-bold text-slate-900">Create your account</h1>
      <p class="text-slate-500 text-sm mt-1">Join Civic Services and report issues in your community</p>
    </div>

    <!-- Success State -->
    <transition name="fade">
      <div v-if="registered" class="text-center py-8">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
          <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
          </svg>
        </div>
        <h2 class="text-xl font-bold text-slate-900 mb-2">Account created!</h2>
        <p class="text-slate-500 text-sm mb-6">
          Welcome, <strong>{{ form.first_name }}</strong>! Your account has been registered successfully.
        </p>
        <div class="flex items-center justify-center gap-2 text-sm text-slate-400">
          <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
          </svg>
          Redirecting to sign in…
        </div>
      </div>
    </transition>

    <!-- Registration Form -->
    <form v-if="!registered" @submit.prevent="handleRegister" class="space-y-5" novalidate>

      <!-- Name Row -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label for="first_name" class="form-label">First Name <span class="text-red-500">*</span></label>
          <input
            id="first_name"
            v-model.trim="form.first_name"
            type="text"
            class="form-input"
            :class="fieldError('first_name') ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
            placeholder="Priya"
            autocomplete="given-name"
            @blur="touch('first_name')"
          />
          <p v-if="fieldError('first_name')" class="field-error">{{ fieldError('first_name') }}</p>
        </div>
        <div>
          <label for="last_name" class="form-label">Last Name <span class="text-red-500">*</span></label>
          <input
            id="last_name"
            v-model.trim="form.last_name"
            type="text"
            class="form-input"
            :class="fieldError('last_name') ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
            placeholder="Sharma"
            autocomplete="family-name"
            @blur="touch('last_name')"
          />
          <p v-if="fieldError('last_name')" class="field-error">{{ fieldError('last_name') }}</p>
        </div>
      </div>

      <!-- Username -->
      <div>
        <label for="username" class="form-label">Username <span class="text-red-500">*</span></label>
        <input
          id="username"
          v-model.trim="form.username"
          type="text"
          class="form-input"
          :class="fieldError('username') ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
          placeholder="priya_sharma"
          autocomplete="username"
          @blur="touch('username')"
        />
        <p v-if="fieldError('username')" class="field-error">{{ fieldError('username') }}</p>
      </div>

      <!-- Email -->
      <div>
        <label for="email" class="form-label">Email Address <span class="text-red-500">*</span></label>
        <input
          id="email"
          v-model.trim="form.email"
          type="email"
          class="form-input"
          :class="fieldError('email') ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
          placeholder="priya@example.com"
          autocomplete="email"
          @blur="touch('email')"
        />
        <p v-if="fieldError('email')" class="field-error">{{ fieldError('email') }}</p>
      </div>

      <!-- Mobile -->
      <div>
        <label for="phone" class="form-label">Mobile Number</label>
        <input
          id="phone"
          v-model.trim="form.phone"
          type="tel"
          class="form-input"
          :class="fieldError('phone') ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
          placeholder="9876543210"
          autocomplete="tel"
          @blur="touch('phone')"
        />
        <p v-if="fieldError('phone')" class="field-error">{{ fieldError('phone') }}</p>
        <p v-else class="mt-1 text-xs text-slate-400">Enter 10 digits starting with 6, 7, 8, or 9.</p>
      </div>

      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div class="relative">
          <label for="pincode" class="form-label">Pincode <span class="text-red-500">*</span></label>
          <input
            id="pincode"
            v-model.trim="form.pincode"
            type="text"
            maxlength="6"
            class="form-input"
            :class="fieldError('pincode') ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
            placeholder="226001"
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

          <p v-if="fieldError('pincode')" class="field-error">{{ fieldError('pincode') }}</p>
          <p v-else class="mt-1 text-xs text-slate-400">Type at least 2 digits to see pincode suggestions.</p>
        </div>

        <div>
          <label for="city_id" class="form-label">City <span class="text-red-500">*</span></label>
          <select
            id="city_id"
            v-model="form.city_id"
            class="form-input"
            :class="fieldError('city_id') ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
            @blur="touch('city_id')"
          >
            <option value="" disabled>Select city</option>
            <option v-for="city in cityOptions" :key="city.city_id" :value="city.city_id">
              {{ city.city_name }}{{ city.state ? `, ${city.state}` : '' }}
            </option>
          </select>
          <p v-if="fieldError('city_id')" class="field-error">{{ fieldError('city_id') }}</p>
          <p v-else-if="locationMessage" class="mt-1 text-xs text-slate-400">{{ locationMessage }}</p>
        </div>
      </div>

      <!-- Password -->
      <div>
        <label for="password" class="form-label">Password <span class="text-red-500">*</span></label>
        <div class="relative">
          <input
            id="password"
            v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            class="form-input pr-12"
            :class="fieldError('password') ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
            placeholder="Min 8 chars with A, 1, @"
            autocomplete="new-password"
            @blur="touch('password')"
            @input="touch('password')"
          />
          <button
            type="button"
            @click="showPassword = !showPassword"
            class="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-700 transition-colors"
            :aria-label="showPassword ? 'Hide password' : 'Show password'"
          >
            <svg v-if="!showPassword" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
            </svg>
          </button>
        </div>
        <!-- Password strength indicator -->
        <div v-if="form.password" class="mt-2 space-y-1">
          <div class="flex gap-1">
            <div
              v-for="i in 4"
              :key="i"
              class="h-1 flex-1 rounded-full transition-all duration-300"
              :class="passwordStrengthBars[i - 1]"
            ></div>
          </div>
          <p class="text-xs" :class="passwordStrengthTextClass">
            {{ passwordStrengthLabel }}
          </p>
        </div>
        <p v-if="fieldError('password')" class="field-error">{{ fieldError('password') }}</p>
      </div>

      <!-- Confirm Password -->
      <div>
        <label for="confirm_password" class="form-label">Confirm Password <span class="text-red-500">*</span></label>
        <div class="relative">
          <input
            id="confirm_password"
            v-model="form.confirm_password"
            :type="showConfirm ? 'text' : 'password'"
            class="form-input pr-12"
            :class="fieldError('confirm_password') ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
            placeholder="Re-enter your password"
            autocomplete="new-password"
            @blur="touch('confirm_password')"
          />
          <button
            type="button"
            @click="showConfirm = !showConfirm"
            class="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-700 transition-colors"
            :aria-label="showConfirm ? 'Hide password' : 'Show password'"
          >
            <svg v-if="!showConfirm" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
            </svg>
          </button>
        </div>
        <p v-if="fieldError('confirm_password')" class="field-error">{{ fieldError('confirm_password') }}</p>
      </div>

      <!-- Server Error -->
      <transition name="fade">
        <div
          v-if="serverError"
          class="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3"
          role="alert"
        >
          <svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <p class="text-red-700 text-sm">{{ serverError }}</p>
        </div>
      </transition>

      <!-- Submit -->
      <button
        type="submit"
        class="btn-primary w-full mt-2"
        :disabled="isLoading"
        id="register-submit-btn"
      >
        <svg v-if="isLoading" class="w-4 h-4 animate-spin mr-2" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
        </svg>
        {{ isLoading ? 'Creating account…' : 'Create Account' }}
      </button>

      <!-- Login Link -->
      <p class="text-center text-sm text-slate-500 pt-1">
        Already have an account?
        <RouterLink to="/login" class="font-semibold text-primary-600 hover:text-primary-700 transition-colors">
          Sign in
        </RouterLink>
      </p>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onBeforeUnmount } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import locationService from '@/services/location.service'
import { validateIndianMobile } from '@/utils/validation'

const authStore = useAuthStore()
const router = useRouter()

// ── Form state ──────────────────────────────────────────────────────────────
const form = reactive({
  first_name: '',
  last_name: '',
  username: '',
  email: '',
  phone: '',
  pincode: '',
  city_id: '',
  password: '',
  confirm_password: '',
})

const touched = reactive({})
const isLoading = ref(false)
const serverError = ref(null)
const registered = ref(false)
const showPassword = ref(false)
const showConfirm = ref(false)
const cityOptions = ref([])
const locationMessage = ref('')
const pincodeSuggestions = ref([])
const showPincodeSuggestions = ref(false)
const isPincodeSuggesting = ref(false)
let pincodeSuggestDebounce = null

// ── Touch tracking ──────────────────────────────────────────────────────────
function touch(field) {
  touched[field] = true
}

// ── Client-side validation rules ────────────────────────────────────────────
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function validateField(field) {
  const v = form[field]
  switch (field) {
    case 'first_name':
      if (!v || !v.trim()) return 'First name is required.'
      if (v.trim().length > 80) return 'First name is too long.'
      return null
    case 'last_name':
      if (!v || !v.trim()) return 'Last name is required.'
      if (v.trim().length > 80) return 'Last name is too long.'
      return null
    case 'username':
      if (!v) return 'Username is required.'
      if (v.length < 3) return 'Username must be at least 3 characters.'
      if (v.length > 80) return 'Username is too long.'
      return null
    case 'email':
      if (!v) return 'Email address is required.'
      if (!EMAIL_RE.test(v)) return 'Please enter a valid email address.'
      return null
    case 'phone':
      return validateIndianMobile(v)
    case 'password': {
      if (!v) return 'Password is required.'
      if (v.length < 8) return 'Password must be at least 8 characters.'
      if (!/[A-Z]/.test(v)) return 'Password must contain at least one uppercase letter.'
      if (!/\d/.test(v)) return 'Password must contain at least one digit.'
      if (!/[!@#$%^&*(),.?":{}|<>\-_]/.test(v)) return 'Password must contain at least one special character.'
      return null
    }
    case 'confirm_password':
      if (!v) return 'Please confirm your password.'
      if (v !== form.password) return 'Passwords do not match.'
      return null
    case 'pincode':
      if (!v) return 'Pincode is required.'
      if (!/^\d{6}$/.test(v)) return 'Pincode must be exactly 6 digits.'
      return null
    case 'city_id':
      if (!form.city_id) return 'Please select a city for this pincode.'
      return null
    default:
      return null
  }
}

function fieldError(field) {
  if (!touched[field]) return null
  return validateField(field)
}

// ── Password strength ───────────────────────────────────────────────────────
const passwordStrength = computed(() => {
  const p = form.password
  if (!p) return 0
  let score = 0
  if (p.length >= 8) score++
  if (/[A-Z]/.test(p)) score++
  if (/\d/.test(p)) score++
  if (/[!@#$%^&*(),.?":{}|<>\-_]/.test(p)) score++
  return score
})

const passwordStrengthBars = computed(() => {
  const s = passwordStrength.value
  const colors = {
    0: 'bg-slate-200',
    1: 'bg-red-400',
    2: 'bg-orange-400',
    3: 'bg-yellow-400',
    4: 'bg-green-500',
  }
  const active = colors[s]
  return [
    s >= 1 ? active : 'bg-slate-200',
    s >= 2 ? active : 'bg-slate-200',
    s >= 3 ? active : 'bg-slate-200',
    s >= 4 ? active : 'bg-slate-200',
  ]
})

const passwordStrengthLabel = computed(() => {
  return ['', 'Weak', 'Fair', 'Good', 'Strong'][passwordStrength.value]
})

const passwordStrengthTextClass = computed(() => {
  return ['', 'text-red-500', 'text-orange-500', 'text-yellow-600', 'text-green-600'][passwordStrength.value]
})

// ── Submit ──────────────────────────────────────────────────────────────────
async function handleRegister() {
  // Touch all fields to show errors
  Object.keys(form).forEach(touch)

  const allFields = ['first_name', 'last_name', 'username', 'email', 'phone', 'pincode', 'city_id', 'password', 'confirm_password']
  const hasErrors = allFields.some(f => validateField(f) !== null)
  if (hasErrors) return

  isLoading.value = true
  serverError.value = null

  try {
    const payload = {
      username: form.username,
      email: form.email,
      password: form.password,
      first_name: form.first_name,
      last_name: form.last_name,
      pincode: form.pincode,
      city_id: Number(form.city_id),
    }
    if (form.phone) payload.phone = form.phone

    await authStore.register(payload)

    registered.value = true

    // Auto-redirect to login after 2.5s
    setTimeout(() => {
      router.push({ name: 'login' })
    }, 2500)
  } catch (err) {
    serverError.value = err.message || 'Registration failed. Please try again.'
  } finally {
    isLoading.value = false
  }
}

async function handlePincodeBlur() {
  normalizePincode()
  touch('pincode')
  touch('city_id')
  locationMessage.value = ''
  window.setTimeout(() => {
    showPincodeSuggestions.value = false
  }, 120)

  if (validateField('pincode')) {
    cityOptions.value = []
    form.city_id = ''
    return
  }

  try {
    const response = await locationService.lookupPincode(form.pincode)
    const matches = response?.data?.cities || []
    cityOptions.value = matches

    if (matches.length === 0) {
      form.city_id = ''
      locationMessage.value = 'No city mapping found for this pincode.'
      return
    }

    if (matches.length === 1) {
      form.city_id = matches[0].city_id
      locationMessage.value = `City resolved: ${matches[0].city_name}`
      return
    }

    if (!matches.some((city) => city.city_id === Number(form.city_id))) {
      form.city_id = ''
    }
    locationMessage.value = 'Multiple city options found. Please select one.'
  } catch (err) {
    cityOptions.value = []
    form.city_id = ''
    locationMessage.value = err?.response?.data?.message || 'Could not resolve pincode right now.'
  }
}

function normalizePincode() {
  form.pincode = (form.pincode || '').replace(/\D/g, '').slice(0, 6)
}

function handlePincodeInput() {
  normalizePincode()
  locationMessage.value = ''

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
    const response = await locationService.searchPincodes(prefix, 8)
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

onBeforeUnmount(() => {
  window.clearTimeout(pincodeSuggestDebounce)
})
</script>

<style scoped>
.field-error {
  @apply mt-1 text-xs text-red-600;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
