/**
 * Field worker service — wraps assignment tracking API endpoints.
 */

import api from './api'

const fieldWorkerService = {
  /**
   * Get the current field worker's assignments.
   * @param {Object} params - Pagination and filter params (page, per_page, status)
   */
  async getAssignments(params = {}) {
    const response = await api.get('/fieldworker/assignments', { params })
    return response.data
  },

  /**
   * Get dashboard summary(counts by status and recent assignments).
   */
  async getDashboardSummary() {
    const response = await api.get('/fieldworker/dashboard')
    return response.data
  },

  /**
   * Get a specific assignment by ID.
   * @param {number} id
   */
  async getAssignment(id) {
    const response = await api.get(`/fieldworker/assignments/${id}`)
    return response.data
  },

  /**
   * Accept an assigned task.
   * @param {number} id
   */
  async acceptAssignment(id) {
    const response = await api.post(`/fieldworker/assignments/${id}/accept`)
    return response.data
  },

  /**
   * Update assignment progress (in_progress or rejected), with optional notes.
   * @param {number} id
   * @param {Object} data - { status, notes }
   */
  async updateProgress(id, data) {
    const response = await api.put(`/fieldworker/assignments/${id}`, data)
    return response.data
  },

  /**
   * Mark an assignment as completed and also optionally attaching evidence_url.
   * @param {number} id
   * @param {Object} data - { evidence_url }
   */
  async completeAssignment(id, data = {}) {
    const response = await api.post(`/fieldworker/assignments/${id}/complete`, data)
    return response.data
  },

  /**
   * Upload a repair-completion evidence photo.
   * @param {File} file
   */
  async uploadEvidencePhoto(file) {
    const formData = new FormData()
    formData.append('photo', file)
    const response = await api.post('/fieldworker/assignments/media', formData)
    return response.data
  },
}

export default fieldWorkerService
