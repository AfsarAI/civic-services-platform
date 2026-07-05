<template>
  <div class="min-h-screen w-full flex items-center justify-center bg-slate-900 relative overflow-hidden px-4 py-12 sm:px-6 lg:px-8">
    
    <!-- Ambient glowing backgrounds -->
    <div class="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary-600/20 blur-[120px] pointer-events-none"></div>
    <div class="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-blue-500/20 blur-[120px] pointer-events-none"></div>

    <!-- Centered Box Content -->
    <div class="relative z-10 w-full max-w-lg bg-slate-800/40 backdrop-blur-xl border border-slate-700/50 rounded-3xl p-8 sm:p-10 shadow-2xl transition-all duration-300">
      
      <!-- Logo and Platform name -->
      <div class="flex flex-col items-center justify-center mb-6">
        <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-500 to-blue-600 text-white shadow-lg shadow-primary-500/30 mb-3">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
          </svg>
        </div>
        <h2 class="text-xl font-extrabold text-white tracking-tight">Civic Sense</h2>
        <span class="text-xs font-semibold text-primary-400 uppercase tracking-widest mt-0.5">Smart City System</span>
      </div>

      <RouterView />
    </div>

    <!-- Bottom Footer Info -->
    <div class="absolute bottom-4 left-0 right-0 text-center text-xs text-slate-500 pointer-events-none">
      © 2026 Civic Sense. All rights reserved.
    </div>
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
</script>

<style scoped>
/* Scoped overrides to make login/register form elements matches the dark glassmorphic layout */
:deep(.form-label) {
  @apply text-slate-300 font-medium text-xs mb-1.5;
}

:deep(.form-input) {
  @apply bg-slate-900/60 border-slate-700/80 text-white placeholder:text-slate-500 focus:border-primary-500 focus:ring-primary-500/20 focus:bg-slate-950/80;
}

:deep(.field-error) {
  @apply text-red-400 text-xs mt-1;
}

:deep(.text-slate-900) {
  @apply text-white;
}

:deep(.text-slate-500) {
  @apply text-slate-400;
}

:deep(.card) {
  @apply bg-slate-900/40 border-slate-700/60;
}
</style>