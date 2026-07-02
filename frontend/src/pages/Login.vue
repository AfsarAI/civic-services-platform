<template>
  <AppCard padding="lg">
    <div class="text-center">
      <h1 class="text-3xl font-bold text-slate-900">
        Welcome Back
      </h1>

      <p class="mt-2 text-sm text-slate-500">
        Sign in to continue to Civic Services Platform
      </p>
    </div>

    <form class="mt-8 space-y-5" @submit.prevent="handleLogin">
      <AppInput
        id="email"
        v-model="form.email"
        label="Email Address"
        type="email"
        placeholder="you@example.com"
        autocomplete="email"
        required
      />

      <AppInput
        id="password"
        v-model="form.password"
        label="Password"
        type="password"
        placeholder="••••••••"
        autocomplete="current-password"
        required
      />

      <div class="flex items-center justify-between text-sm">
        <label class="flex items-center gap-2 text-slate-600">
          <input type="checkbox" class="rounded border-slate-300">
          Remember me
        </label>

        <a href="#" class="font-medium text-primary-600 hover:text-primary-700">
          Forgot Password?
        </a>
      </div>

      <div
        v-if="error"
        class="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-600"
      >
        {{ error }}
      </div>

      <AppButton type="submit" full-width :loading="isLoading">
        Sign In
      </AppButton>
    </form>

    <div class="my-8 flex items-center">
      <div class="h-px flex-1 bg-slate-200"></div>
      <span class="px-4 text-sm text-slate-400">OR</span>
      <div class="h-px flex-1 bg-slate-200"></div>
    </div>

    <div class="space-y-3">
      <AppButton variant="secondary" full-width>
        Continue with Google
      </AppButton>

      <AppButton variant="secondary" full-width>
        Continue with Microsoft
      </AppButton>
    </div>

    <p class="mt-8 text-center text-sm text-slate-500">
      Don't have an account?
      <a href="#" class="font-semibold text-primary-600 hover:text-primary-700">
        Register
      </a>
    </p>
  </AppCard>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppInput from '@/components/ui/AppInput.vue'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  email: '',
  password: '',
})

const isLoading = ref(false)
const error = ref(null)

async function handleLogin() {
  isLoading.value = true
  error.value = null

  try {
    await authStore.login(form.email, form.password)
    router.push({ name: 'dashboard' })
  } catch (err) {
    error.value = err.message || 'Login failed. Please check your credentials.'
  } finally {
    isLoading.value = false
  }
}
</script>