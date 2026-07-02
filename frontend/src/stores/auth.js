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
  const adminLevel = computed(() => user.value?.admin_level ?? null)
  const cityName = computed(() => user.value?.city_name ?? null)
  const isSystemAdmin = computed(() => userRole.value === 'administrator' && adminLevel.value === 'system')
  const isMunicipalAdmin = computed(() => userRole.value === 'administrator' && adminLevel.value === 'municipal')
  const fullName = computed(() => user.value?.full_name ?? '')
  const isHydrated = ref(false)
  let hydrationPromise = null

  // ── Actions ────────────────────────────────────────────────────────────
  async function login(email, password) {
    try {
      const response = await authService.login(email, password)
      if (!response?.success || !response?.data?.access_token || !response?.data?.refresh_token || !response?.data?.user) {
        throw new Error(response?.message || 'Login failed.')
      }

      _setSession(response.data, response.data.user)
      isHydrated.value = true
      return response.data.user
    } catch (error) {
      _clearSession()
      throw _toUserFriendlyError(error, 'Login failed. Please check your credentials.')
    }
  }

  async function register(userData) {
    try {
      const response = await authService.register(userData)
      if (!response?.success) {
        throw new Error(response?.message || 'Registration failed.')
      }
      return response.data?.user || null
    } catch (error) {
      throw _toUserFriendlyError(error, 'Registration failed.')
    }
  }

  async function logout() {
    let logoutError = null
    try {
      if (accessToken.value) {
        await authService.logout()
      }
    } catch (error) {
      logoutError = _toUserFriendlyError(error, 'Logout failed.')
    }
    _clearSession()
    isHydrated.value = true
    if (logoutError) {
      throw logoutError
    }
  }

  async function fetchCurrentUser() {
    if (!accessToken.value) {
      _clearSession()
      return null
    }

    try {
      const response = await authService.me()
      if (!response?.success || !response?.data?.user) {
        throw new Error(response?.message || 'Failed to load user profile.')
      }

      user.value = response.data.user
      localStorage.setItem('user', JSON.stringify(response.data.user))
      return response.data.user
    } catch (error) {
      _clearSession()
      throw _toUserFriendlyError(error, 'Session expired. Please sign in again.')
    }
  }

  async function hydrateSession() {
    if (isHydrated.value) {
      return
    }

    if (!hydrationPromise) {
      hydrationPromise = (async () => {
        try {
          await fetchCurrentUser()
        } catch {
          // fetchCurrentUser already clears invalid session state.
        } finally {
          isHydrated.value = true
          hydrationPromise = null
        }
      })()
    }

    await hydrationPromise
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

  function _toUserFriendlyError(error, fallbackMessage) {
    const message = error?.response?.data?.message || error?.message || fallbackMessage
    return new Error(message)
  }

  return {
    user,
    accessToken,
    isAuthenticated,
    userRole,
    adminLevel,
    cityName,
    isSystemAdmin,
    isMunicipalAdmin,
    fullName,
    isHydrated,
    login,
    register,
    logout,
    fetchCurrentUser,
    hydrateSession,
  }
})
