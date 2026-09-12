import axios from 'axios'

const client = axios.create({ baseURL: '/api/' })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true
      const { useAuthStore } = await import('../stores/auth')
      const authStore = useAuthStore()
      const refreshed = await authStore.refreshAccessToken()
      if (refreshed) {
        originalRequest.headers.Authorization = `Bearer ${authStore.accessToken}`
        return client(originalRequest)
      }
      authStore.logout()
    }
    return Promise.reject(error)
  },
)

export default client
