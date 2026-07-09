<template>
  <div class="w-full">
    <!-- Header -->
    <div class="text-center mb-6">
      <h1 class="text-2xl font-bold text-slate-900">Welcome back</h1>
      <p class="text-slate-500 text-sm mt-1">Sign in to your Civic Services account</p>
    </div>

    <form @submit.prevent="handleLogin" class="space-y-5" novalidate>
      <!-- Email -->
      <div>
        <label for="email" class="form-label">Email Address</label>
        <input
          id="email"
          v-model.trim="form.email"
          type="email"
          class="form-input"
          :class="emailHasError ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
          placeholder="you@example.com"
          required
          autocomplete="email"
          @blur="touched.email = true"
          @input="clearFieldError('email')"
        />
        <transition name="slide-error">
          <p v-if="emailErrorMsg" class="field-error" id="email-error">
            <svg class="inline w-3.5 h-3.5 mr-1 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            {{ emailErrorMsg }}
          </p>
        </transition>
      </div>

      <!-- Password -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <label for="password" class="form-label mb-0">Password</label>
        </div>
        <div class="relative">
          <input
            id="password"
            v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            class="form-input pr-12"
            :class="passwordHasError ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
            placeholder="••••••••"
            required
            autocomplete="current-password"
            @blur="touched.password = true"
            @input="clearFieldError('password')"
          />
          <button
            type="button"
            @click="showPassword = !showPassword"
            class="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-700 transition-colors"
            :aria-label="showPassword ? 'Hide password' : 'Show password'"
          >
            <svg v-if="!showPassword" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
            </svg>
          </button>
        </div>
        <transition name="slide-error">
          <p v-if="passwordErrorMsg" class="field-error" id="password-error">
            <svg class="inline w-3.5 h-3.5 mr-1 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            {{ passwordErrorMsg }}
          </p>
        </transition>
      </div>

      <!-- General Server Error (non-field) -->
      <transition name="fade">
        <div
          v-if="generalError"
          class="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3"
          role="alert"
          id="login-error-alert"
        >
          <svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <p class="text-red-700 text-sm">{{ generalError }}</p>
        </div>
      </transition>

      <!-- Submit -->
      <button
        type="submit"
        class="btn-primary w-full mt-2"
        :disabled="isLoading"
        id="login-submit-btn"
      >
        <svg v-if="isLoading" class="w-4 h-4 animate-spin mr-2" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
        </svg>
        {{ isLoading ? 'Signing in…' : 'Sign In' }}
      </button>

      <!-- Register Link -->
      <p class="text-center text-sm text-slate-500 pt-1">
        Don't have an account?
        <RouterLink
          to="/register"
          class="font-semibold text-primary-600 hover:text-primary-700 transition-colors"
          id="go-to-register-link"
        >
          Create one free
        </RouterLink>
      </p>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ email: '', password: '' })
const touched = reactive({ email: false, password: false })
const isLoading = ref(false)
const showPassword = ref(false)

// Separate field-level and general errors
const fieldErrors = reactive({ email: null, password: null })
const generalError = ref(null)

// ── Client-side validation ───────────────────────────────────────────────────
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function validateEmail() {
  if (!form.email) return 'Email address is required.'
  if (!EMAIL_RE.test(form.email)) return 'Please enter a valid email address.'
  return null
}

function validatePassword() {
  if (!form.password) return 'Password is required.'
  return null
}

// ── Computed error messages ──────────────────────────────────────────────────
const emailErrorMsg = computed(() => {
  if (fieldErrors.email) return fieldErrors.email
  if (touched.email) return validateEmail()
  return null
})

const passwordErrorMsg = computed(() => {
  if (fieldErrors.password) return fieldErrors.password
  if (touched.password) return validatePassword()
  return null
})

const emailHasError = computed(() => !!emailErrorMsg.value)
const passwordHasError = computed(() => !!passwordErrorMsg.value)

// ── Clear errors on input ────────────────────────────────────────────────────
function clearFieldError(field) {
  fieldErrors[field] = null
  generalError.value = null
}

// ── Map backend error → field or general error ───────────────────────────────
function mapAuthError(message) {
  // Field-specific mapping (uses prefixes set in backend service.py)
  if (message.includes('No account found with this email')) {
    fieldErrors.email = 'No account found with this email.'
    return
  }
  if (message.includes('Incorrect password')) {
    fieldErrors.password = 'Incorrect password. Please try again.'
    return
  }
  if (message.includes('deactivated')) {
    generalError.value = 'Your account has been deactivated. Please contact support.'
    return
  }

  // HTTP status-based messages from Axios error object are passed as `message`
  generalError.value = message
}

function getFriendlyErrorMessage(err) {
  // Network / timeout / server unavailable
  if (!err.response) {
    if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
      return 'The request timed out. Please check your connection and try again.'
    }
    return 'Unable to reach the server. Please check your internet connection.'
  }

  const status = err.response.status
  const serverMessage = err.response.data?.message || ''

  // Return server message for field-mapping (it contains the "Invalid email or password: …" prefix)
  if (serverMessage) return serverMessage

  // Fallback per HTTP status
  const statusMessages = {
    400: 'Invalid request. Please check your input and try again.',
    401: 'Invalid credentials. Please check your email and password.',
    403: 'Access denied. You do not have permission to perform this action.',
    404: 'Service not found. Please try again later.',
    409: 'A conflict occurred. Please try again.',
    422: 'Validation failed. Please check your input.',
    500: 'A server error occurred. Please try again later.',
    502: 'The server is temporarily unavailable. Please try again shortly.',
    503: 'Service unavailable. Please try again later.',
  }
  return statusMessages[status] || 'An unexpected error occurred. Please try again.'
}

// ── Submit handler ───────────────────────────────────────────────────────────
async function handleLogin() {
  // Mark all fields as touched to trigger client-side validation display
  touched.email = true
  touched.password = true

  // Client-side guard — do not hit the API if basic validation fails
  if (validateEmail() || validatePassword()) return

  // Clear all prior errors
  fieldErrors.email = null
  fieldErrors.password = null
  generalError.value = null
  isLoading.value = true

  try {
    const loggedInUser = await authStore.login(form.email, form.password)
    const redirectTarget = route.query.redirect

    if (typeof redirectTarget === 'string' && redirectTarget.startsWith('/')) {
      await router.push(redirectTarget)
      return
    }

    if (loggedInUser?.role === 'administrator') {
      await router.push({ name: 'admin-dashboard' })
      return
    }
    if (loggedInUser?.role === 'citizen') {
      await router.push({ name: 'citizen-dashboard' })
      return
    }
    if (loggedInUser?.role === 'field_worker') {
      await router.push({ name: 'fieldworker-dashboard' })
      return
    }
    await router.push({ name: 'dashboard' })
  } catch (err) {
    const message = getFriendlyErrorMessage(err)
    mapAuthError(message)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.field-error {
  @apply mt-1.5 flex items-center text-xs text-red-600 font-medium;
}

/* General alert fade */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Inline field error slide-down */
.slide-error-enter-active {
  transition: all 0.2s ease-out;
}
.slide-error-leave-active {
  transition: all 0.15s ease-in;
}
.slide-error-enter-from,
.slide-error-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
