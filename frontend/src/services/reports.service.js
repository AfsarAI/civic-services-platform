/**
 * Reports service — wraps analytics/report API endpoints.
 *
 * Accessible to both administrator subtypes: system administrators get
 * platform-wide figures, municipal administrators are automatically scoped
 * to their own city by the backend.
 */

import api from './api'

const reportsService = {
  async getSummary(filters = {}) {
    const response = await api.get('/reports/complaints/summary', { params: filters })
    return response.data
  },

  async getByStatus(filters = {}) {
    const response = await api.get('/reports/complaints/by-status', { params: filters })
    return response.data
  },

  async getByCategory(filters = {}) {
    const response = await api.get('/reports/complaints/by-category', { params: filters })
    return response.data
  },

  async getByPriority(filters = {}) {
    const response = await api.get('/reports/complaints/by-priority', { params: filters })
    return response.data
  },

  async getByLocation(filters = {}) {
    const response = await api.get('/reports/complaints/by-location', { params: filters })
    return response.data
  },

  async getTrends(period = 'daily', filters = {}) {
    const response = await api.get('/reports/complaints/trends', { params: { period, ...filters } })
    return response.data
  },

  async getWorkerPerformance(filters = {}) {
    const response = await api.get('/reports/workers/performance', { params: filters })
    return response.data
  },

  async exportCsv(filters = {}) {
    return api.get('/reports/export/csv', { params: filters, responseType: 'blob' })
  },

  async exportExcel(filters = {}) {
    return api.get('/reports/export/excel', { params: filters, responseType: 'blob' })
  },

  async exportPdf(filters = {}) {
    return api.get('/reports/export/pdf', { params: filters, responseType: 'blob' })
  },
}

export default reportsService
