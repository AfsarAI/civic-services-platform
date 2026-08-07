/**
 * Administrator service — wraps system-admin municipal administrator APIs.
 */

import api from './api'

const adminService = {
  async getCities() {
    const response = await api.get('/admin/cities')
    return response.data
  },

  async lookupPincode(pincode) {
    const response = await api.get(`/locations/pincode/${pincode}`)
    return response.data
  },

  async searchPincodes(prefix = '', limit = 10) {
    const response = await api.get('/locations/pincodes', { params: { prefix, limit } })
    return response.data
  },

  async searchCities(query = '', limit = 10) {
    const response = await api.get('/locations/cities', { params: { query, limit } })
    return response.data
  },

  async getMunicipalAdministrators(params = {}) {
    const response = await api.get('/admin/municipal-administrators', { params })
    return response.data
  },

  async createMunicipalAdministrator(payload) {
    const response = await api.post('/admin/municipal-administrators', payload)
    return response.data
  },

  async deactivateMunicipalAdministrator(userId) {
    const response = await api.delete(`/admin/municipal-administrators/${userId}`)
    return response.data
  },

  async updateMunicipalAdministrator(userId, payload) {
    const response = await api.put(`/admin/municipal-administrators/${userId}`, payload)
    return response.data
  },

  async getUsers(params = {}) {
    const response = await api.get('/admin/users', { params })
    return response.data
  },

  async updateUser(userId, payload) {
    const response = await api.put(`/admin/users/${userId}`, payload)
    return response.data
  },

  async getFieldWorkers(params = {}) {
    const response = await api.get('/admin/field-workers', { params })
    return response.data
  },

  async createFieldWorker(payload) {
    const response = await api.post('/admin/field-workers', payload)
    return response.data
  },

  async updateFieldWorker(userId, payload) {
    const response = await api.put(`/admin/field-workers/${userId}`, payload)
    return response.data
  },

  async getDashboard(params = {}) {
    const response = await api.get('/admin/dashboard', { params })
    return response.data
  },

  async getSystemSettings() {
    const response = await api.get('/admin/settings')
    return response.data
  },

  async updateSystemSettings(payload) {
    const response = await api.put('/admin/settings', payload)
    return response.data
  },

  async getDashboardSummary() {
    const response = await api.get('/admin/dashboard')
    return response.data
  },
}

export default adminService
