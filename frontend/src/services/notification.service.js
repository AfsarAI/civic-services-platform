/**
 * Notification service — wraps notification API endpoints.
 */

import api from './api'

const notificationService = {
  /**
   * Get paginated notifications for the current user.
   * @param {Object} params - { page, per_page, unread_only }
   */
  async getNotifications(params = {}) {
    const response = await api.get('/notifications/', { params })
    return response.data
  },

  /**
   * Get a single notification by ID.
   * @param {number} id
   */
  async getNotification(id) {
    const response = await api.get(`/notifications/${id}`)
    return response.data
  },

  /**
   * Mark a single notification as read.
   * @param {number} id
   */
  async markAsRead(id) {
    const response = await api.patch(`/notifications/${id}/read`)
    return response.data
  },

  /**
   * Mark all notifications as read.
   */
  async markAllAsRead() {
    const response = await api.patch('/notifications/read-all')
    return response.data
  },

  /**
   * Get the unread notification count.
   */
  async getUnreadCount() {
    const response = await api.get('/notifications/unread-count')
    return response.data
  },
}

export default notificationService
