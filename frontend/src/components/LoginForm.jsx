import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import './LoginForm.css'

function LoginForm({ onSuccess, onSwitchToRegister }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { login } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const result = await login(email, password)
    
    if (result.success) {
      if (onSuccess) onSuccess()
    } else {
      setError(result.error)
    }
    
    setLoading(false)
  }

  return (
    <div className="login-form-container">
      <div className="login-form-card">
        <div className="login-form-header">
          <h2>Вход в систему</h2>
          <p>Войдите, чтобы продолжить работу</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <div className="form-error">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Пароль</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Введите пароль"
              required
              disabled={loading}
            />
          </div>

          <button 
            type="submit" 
            className="login-button"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Вход...
              </>
            ) : (
              'Войти'
            )}
          </button>
        </form>

        <div className="login-form-footer">
          <p>
            Нет аккаунта?{' '}
            <button 
              className="link-button" 
              onClick={onSwitchToRegister}
              disabled={loading}
            >
              Зарегистрироваться
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginForm

