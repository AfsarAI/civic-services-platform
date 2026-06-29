<template>
  <div class="max-w-2xl">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Report a Civic Issue</h1>
      <p class="text-gray-500 text-sm mt-1">Fill in the details below to submit a new complaint.</p>
    </div>

    <form @submit.prevent="handleSubmit" class="card space-y-5">
      <div>
        <label for="title" class="form-label">Title <span class="text-red-500">*</span></label>
        <input id="title" v-model="form.title" type="text" class="form-input" placeholder="e.g. Large pothole on Main Street" required />
      </div>

      <div>
        <label for="category" class="form-label">Category <span class="text-red-500">*</span></label>
        <select id="category" v-model="form.category" class="form-input" required>
          <option value="" disabled>Select a category</option>
          <option v-for="cat in categories" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
        </select>
      </div>

      <div>
        <label for="description" class="form-label">Description <span class="text-red-500">*</span></label>
        <textarea id="description" v-model="form.description" rows="4" class="form-input" placeholder="Provide as much detail as possible…" required></textarea>
      </div>

      <div>
        <label for="address" class="form-label">Address / Location</label>
        <input id="address" v-model="form.address" type="text" class="form-input" placeholder="Street address or landmark" />
      </div>

      <div>
        <label for="priority" class="form-label">Priority</label>
        <select id="priority" v-model="form.priority" class="form-input">
          <option value="low">Low</option>
          <option value="medium" selected>Medium</option>
          <option value="high">High</option>
          <option value="urgent">Urgent</option>
        </select>
      </div>

      <div v-if="error" class="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-3 py-2">{{ error }}</div>

      <div class="flex gap-3 pt-2">
        <button type="submit" class="btn-primary" :disabled="isLoading">
          {{ isLoading ? 'Submitting…' : 'Submit Complaint' }}
        </button>
        <RouterLink to="/citizen/dashboard" class="btn-secondary">Cancel</RouterLink>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

const router = useRouter()
const isLoading = ref(false)
const error = ref(null)

const form = reactive({
  title: '',
  category: '',
  description: '',
  address: '',
  priority: 'medium',
})

const categories = [
  { value: 'pothole',      label: 'Pothole' },
  { value: 'streetlight',  label: 'Streetlight' },
  { value: 'drainage',     label: 'Drainage' },
  { value: 'garbage',      label: 'Garbage' },
  { value: 'road_damage',  label: 'Road Damage' },
  { value: 'other',        label: 'Other' },
]

async function handleSubmit() {
  isLoading.value = true
  error.value = null
  try {
    // TODO: call complaintStore.submitComplaint(form)
    throw new Error('Submission not yet implemented')
  } catch (err) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}
</script>
