<template>
  <div class="w-full">
    <!-- Header -->
    <div class="text-center mb-6">
      <h1 class="text-2xl font-bold text-white">Welcome back</h1>
      <p class="text-slate-400 text-sm mt-1">Sign in to your Civic Sense account</p>
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
          :class="touched.email && !form.email ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
          placeholder="you@example.com"
          required
          autocomplete="email"
          @blur="touched.email = true"
        />
        <p v-if="touched.email && !form.email" class="mt-1 text-xs text-red-600">Email address is required.</p>
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
            :class="touched.password && !form.password ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''"
            placeholder="••••••••"
            required
            autocomplete="current-password"
            @blur="touched.password = true"
          />
          <button
            type="button"
            @click="showPassword = !showPassword"
            class="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
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
        <p v-if="touched.password && !form.password" class="mt-1 text-xs text-red-600">Password is required.</p>
      </div>

      <!-- Server Error -->
      <transition name="fade">
        <div
          v-if="error"
          class="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3"
          role="alert"
          id="login-error-alert"
        >
          <svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <p class="text-red-700 text-sm">{{ error }}</p>
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
import { ref, reactive } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ email: '', password: '' })
const touched = reactive({ email: false, password: false })
const isLoading = ref(false)
const error = ref(null)
const showPassword = ref(false)

async function handleLogin() {
  touched.email = true
  touched.password = true

  if (!form.email || !form.password) return

  isLoading.value = true
  error.value = null

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
    error.value = err.message || 'Login failed. Please check your credentials.'
  } finally {
    isLoading.value = false
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
