import React from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

function Header() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    if (window.confirm('Вы уверены, что хотите выйти?')) {
      logout()
      navigate('/auth')
    }
  }

  const isMapPage = location.pathname === '/map'
  const isDashboard = location.pathname === '/dashboard'
  const isProfile = location.pathname === '/profile'

  return (
    <header className="header">
      <div className="header-content">
        <Link to="/" className="header-logo-link">
          <div className="header-logo">
            <img src="/farmer-bot.png" alt="R2-Фермер" className="header-logo-img" />
          </div>
          <div className="header-text">
            <h1>R2-Фермер</h1>
            <p>Мониторинг сельскохозяйственных полей</p>
          </div>
        </Link>
        
        <div className="header-actions">
          <Link 
            to="/" 
            className={`nav-button ${location.pathname === '/' ? 'active' : ''}`}
            title="Главная"
          >
            🏠 Главная
          </Link>
          
          <Link 
            to="/map" 
            className={`nav-button ${isMapPage ? 'active' : ''}`}
            title="Карта"
          >
            🗺️ Карта
          </Link>
          
          <Link 
            to="/dashboard" 
            className={`nav-button ${isDashboard ? 'active' : ''}`}
            title="Дашборд"
          >
            📊 Дашборд
          </Link>
          
          <Link 
            to="/profile" 
            className={`nav-button ${isProfile ? 'active' : ''}`}
            title="Профиль"
          >
            👤 Профиль
          </Link>
          
          <button className="logout-button" onClick={handleLogout} title="Выйти">
            Выйти
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header



