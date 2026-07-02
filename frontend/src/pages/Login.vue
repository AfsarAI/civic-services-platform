<template>
  <div class="card w-full">
    <div class="text-center mb-6">
      <h2 class="text-2xl font-bold text-gray-900">Sign In</h2>
      <p class="text-gray-500 text-sm mt-1">Enter your credentials to continue</p>
    </div>

    <form @submit.prevent="handleLogin" class="space-y-4">
      <div>
        <label for="email" class="form-label">Email</label>
        <input
          id="email"
          v-model="form.email"
          type="email"
          class="form-input"
          placeholder="you@example.com"
          required
          autocomplete="email"
        />
      </div>

      <div>
        <label for="password" class="form-label">Password</label>
        <input
          id="password"
          v-model="form.password"
          type="password"
          class="form-input"
          placeholder="••••••••"
          required
          autocomplete="current-password"
        />
      </div>

      <div v-if="error" class="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-3 py-2">
        {{ error }}
      </div>

      <button type="submit" class="btn-primary w-full" :disabled="isLoading">
        {{ isLoading ? 'Signing in…' : 'Sign In' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ email: '', password: '' })
const isLoading = ref(false)
const error = ref(null)

async function handleLogin() {
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
