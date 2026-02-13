import axios from 'axios'
import { useAuthStore } from '~/src/entities/user'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api'
})

api.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const auth = useAuthStore()
    if (error.response?.status === 401 && auth.refreshToken) {
      try {
        const { data } = await axios.post(
          `${import.meta.env.VITE_API_URL || '/api'}/auth/refresh/`,
          { refresh: auth.refreshToken }
        )
        auth.setTokens(data.access, auth.refreshToken)
        error.config.headers.Authorization = `Bearer ${data.access}`
        return api.request(error.config)
      } catch {
        auth.logout()
      }
    }
    return Promise.reject(error)
  }
)

export default api
