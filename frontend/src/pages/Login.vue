<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 via-blue-50 to-indigo-100 px-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div
          class="w-16 h-16 mx-auto rounded-2xl bg-indigo-600 flex items-center justify-center shadow-lg"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="w-8 h-8 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 11c1.657 0 3-1.79 3-4s-1.343-4-3-4-3 1.79-3 4 1.343 4 3 4zm0 2c-2.761 0-5 2.239-5 5v1h10v-1c0-2.761-2.239-5-5-5z"
            />
          </svg>
        </div>

        <h1 class="text-3xl font-bold text-gray-800 mt-5">
          Welcome Back
        </h1>

        <p class="text-gray-500 mt-2">
          Sign in to access your dashboard
        </p>
      </div>

      <!-- Card -->
      <div class="bg-white rounded-3xl shadow-2xl p-8 border border-gray-100">
        <form @submit.prevent="handleLogin" class="space-y-5">

          <!-- Email -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>

            <input
              v-model="form.email"
              type="email"
              required
              placeholder="you@example.com"
              autocomplete="email"
              class="w-full rounded-xl border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
            />
          </div>

          <!-- Password -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>

            <div class="relative">
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                required
                autocomplete="current-password"
                placeholder="Enter your password"
                class="w-full rounded-xl border border-gray-300 px-4 py-3 pr-12 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
              />

              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-indigo-600"
              >
                {{ showPassword ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>

          <!-- Forgot Password -->
          <div class="flex justify-end">
            <a
              href="#"
              class="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
            >
              Forgot Password?
            </a>
          </div>

          <!-- Error -->
          <div
            v-if="error"
            class="bg-red-50 border border-red-200 text-red-600 rounded-xl px-4 py-3 text-sm"
          >
            {{ error }}
          </div>

          <!-- Button -->
          <button
            type="submit"
            :disabled="isLoading"
            class="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-70 text-white font-semibold py-3 rounded-xl transition flex justify-center items-center"
          >
            <svg
              v-if="isLoading"
              class="animate-spin h-5 w-5 mr-2"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-20"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              />

              <path
                class="opacity-90"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
              />
            </svg>

            {{ isLoading ? 'Signing In...' : 'Sign In' }}
          </button>
        </form>
         <div class="mt-6 text-center text-sm text-gray-500">
  Don't have an account?

  <RouterLink
    to="/register"
    class="text-indigo-600 hover:text-indigo-700 font-semibold"
  >
    Register
  </RouterLink>
</div>
        <!-- Footer -->
        <div class="mt-8 text-center text-sm text-gray-500">
          © {{ new Date().getFullYear() }} Your Company. All rights reserved.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
<<<<<<< HEAD
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const router = useRouter();
=======
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
>>>>>>> origin/dev

const form = reactive({
  email: "",
  password: "",
});

const showPassword = ref(false);
const isLoading = ref(false);
const error = ref("");

async function handleLogin() {
  isLoading.value = true;
  error.value = "";

  try {
<<<<<<< HEAD
    await authStore.login(form.email, form.password);
    router.push({ name: "dashboard" });
=======
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
>>>>>>> origin/dev
  } catch (err) {
    error.value =
      err.message || "Invalid email or password. Please try again.";
  } finally {
    isLoading.value = false;
  }
}
</script>