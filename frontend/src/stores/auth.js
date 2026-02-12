import { defineStore } from 'pinia'
import api from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: localStorage.getItem('accessToken') || '',
    refreshToken: localStorage.getItem('refreshToken') || ''
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken)
  },
  actions: {
    setTokens(access, refresh) {
      this.accessToken = access
      this.refreshToken = refresh
      localStorage.setItem('accessToken', access)
      localStorage.setItem('refreshToken', refresh)
    },
    async login({ username, password }) {
      const { data } = await api.post('/auth/token/', { username, password })
      this.setTokens(data.access, data.refresh)
    },
    async register({ username, email, password }) {
      await api.post('/auth/register/', { username, email, password })
    },
    logout() {
      this.user = null
      this.accessToken = ''
      this.refreshToken = ''
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
    }
  }
})
