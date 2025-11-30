import React from 'react'
import { useAuth } from '../contexts/AuthContext'

function PrivateRoute({ children, fallback }) {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '18px',
        color: 'var(--text-secondary)'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div className="spinner" style={{
            width: '40px',
            height: '40px',
            border: '3px solid var(--border-light)',
            borderTopColor: 'var(--primary-green)',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          <p>Загрузка...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return fallback || null
  }

  return children
}

export default PrivateRoute

