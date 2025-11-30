import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import './RegisterForm.css'

function RegisterForm({ onSuccess, onSwitchToLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { register } = useAuth()

  const validateForm = () => {
    if (password.length < 8) {
      setError('Пароль должен содержать минимум 8 символов')
      return false
    }

    if (!/\d/.test(password)) {
      setError('Пароль должен содержать хотя бы одну цифру')
      return false
    }

    if (!/[a-zA-Z]/.test(password)) {
      setError('Пароль должен содержать хотя бы одну букву')
      return false
    }

    if (password !== confirmPassword) {
      setError('Пароли не совпадают')
      return false
    }

    return true
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!validateForm()) {
      return
    }

    setLoading(true)

    const result = await register(email, password)
    
    if (result.success) {
      if (onSuccess) onSuccess()
    } else {
      setError(result.error)
    }
    
    setLoading(false)
  }

  return (
    <div className="register-form-container">
      <div className="register-form-card">
        <div className="register-form-header">
          <h2>Регистрация</h2>
          <p>Создайте аккаунт для доступа к R2-Фермер</p>
        </div>

        <form onSubmit={handleSubmit} className="register-form">
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
              placeholder="Минимум 8 символов"
              required
              disabled={loading}
            />
            <small className="form-hint">
              Пароль должен содержать минимум 8 символов, включая буквы и цифры
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Подтверждение пароля</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Повторите пароль"
              required
              disabled={loading}
            />
          </div>

          <button 
            type="submit" 
            className="register-button"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Регистрация...
              </>
            ) : (
              'Зарегистрироваться'
            )}
          </button>
        </form>

        <div className="register-form-footer">
          <p>
            Уже есть аккаунт?{' '}
            <button 
              className="link-button" 
              onClick={onSwitchToLogin}
              disabled={loading}
            >
              Войти
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}

export default RegisterForm

