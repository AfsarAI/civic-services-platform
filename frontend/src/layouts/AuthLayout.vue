<template>
  <div class="min-h-screen bg-slate-50 text-slate-800">
    <header class="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div class="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <RouterLink to="/landing" class="flex items-center gap-2 text-lg font-bold text-primary-700">
          <span class="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-sm font-bold text-white">CS</span>
          Civic Services
        </RouterLink>

        <nav class="flex items-center gap-1.5 sm:gap-2">
          <RouterLink to="/landing" class="rounded-lg px-2.5 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 sm:px-3 sm:text-sm">Home</RouterLink>
          <RouterLink to="/login" class="rounded-lg px-2.5 py-2 text-xs font-medium text-primary-700 hover:bg-primary-50 sm:px-3 sm:text-sm">Login</RouterLink>
          <RouterLink to="/register" class="btn-primary px-3 py-2 text-xs sm:px-4 sm:text-sm">Register</RouterLink>
        </nav>
      </div>
    </header>

    <main class="relative overflow-hidden px-4 py-8 sm:px-6 sm:py-12">
      <div class="absolute -left-20 top-12 h-56 w-56 rounded-full bg-cyan-300/25 blur-3xl sm:h-72 sm:w-72"></div>
      <div class="absolute -right-24 bottom-6 h-64 w-64 rounded-full bg-blue-300/25 blur-3xl sm:h-80 sm:w-80"></div>

      <div class="relative mx-auto w-full max-w-6xl">
        <div class="grid gap-6 lg:grid-cols-[1fr_1fr] lg:items-center">
          <section class="hidden lg:block">
            <p class="mb-3 inline-flex rounded-full border border-sky-200 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-sky-700">
              Secure Access
            </p>
            <h1 class="text-4xl font-bold tracking-tight text-slate-900">
              Civic complaint workflows, all in one place.
            </h1>
            <p class="mt-4 max-w-lg text-base text-slate-600">
              Sign in to track complaints, assign field teams, and close civic issues with accountable updates.
            </p>
          </section>

          <section class="mx-auto w-full max-w-xl rounded-3xl border border-slate-200 bg-white/95 p-5 shadow-xl backdrop-blur sm:p-7">
            <div class="mb-6 flex justify-center">
              <div class="inline-flex rounded-full border border-slate-200 bg-slate-50 p-1">
                <RouterLink
                  to="/login"
                  class="rounded-full px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-slate-600 transition-colors hover:text-slate-900"
                  active-class="bg-primary-600 text-white shadow"
                >
                  Login
                </RouterLink>
                <RouterLink
                  to="/register"
                  class="rounded-full px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-slate-600 transition-colors hover:text-slate-900"
                  active-class="bg-primary-600 text-white shadow"
                >
                  Register
                </RouterLink>
              </div>
            </div>

            <RouterView />
          </section>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>
