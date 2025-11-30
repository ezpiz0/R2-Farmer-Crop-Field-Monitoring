import React from 'react'
import { Link } from 'react-router-dom'
import './HomePage.css'

function HomePage() {
  const cards = [
    {
      id: 'map',
      title: 'Анализ полей',
      description: 'Выберите поле на карте и получите детальный анализ состояния посевов',
      icon: '🗺️',
      link: '/map',
      color: '#10b981'
    },
    {
      id: 'dashboard',
      title: 'Мой дашборд',
      description: 'Просматривайте сохраненные анализы и отслеживайте динамику',
      icon: '📊',
      link: '/dashboard',
      color: '#3b82f6'
    },
    {
      id: 'profile',
      title: 'Личный кабинет',
      description: 'Управляйте своим профилем и настройками аккаунта',
      icon: '👤',
      link: '/profile',
      color: '#8b5cf6'
    }
  ]

  return (
    <div className="home-page">
      <div className="home-header">
        <h1 className="home-title">
          <img src="/farmer-bot.png" alt="R2-Фермер" className="home-icon-img" />
          R2-Фермер
        </h1>
        <p className="home-subtitle">
          Система мониторинга сельскохозяйственных полей на основе спутниковых данных Sentinel-2
        </p>
      </div>

      <div className="home-cards">
        {cards.map((card) => (
          <Link 
            key={card.id} 
            to={card.link} 
            className="home-card"
            style={{ '--card-color': card.color }}
          >
            <div className="card-icon">{card.icon}</div>
            <h2 className="card-title">{card.title}</h2>
            <p className="card-description">{card.description}</p>
            <div className="card-arrow">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path 
                  d="M5 12h14m-7-7l7 7-7 7" 
                  stroke="currentColor" 
                  strokeWidth="2" 
                  strokeLinecap="round" 
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </Link>
        ))}
      </div>

      <div className="home-features">
        <h3>Возможности системы</h3>
        <div className="features-grid">
          <div className="feature-item">
            <span className="feature-emoji">🛰️</span>
            <span>Спутниковые данные Sentinel-2</span>
          </div>
          <div className="feature-item">
            <span className="feature-emoji">📈</span>
            <span>Вегетационные индексы (NDVI, EVI)</span>
          </div>
          <div className="feature-item">
            <span className="feature-emoji">📅</span>
            <span>Временные ряды и динамика</span>
          </div>
          <div className="feature-item">
            <span className="feature-emoji">💾</span>
            <span>Сохранение анализов</span>
          </div>
          <div className="feature-item">
            <span className="feature-emoji">📥</span>
            <span>Экспорт данных (PNG, CSV)</span>
          </div>
          <div className="feature-item">
            <span className="feature-emoji">🎨</span>
            <span>Визуализация карт</span>
          </div>
        </div>
      </div>

      <div className="home-footer">
        <p>Powered by <span className="brand">R² negative</span></p>
      </div>
    </div>
  )
}

export default HomePage

