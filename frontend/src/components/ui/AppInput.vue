<template>
  <div>
    <label
      v-if="label"
      :for="id"
      class="form-label"
    >
      {{ label }}
    </label>

    <input
      :id="id"
      :value="modelValue"
      :type="type"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      :required="required"
      :disabled="disabled"
      class="form-input"
      @input="$emit('update:modelValue', $event.target.value)"
    />

    <p
      v-if="helperText"
      class="mt-2 text-xs text-slate-500"
    >
      {{ helperText }}
    </p>

    <p
      v-if="error"
      class="mt-2 text-xs font-medium text-red-600"
    >
      {{ error }}
    </p>
  </div>
</template>

<script setup>
defineProps({
  id: String,
  label: String,
  modelValue: {
    type: String,
    default: '',
  },
  type: {
    type: String,
    default: 'text',
  },
  placeholder: String,
  autocomplete: String,
  helperText: String,
  error: String,
  required: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['update:modelValue'])
</script>