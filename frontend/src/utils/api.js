import axios from 'axios'

// Create axios instance with dynamic baseURL
// Пустой baseURL означает, что запросы идут на текущий домен
// Это позволяет работать как на localhost, так и через ngrok
const api = axios.create({
  baseURL: '', // Запросы идут на текущий домен (работает везде!)
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token')
      // Optionally redirect to login
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

export default api

