/**
 * Authentication service — wraps auth API endpoints.
 */

import api from './api'

const authService = {
  /**
   * Authenticate a user and return tokens.
   * @param {string} email
   * @param {string} password
   */
  async login(email, password) {
    const response = await api.post('/auth/login', { email, password })
    return response.data
  },

  /**
   * Register a new user account.
   * @param {Object} userData
   */
  async register(userData) {
    const response = await api.post('/auth/register', userData)
    return response.data
  },

  /**
   * Refresh the access token.
   */
  async refresh() {
    const response = await api.post('/auth/refresh')
    return response.data
  },

  /**
   * Logout — invalidate the current token.
   */
  async logout() {
    const response = await api.post('/auth/logout')
    return response.data
  },

  /**
   * Get the current authenticated user's profile.
   */
  async me() {
    const response = await api.get('/auth/me')
    return response.data
  },
}

export default authService
