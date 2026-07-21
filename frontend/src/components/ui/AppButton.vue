<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="buttonClasses"
  >
    <span v-if="loading" class="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></span>
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
  },
  size: {
    type: String,
    default: 'md',
  },
  type: {
    type: String,
    default: 'button',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  fullWidth: {
    type: Boolean,
    default: false,
  },
})

const buttonClasses = computed(() => [
  'inline-flex items-center justify-center rounded-xl font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60',
  props.variant === 'primary' && 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500 active:scale-95',
  props.variant === 'secondary' && 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 focus:ring-primary-500',
  props.variant === 'danger' && 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  props.size === 'sm' && 'px-3 py-2 text-sm',
  props.size === 'md' && 'px-5 py-3 text-sm',
  props.size === 'lg' && 'px-6 py-3.5 text-base',
  props.fullWidth && 'w-full',
])
</script>