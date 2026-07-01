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
          Create Account
        </h1>

        <p class="text-gray-500 mt-2">
          Register to access Civic Services
        </p>
      </div>

      <div class="bg-white rounded-3xl shadow-2xl p-8 border border-gray-100">

        <form @submit.prevent="handleRegister" class="space-y-5">

          <!-- Full Name -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Full Name
            </label>

            <input
              v-model="form.name"
              type="text"
              required
              placeholder="Enter your full name"
              class="w-full rounded-xl border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>

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
              class="w-full rounded-xl border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>

          <!-- Mobile -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Mobile Number
            </label>

            <input
              v-model="form.mobile"
              type="tel"
              maxlength="10"
              required
              placeholder="9876543210"
              class="w-full rounded-xl border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>

          <!-- Password -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>

            <input
              v-model="form.password"
              type="password"
              required
              placeholder="Password"
              class="w-full rounded-xl border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>

          <!-- Confirm Password -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Confirm Password
            </label>

            <input
              v-model="form.confirmPassword"
              type="password"
              required
              placeholder="Confirm Password"
              class="w-full rounded-xl border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>

          <!-- Error -->
          <div
            v-if="error"
            class="bg-red-50 border border-red-200 text-red-600 rounded-xl px-4 py-3 text-sm"
          >
            {{ error }}
          </div>

          <!-- Success -->
          <div
            v-if="success"
            class="bg-green-50 border border-green-200 text-green-700 rounded-xl px-4 py-3 text-sm"
          >
            {{ success }}
          </div>

          <!-- Button -->
          <button
            type="submit"
            :disabled="isLoading"
            class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 rounded-xl transition"
          >
            {{ isLoading ? "Creating Account..." : "Register" }}
          </button>

        </form>

        <div class="mt-6 text-center text-sm text-gray-500">
  Already have an account?

  <RouterLink
    to="/login"
    class="text-indigo-600 hover:text-indigo-700 font-semibold"
  >
    Sign In
  </RouterLink>
</div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const router = useRouter();

const form = reactive({
  name: "",
  email: "",
  mobile: "",
  password: "",
  confirmPassword: ""
});

const isLoading = ref(false);
const error = ref("");
const success = ref("");

async function handleRegister() {

  error.value = "";
  success.value = "";

  if (!form.name.trim()) {
    error.value = "Full Name is required.";
    return;
  }

  if (!/^[0-9]{10}$/.test(form.mobile)) {
    error.value = "Enter a valid 10-digit mobile number.";
    return;
  }

  if (form.password !== form.confirmPassword) {
    error.value = "Passwords do not match.";
    return;
  }

  isLoading.value = true;

  try {

    await authStore.register({
      name: form.name,
      email: form.email,
      mobile: form.mobile,
      password: form.password
    });

    success.value = "Registration successful! Redirecting to login...";

    setTimeout(() => {
      router.push({ name: "login" });
    }, 1500);

  } catch (err) {

    error.value =
      err.message ||
      "Email already exists or registration failed.";

  } finally {
    isLoading.value = false;
  }
}
</script>