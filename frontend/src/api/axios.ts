import axios from 'axios'

/**
 * Base URL strategy:
 *  - In Docker (production build): requests go to /api/ which nginx proxies to backend:8000
 *  - In local dev (npm run dev): Vite proxies /api/ to localhost:8000 via vite.config.ts
 *
 * The VITE_API_URL env var can override this for custom deployments.
 */
const BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: BASE_URL,
})

// Attach access token to every request
api.interceptors.request.use((config) => {
   
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Silent token refresh on 401
let isRefreshing = false
let pendingRequests: Array<(token: string) => void> = []

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Only attempt refresh once per failed request
    if (error.response?.status === 401 && !originalRequest._retried) {
      originalRequest._retried = true

      const refreshToken = localStorage.getItem('refresh_token')

      if (!refreshToken) {
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingRequests.push((newToken: string) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            resolve(api(originalRequest))
          })
        })
      }

      isRefreshing = true

      try {
        const res = await axios.post(`${BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        })

        const newAccessToken: string = res.data.access_token
        localStorage.setItem('token', newAccessToken)
        api.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`

        pendingRequests.forEach((cb) => cb(newAccessToken))
        pendingRequests = []

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return api(originalRequest)
      } catch {
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default api
