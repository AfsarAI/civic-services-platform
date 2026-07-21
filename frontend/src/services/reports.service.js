/**
 * Reports service — wraps analytics/report API endpoints (system admin only).
 */

import api from './api'

const reportsService = {
  async getSummary() {
    const response = await api.get('/reports/complaints/summary')
    return response.data
  },

  async getByStatus() {
    const response = await api.get('/reports/complaints/by-status')
    return response.data
  },

  async getByCategory() {
    const response = await api.get('/reports/complaints/by-category')
    return response.data
  },

  async getTrends(period = 'daily') {
    const response = await api.get('/reports/complaints/trends', { params: { period } })
    return response.data
  },

  async getWorkerPerformance() {
    const response = await api.get('/reports/workers/performance')
    return response.data
  },
}

export default reportsService
