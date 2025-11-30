import React, { useEffect } from 'react'
import './ErrorNotification.css'

function ErrorNotification({ message, onClose, type = 'error' }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose()
    }, 5000)

    return () => clearTimeout(timer)
  }, [onClose])

  const getIcon = () => {
    switch (type) {
      case 'error':
        return '😢'
      case 'warning':
        return '⚠️'
      case 'info':
        return 'ℹ️'
      default:
        return '😢'
    }
  }

  return (
    <div className={`error-notification ${type}`}>
      <div className="error-notification-content">
        <div className="error-notification-icon">{getIcon()}</div>
        <div className="error-notification-message">
          <div className="error-notification-title">
            {type === 'error' ? 'Ой! Что-то пошло не так...' : 'Внимание!'}
          </div>
          <div className="error-notification-text">{message}</div>
        </div>
        <button className="error-notification-close" onClick={onClose}>
          ✕
        </button>
      </div>
      <div className="error-notification-progress"></div>
    </div>
  )
}

export default ErrorNotification

