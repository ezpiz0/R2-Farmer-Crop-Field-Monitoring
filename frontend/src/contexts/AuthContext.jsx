import React, { createContext, useState, useContext, useEffect } from 'react'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Check if user is already logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token')
      
      if (token) {
        try {
        const response = await fetch('/api/v1/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

          if (response.ok) {
            const data = await response.json()
            setUser(data)
            setIsAuthenticated(true)
          } else {
            // Token is invalid, remove it
            localStorage.removeItem('access_token')
          }
        } catch (err) {
          console.error('Error checking authentication:', err)
          localStorage.removeItem('access_token')
        }
      }
      
      setLoading(false)
    }

    checkAuth()
  }, [])

  const register = async (email, password) => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed')
      }

      setLoading(false)
      return { success: true, message: data.message }
    } catch (err) {
      setError(err.message)
      setLoading(false)
      return { success: false, error: err.message }
    }
  }

  const login = async (email, password) => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed')
      }

      // Save token to localStorage
      localStorage.setItem('access_token', data.access_token)

      // Fetch user data
      const userResponse = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      })

      if (userResponse.ok) {
        const userData = await userResponse.json()
        setUser(userData)
        setIsAuthenticated(true)
      }

      setLoading(false)
      return { success: true, message: data.message }
    } catch (err) {
      setError(err.message)
      setLoading(false)
      return { success: false, error: err.message }
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    setUser(null)
    setIsAuthenticated(false)
    setError(null)
  }

  const value = {
    user,
    isAuthenticated,
    loading,
    error,
    register,
    login,
    logout
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export default AuthContext

