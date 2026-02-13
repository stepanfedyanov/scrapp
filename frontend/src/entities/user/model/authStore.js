import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '~/src/shared/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('accessToken') || '')
  const refreshToken = ref(localStorage.getItem('refreshToken') || '')

  const isAuthenticated = computed(() => Boolean(accessToken.value))

  const setTokens = (access, refresh) => {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('accessToken', access)
    localStorage.setItem('refreshToken', refresh)
  }

  const login = async ({ username, password }) => {
    const { data } = await api.post('/auth/token/', { username, password })
    setTokens(data.access, data.refresh)
  }

  const register = async ({ username, email, password }) => {
    await api.post('/auth/register/', { username, email, password })
  }

  const logout = () => {
    user.value = null
    accessToken.value = ''
    refreshToken.value = ''
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
  }

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    setTokens,
    login,
    register,
    logout
  }
})
