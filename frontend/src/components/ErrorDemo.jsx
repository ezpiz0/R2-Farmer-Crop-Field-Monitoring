import React from 'react'
import ErrorPage from './ErrorPage'

// Компонент для демонстрации разных типов ошибок
function ErrorDemo() {
  const [errorType, setErrorType] = React.useState(null)

  if (errorType) {
    return <ErrorPage errorCode={errorType} />
  }

  return (
    <div style={{ 
      padding: '40px', 
      textAlign: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <h1 style={{ color: 'white', marginBottom: '40px' }}>Демонстрация страниц ошибок</h1>
      <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', flexWrap: 'wrap' }}>
        <button 
          onClick={() => setErrorType('404')}
          style={{
            padding: '20px 40px',
            fontSize: '18px',
            background: '#FF6B6B',
            color: 'white',
            border: 'none',
            borderRadius: '12px',
            cursor: 'pointer',
            fontWeight: '600'
          }}
        >
          Показать ошибку 404
        </button>
        <button 
          onClick={() => setErrorType('500')}
          style={{
            padding: '20px 40px',
            fontSize: '18px',
            background: '#4ECDC4',
            color: 'white',
            border: 'none',
            borderRadius: '12px',
            cursor: 'pointer',
            fontWeight: '600'
          }}
        >
          Показать ошибку 500
        </button>
        <button 
          onClick={() => setErrorType('403')}
          style={{
            padding: '20px 40px',
            fontSize: '18px',
            background: '#F7B731',
            color: 'white',
            border: 'none',
            borderRadius: '12px',
            cursor: 'pointer',
            fontWeight: '600'
          }}
        >
          Показать ошибку 403
        </button>
      </div>
    </div>
  )
}

export default ErrorDemo

