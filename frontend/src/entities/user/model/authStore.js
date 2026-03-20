import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '~/src/shared/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('accessToken') || '')
  const refreshToken = ref(localStorage.getItem('refreshToken') || '')

  const isAuthenticated = computed(() => Boolean(accessToken.value))
  const canUseAI = computed(() => Boolean(user.value?.can_use_ai))

  const setTokens = (access, refresh) => {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('accessToken', access)
    localStorage.setItem('refreshToken', refresh)
  }

  const fetchUser = async () => {
    const { data } = await api.get('/auth/me/')
    user.value = data
  }

  const login = async ({ username, password }) => {
    const { data } = await api.post('/auth/token/', { username, password })
    setTokens(data.access, data.refresh)
    await fetchUser()
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
    canUseAI,
    setTokens,
    fetchUser,
    login,
    register,
    logout
  }
})
