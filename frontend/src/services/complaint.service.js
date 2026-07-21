/**
 * Complaint service — wraps complaint API endpoints.
 */

import api from './api'

const complaintService = {
  /**
   * Get the current citizen's complaints.
   * @param {Object} params - Pagination and filter params
   */
  async getMyComplaints(params = {}) {
    const response = await api.get('/citizen/complaints', { params })
    return response.data
  },

  /**
   * Get dashboard summary (statistics and recent complaints).
   */
  async getDashboardSummary() {
    const response = await api.get('/citizen/dashboard')
    return response.data
  },

  /**
   * Submit a new complaint.
   * @param {Object} data - Complaint payload
   */
  async submitComplaint(data) {
    const response = await api.post('/citizen/complaints', data)
    return response.data
  },

  /**
   * Upload a complaint photo before submission.
   * @param {File} file
   */
  async uploadComplaintPhoto(file) {
    const formData = new FormData()
    formData.append('photo', file)
    const response = await api.post('/citizen/complaints/media', formData)
    return response.data
  },

  /**
   * Get a specific complaint by ID.
   * @param {number} id
   */
  async getComplaint(id) {
    const response = await api.get(`/citizen/complaints/${id}`)
    return response.data
  },

  /**
   * Update a complaint.
   * @param {number} id
   * @param {Object} data
   */
  async updateComplaint(id, data) {
    const response = await api.put(`/citizen/complaints/${id}`, data)
    return response.data
  },

  /**
   * Delete a complaint.
   * @param {number} id
   */
  async deleteComplaint(id) {
    const response = await api.delete(`/citizen/complaints/${id}`)
    return response.data
  },

  /**
   * Submit feedback for a resolved complaint.
   * @param {number} complaintId
   * @param {Object} feedbackData
   */
  async submitFeedback(complaintId, feedbackData) {
    const response = await api.post(`/citizen/complaints/${complaintId}/feedback`, feedbackData)
    return response.data
  },

  /**
   * Get all complaints (admin).
   * @param {Object} params
   */
  async getAllComplaints(params = {}) {
    const response = await api.get('/admin/complaints', { params })
    return response.data
  },

  /**
   * Get a specific complaint by ID (admin).
   * @param {number} id
   */
  async getAdminComplaint(id) {
    const response = await api.get(`/admin/complaints/${id}`)
    return response.data
  },

  /**
   * Update a complaint's status and/or priority (admin).
   * @param {number} id
   * @param {Object} data
   */
  async updateAdminComplaint(id, data) {
    const response = await api.put(`/admin/complaints/${id}`, data)
    return response.data
  },

  /**
   * Assign a complaint to a field worker (admin).
   * @param {number} complaintId
   * @param {Object} assignData
   */
  async assignComplaint(complaintId, assignData) {
    const response = await api.post(`/admin/complaints/${complaintId}/assign`, assignData)
    return response.data
  },
}

export default complaintService
