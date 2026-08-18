export const INDIAN_MOBILE_PATTERN = /^[6-9]\d{9}$/
export const INDIAN_MOBILE_ERROR = 'Enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.'

export function validateIndianMobile(value, { required = false } = {}) {
  const normalized = typeof value === 'string' ? value.trim() : value

  if (!normalized) {
    return required ? 'Mobile number is required.' : null
  }

  return INDIAN_MOBILE_PATTERN.test(normalized) ? null : INDIAN_MOBILE_ERROR
}
