<template>
  <div class="min-h-screen bg-slate-50 text-slate-800">
    <header class="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div class="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <RouterLink to="/landing" class="flex items-center gap-2 text-lg font-bold text-primary-700">
          <span class="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-sm font-bold text-white">CS</span>
          Civic Services
        </RouterLink>

        <nav class="flex items-center gap-1.5 sm:gap-2">
          <a href="#about" class="rounded-lg px-2.5 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 sm:px-3 sm:text-sm">About</a>
          <RouterLink to="/login" class="rounded-lg px-2.5 py-2 text-xs font-medium text-primary-700 hover:bg-primary-50 sm:px-3 sm:text-sm">Login</RouterLink>
          <RouterLink to="/register" class="btn-primary px-3 py-2 text-xs sm:px-4 sm:text-sm">Register</RouterLink>
        </nav>
      </div>
    </header>

    <main>
      <section class="relative overflow-hidden border-b border-slate-200 bg-gradient-to-br from-white via-sky-50 to-cyan-100">
        <div class="absolute -left-24 top-10 h-56 w-56 rounded-full bg-cyan-300/30 blur-3xl sm:h-72 sm:w-72"></div>
        <div class="absolute -right-20 bottom-0 h-64 w-64 rounded-full bg-blue-300/30 blur-3xl sm:h-80 sm:w-80"></div>

        <div class="relative mx-auto w-full max-w-6xl px-4 py-9 sm:px-6 sm:py-12 lg:py-16">
          <div class="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-start">
            <div>
              <p class="mb-3 inline-flex rounded-full border border-sky-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-sky-700 sm:text-xs">
                Mobile First Civic Platform
              </p>
              <h1 class="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl">
                One place to report, track, and resolve civic complaints across India.
              </h1>
              <p class="mt-4 max-w-2xl text-sm text-slate-600 sm:text-base lg:text-lg">
                Report potholes with a photo, map pin, and pincode. The app is built for fast mobile reporting and transparent resolution.
              </p>

              <div class="mt-6 flex flex-wrap gap-3">
                <RouterLink to="/register" class="btn-primary">Create Account</RouterLink>
                <RouterLink to="/login" class="btn-secondary">Sign In</RouterLink>
              </div>

              <div class="mt-7 grid grid-cols-2 gap-3 sm:grid-cols-4">
                <article class="rounded-xl border border-slate-200 bg-white px-3 py-3 shadow-sm">
                  <p class="text-[11px] uppercase tracking-wide text-slate-500 sm:text-xs">Registered Users</p>
                  <p class="mt-1 text-xl font-bold text-slate-900">{{ formatNumber(overview.registered_users) }}</p>
                </article>
                <article class="rounded-xl border border-slate-200 bg-white px-3 py-3 shadow-sm">
                  <p class="text-[11px] uppercase tracking-wide text-slate-500 sm:text-xs">Open Complaints</p>
                  <p class="mt-1 text-xl font-bold text-amber-600">{{ formatNumber(overview.open_complaints) }}</p>
                </article>
                <article class="rounded-xl border border-slate-200 bg-white px-3 py-3 shadow-sm">
                  <p class="text-[11px] uppercase tracking-wide text-slate-500 sm:text-xs">Resolved</p>
                  <p class="mt-1 text-xl font-bold text-emerald-600">{{ formatNumber(overview.resolved_complaints) }}</p>
                </article>
                <article class="rounded-xl border border-slate-200 bg-white px-3 py-3 shadow-sm">
                  <p class="text-[11px] uppercase tracking-wide text-slate-500 sm:text-xs">Pincodes</p>
                  <p class="mt-1 text-xl font-bold text-slate-900">{{ formatNumber(overview.pincode_coverage) }}</p>
                </article>
              </div>
            </div>

            <PublicComplaintMap :markers="mapMarkers" :loading="isMapLoading" />
          </div>
        </div>
      </section>

      <section id="about" class="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6 lg:py-14">
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <article class="card">
            <h3 class="text-base font-semibold">Photo First</h3>
            <p class="mt-2 text-sm text-slate-600">Snap the pothole, place the pin, and submit with one thumb on mobile.</p>
          </article>
          <article class="card">
            <h3 class="text-base font-semibold">Pothole Only</h3>
            <p class="mt-2 text-sm text-slate-600">The product is focused on pothole reporting, not general civic service requests.</p>
          </article>
          <article class="card">
            <h3 class="text-base font-semibold">Live Coverage View</h3>
            <p class="mt-2 text-sm text-slate-600">OpenStreetMap-based India view shows pothole pins and helps identify hotspot areas.</p>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'

import PublicComplaintMap from '@/components/PublicComplaintMap.vue'
import locationService from '@/services/location.service'

const overview = reactive({
  registered_users: 0,
  open_complaints: 0,
  resolved_complaints: 0,
  total_complaints: 0,
  pincode_coverage: 0,
  city_coverage: 0,
})

const mapMarkers = ref([])
const isMapLoading = ref(false)

function formatNumber(value) {
  return Number(value || 0).toLocaleString('en-IN')
}

async function loadOverview() {
  try {
    const response = await locationService.getOverview()
    Object.assign(overview, response?.data || {})
  } catch {
    // Keep zero-state if backend is unavailable.
  }
}

async function loadComplaintPins() {
  isMapLoading.value = true
  try {
    const response = await locationService.getComplaintPins(600)
    mapMarkers.value = response?.data?.items || []
  } catch {
    mapMarkers.value = []
  } finally {
    isMapLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadOverview(), loadComplaintPins()])
})
</script>
