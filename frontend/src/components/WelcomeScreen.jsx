import React from 'react'
import './WelcomeScreen.css'

function WelcomeScreen({ onStart }) {
  return (
    <div className="welcome-screen">
      <div className="welcome-overlay" />
      
      <div className="welcome-content">
        <div className="welcome-logo">
          <img src="/farmer-bot.png" alt="R2-Фермер" className="welcome-logo-img" />
        </div>
        
        <h1 className="welcome-title">R2-Фермер</h1>
        
        <p className="welcome-subtitle">
          Мониторинг здоровья сельскохозяйственных полей
          <br />
          на основе спутниковых данных Sentinel-2
        </p>
        
        <div className="welcome-features">
          <div className="feature-item">
            <span className="feature-icon">🛰️</span>
            <span className="feature-text">Реальные данные со спутников</span>
          </div>
          
          <div className="feature-item">
            <span className="feature-icon">📊</span>
            <span className="feature-text">Анализ вегетационных индексов</span>
          </div>
          
          <div className="feature-item">
            <span className="feature-icon">📈</span>
            <span className="feature-text">Динамика состояния полей</span>
          </div>
        </div>
        
        <button className="welcome-btn" onClick={onStart}>
          <span>Начать работу</span>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M7.5 15L12.5 10L7.5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
        
        <div className="welcome-footer">
          <p className="powered-by">Powered by <span className="brand">R² negative</span></p>
          <p className="api-info">Sentinel Hub API</p>
        </div>
      </div>
    </div>
  )
}

export default WelcomeScreen

