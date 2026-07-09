/**
 * Authentication service — wraps auth API endpoints.
 */

import api from './api'

class AuthService {
  /**
   * Authenticate a user and return tokens.
   * @param {string} email
   * @param {string} password
   */
  async login(email, password) {
    const response = await api.post('/auth/login', { email, password })
    return response.data
  }

  /**
   * Register a new user account.
   * @param {Object} userData
   */
  async register(userData) {
    const response = await api.post('/auth/register', userData)
    return response.data
  }

  /**
   * Refresh the access token.
   */
  async refresh() {
    const response = await api.post('/auth/refresh')
    return response.data
  }

  /**
   * Logout — invalidate the current token.
   */
  async logout() {
    const response = await api.post('/auth/logout')
    return response.data
  }

  /**
   * Get the current authenticated user's profile.
   */
  async me() {
    const response = await api.get('/auth/me')
    return response.data
  }

  /**
   * Update the current user's own profile (no username/email change).
   * @param {Object} data - { first_name, last_name, phone }
   */
  async updateProfile(data) {
    const response = await api.put('/auth/me', data)
    return response.data
  }

  /**
   * Change the current user's own password.
   * @param {Object} data - { current_password, new_password, confirm_password }
   */
  async changePassword(data) {
    const response = await api.post('/auth/change-password', data)
    return response.data
  }

  /**
   * Upload and set the current user's profile photo.
   * @param {File} file
   */
  async uploadAvatar(file) {
    const formData = new FormData()
    formData.append('photo', file)
    const response = await api.post('/auth/me/avatar', formData)
    return response.data
  }
}

const authService = new AuthService()

export default authService
