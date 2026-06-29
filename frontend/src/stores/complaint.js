import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useComplaintStore = defineStore('complaint', () => {
  // ── State ──────────────────────────────────────────────────────────────
  const complaints = ref([])
  const currentComplaint = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  const pagination = ref({ total: 0, page: 1, per_page: 20, pages: 0 })

  // ── Getters ────────────────────────────────────────────────────────────
  const totalComplaints = computed(() => pagination.value.total)

  // ── Actions ────────────────────────────────────────────────────────────
  async function fetchComplaints(params = {}) {
    // TODO: call complaintService.getComplaints(params)
    isLoading.value = true
    error.value = null
    try {
      throw new Error('fetchComplaints not yet implemented')
    } finally {
      isLoading.value = false
    }
  }

  async function fetchComplaint(id) {
    // TODO: call complaintService.getComplaint(id)
    throw new Error('fetchComplaint not yet implemented')
  }

  async function submitComplaint(data) {
    // TODO: call complaintService.submitComplaint(data)
    throw new Error('submitComplaint not yet implemented')
  }

  async function updateComplaint(id, data) {
    // TODO: call complaintService.updateComplaint(id, data)
    throw new Error('updateComplaint not yet implemented')
  }

  function clearCurrent() {
    currentComplaint.value = null
  }

  return {
    complaints,
    currentComplaint,
    isLoading,
    error,
    pagination,
    totalComplaints,
    fetchComplaints,
    fetchComplaint,
    submitComplaint,
    updateComplaint,
    clearCurrent,
  }
})
