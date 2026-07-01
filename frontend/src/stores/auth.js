import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import authService from '@/services/auth.service'

export const useAuthStore = defineStore('auth', () => {
  // ── State ──────────────────────────────────────────────────────────────
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const accessToken = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)

  // ── Getters ────────────────────────────────────────────────────────────
  const isAuthenticated = computed(() => !!accessToken.value)
  const userRole = computed(() => user.value?.role ?? null)
  const fullName = computed(() => user.value?.full_name ?? '')

  // ── Actions ────────────────────────────────────────────────────────────
async function login(email, password) {
  try {
    const response = await authService.login(email, password)

    _setSession(response.tokens, response.user)

    return response
  } catch (error) {
    throw new Error(
      error.response?.data?.message || 'Invalid email or password.'
    )
  }
}

async function register(userData) {
  try {
    const response = await authService.register(userData)

    return response
  } catch (error) {
    throw new Error(
      error.response?.data?.message || 'Registration failed.'
    )
  }
}

  async function logout() {
    // TODO: call authService.logout()
    _clearSession()
  }

  async function fetchCurrentUser() {
    // TODO: call authService.me()
    throw new Error('fetchCurrentUser not yet implemented')
  }

  function _setSession(tokens, userData) {
    accessToken.value = tokens.access_token
    refreshToken.value = tokens.refresh_token
    user.value = userData
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  function _clearSession() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  return {
    user,
    accessToken,
    isAuthenticated,
    userRole,
    fullName,
    login,
    register,
    logout,
    fetchCurrentUser,
  }
})
