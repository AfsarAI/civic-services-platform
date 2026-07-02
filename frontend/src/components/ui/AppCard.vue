<template>
  <div :class="cardClasses">
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  hover: {
    type: Boolean,
    default: false,
  },
  padding: {
    type: String,
    default: 'md',
  },
})

const cardClasses = computed(() => [
  'rounded-2xl border border-slate-200 bg-white shadow-sm',
  props.hover && 'transition-all duration-300 hover:-translate-y-1 hover:shadow-xl',
  props.padding === 'sm' && 'p-4',
  props.padding === 'md' && 'p-6',
  props.padding === 'lg' && 'p-8',
])
</script>