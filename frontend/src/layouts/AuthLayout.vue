<template>
  <div class="min-h-screen bg-slate-50">
    <div class="grid min-h-screen lg:grid-cols-2">
      <!-- Left branding panel -->
      <section class="hidden lg:flex flex-col justify-between bg-gradient-to-br from-primary-50 via-white to-slate-100 p-14">
        <div>
          <div class="flex items-center gap-3">
            <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary-600 text-white shadow-lg">
              🏛️
            </div>

            <div>
              <h1 class="text-2xl font-bold text-slate-900">
                Civic Services
              </h1>
              <p class="text-sm font-medium text-primary-600">
                Platform
              </p>
            </div>
          </div>

          <div class="mt-20 max-w-xl">
            <p class="mb-4 inline-flex rounded-full bg-primary-100 px-4 py-2 text-sm font-semibold text-primary-700">
              Smart city service management
            </p>

            <h2 class="text-5xl font-bold leading-tight text-slate-900">
              Report, track and resolve civic issues faster.
            </h2>

            <p class="mt-6 text-lg leading-8 text-slate-600">
              A unified platform for citizens, administrators and field workers
              to collaborate for better community services.
            </p>
          </div>

          <div class="mt-12 grid gap-5">
            <div class="card">
              <h3 class="text-base font-semibold text-slate-900">📍 Report Issues</h3>
              <p class="mt-1 text-sm text-slate-500">
                Citizens can report road, water, sanitation and electricity problems.
              </p>
            </div>

            <div class="card">
              <h3 class="text-base font-semibold text-slate-900">🔔 Track Progress</h3>
              <p class="mt-1 text-sm text-slate-500">
                Stay updated from complaint submission to final resolution.
              </p>
            </div>

            <div class="card">
              <h3 class="text-base font-semibold text-slate-900">👷 Field Assignment</h3>
              <p class="mt-1 text-sm text-slate-500">
                Administrators can assign and monitor field worker activity.
              </p>
            </div>
          </div>
        </div>

        <p class="text-sm text-slate-500">
          © 2026 Civic Services Platform. Building better communities.
        </p>
      </section>

      <!-- Right auth panel -->
      <section class="flex items-center justify-center px-6 py-10 sm:px-8 lg:px-16">
        <div class="w-full max-w-md">
          <RouterView />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
</script>