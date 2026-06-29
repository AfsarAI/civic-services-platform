/**
 * Utility helpers.
 */

/**
 * Format a date string to a human-readable format.
 * @param {string} dateString
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string}
 */
export function formatDate(dateString, options = {}) {
  if (!dateString) return '—'
  const defaults = { year: 'numeric', month: 'short', day: 'numeric' }
  return new Intl.DateTimeFormat('en-AU', { ...defaults, ...options }).format(new Date(dateString))
}

/**
 * Capitalise the first letter of a string.
 * @param {string} str
 * @returns {string}
 */
export function capitalise(str) {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, ' ')
}

/**
 * Map a complaint status to its badge CSS class.
 * @param {string} status
 * @returns {string}
 */
export function statusBadgeClass(status) {
  const map = {
    pending:     'badge-pending',
    assigned:    'badge-assigned',
    in_progress: 'badge-progress',
    resolved:    'badge-resolved',
    closed:      'badge-closed',
    rejected:    'badge-rejected',
  }
  return map[status] ?? 'badge-pending'
}

/**
 * Truncate a string to a maximum length with ellipsis.
 * @param {string} str
 * @param {number} max
 * @returns {string}
 */
export function truncate(str, max = 80) {
  if (!str || str.length <= max) return str
  return str.slice(0, max) + '…'
}

/**
 * Parse an API error response into a human-readable message.
 * @param {Error} error - Axios error
 * @returns {string}
 */
export function parseApiError(error) {
  if (error.response?.data?.message) return error.response.data.message
  if (error.response?.data?.errors) return JSON.stringify(error.response.data.errors)
  return error.message || 'An unexpected error occurred.'
}
