import React, { useState } from 'react'
import LoginForm from './LoginForm'
import RegisterForm from './RegisterForm'

function AuthPage() {
  const [showLogin, setShowLogin] = useState(true)
  const [successMessage, setSuccessMessage] = useState('')

  const handleRegisterSuccess = () => {
    setSuccessMessage('Регистрация успешна! Теперь вы можете войти.')
    setShowLogin(true)
    setTimeout(() => setSuccessMessage(''), 5000)
  }

  return (
    <div style={{ position: 'relative' }}>
      {successMessage && (
        <div style={{
          position: 'fixed',
          top: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: '#4caf50',
          color: 'white',
          padding: '16px 24px',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          zIndex: 9999,
          fontSize: '14px',
          fontWeight: 500
        }}>
          {successMessage}
        </div>
      )}

      {showLogin ? (
        <LoginForm 
          onSwitchToRegister={() => setShowLogin(false)}
        />
      ) : (
        <RegisterForm 
          onSuccess={handleRegisterSuccess}
          onSwitchToLogin={() => setShowLogin(true)}
        />
      )}
    </div>
  )
}

export default AuthPage

