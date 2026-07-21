/**
 * Location service — pincode and city suggestion APIs.
 */

import api from './api'

const locationService = {
  async lookupPincode(pincode) {
    const response = await api.get(`/locations/pincode/${pincode}`)
    return response.data
  },

  async searchPincodes(prefix = '', limit = 10) {
    const response = await api.get('/locations/pincodes', { params: { prefix, limit } })
    return response.data
  },

  async getOverview() {
    const response = await api.get('/locations/overview')
    return response.data
  },

  async getComplaintPins(limit = 500) {
    const response = await api.get('/locations/complaint-pins', { params: { limit } })
    return response.data
  },

  async reverseGeocode(latitude, longitude) {
    const response = await api.get('/locations/reverse-geocode', {
      params: { lat: latitude, lon: longitude },
    })
    return response.data
  },

  async searchCities(query = '', limit = 10) {
    const response = await api.get('/locations/cities', { params: { query, limit } })
    return response.data
  },
}

export default locationService
