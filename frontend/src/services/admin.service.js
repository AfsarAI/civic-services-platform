/**
 * Administrator service — wraps system-admin municipal administrator APIs.
 */

import api from './api'

const adminService = {
  async getCities() {
    const response = await api.get('/admin/cities')
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
}

export default adminService
