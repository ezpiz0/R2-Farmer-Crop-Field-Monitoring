import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import api from '../utils/api'
import Header from './Header'
import TimeSeriesWidget from './TimeSeriesWidget'
import FieldStatsWidget from './FieldStatsWidget'
import LatestNdviMapWidget from './LatestNdviMapWidget'
import './DashboardPage.css'

function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [dashboardItems, setDashboardItems] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadDashboardItems()
  }, [])

  const loadDashboardItems = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await api.get('/api/v1/dashboard/items')
      setDashboardItems(response.data)
    } catch (err) {
      console.error('Error loading dashboard items:', err)
      setError('Ошибка при загрузке элементов дашборда')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteItem = async (itemId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот элемент?')) {
      return
    }

    try {
      await api.delete(`/api/v1/dashboard/items/${itemId}`)
      setDashboardItems(dashboardItems.filter(item => item.id !== itemId))
    } catch (err) {
      console.error('Error deleting dashboard item:', err)
      alert('Ошибка при удалении элемента')
    }
  }

  const renderWidget = (item) => {
    const key = `widget-${item.id}`

    switch (item.item_type) {
      case 'time_series_chart':
        return <TimeSeriesWidget key={key} item={item} onDelete={handleDeleteItem} />
      case 'field_stats':
        return <FieldStatsWidget key={key} item={item} onDelete={handleDeleteItem} />
      case 'latest_ndvi_map':
        return <LatestNdviMapWidget key={key} item={item} onDelete={handleDeleteItem} />
      default:
        return (
          <div key={key} className="dashboard-widget">
            <div className="widget-header">
              <h3 className="widget-title">Неизвестный тип виджета</h3>
              <button 
                className="widget-btn widget-btn-delete" 
                onClick={() => handleDeleteItem(item.id)}
              >
                🗑️
              </button>
            </div>
          </div>
        )
    }
  }

  if (!user) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-container">
          <div className="auth-required">
            <h2>🔒 Требуется авторизация</h2>
            <p>Пожалуйста, войдите в систему, чтобы получить доступ к дашборду.</p>
            <button className="btn btn-primary" onClick={() => navigate('/auth')}>
              Войти
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      <Header />
      <div className="dashboard-page">
        <div className="dashboard-container">
        <div className="dashboard-header">
          <div className="dashboard-title-section">
            <h1>📊 Мой Дашборд</h1>
            <p className="dashboard-subtitle">
              Добро пожаловать, <strong>{user.email}</strong>!
            </p>
          </div>
          <div className="dashboard-actions">
            <button 
              className="btn btn-secondary" 
              onClick={loadDashboardItems}
              disabled={isLoading}
            >
              🔄 Обновить
            </button>
            <button 
              className="btn btn-primary" 
              onClick={() => navigate('/')}
            >
              🗺️ К карте
            </button>
          </div>
        </div>

        {isLoading && (
          <div className="dashboard-loading">
            <div className="spinner-large"></div>
            <p>Загрузка дашборда...</p>
          </div>
        )}

        {error && !isLoading && (
          <div className="dashboard-error">
            <h3>❌ Ошибка</h3>
            <p>{error}</p>
            <button className="btn btn-primary" onClick={loadDashboardItems}>
              Попробовать снова
            </button>
          </div>
        )}

        {!isLoading && !error && dashboardItems.length === 0 && (
          <div className="dashboard-empty">
            <div className="empty-state">
              <h2>📭 Дашборд пуст</h2>
              <p>У вас пока нет сохраненных анализов.</p>
              <div className="empty-instructions">
                <h3>Как добавить виджеты на дашборд:</h3>
                <ol>
                  <li>Перейдите на главную страницу карты</li>
                  <li>Нарисуйте поле на карте</li>
                  <li>Сохраните поле с помощью кнопки "💾 Сохранить поле"</li>
                  <li>Выполните анализ (NDVI или временной ряд)</li>
                  <li>Нажмите кнопку "📊 Добавить на дашборд"</li>
                </ol>
              </div>
              <button className="btn btn-primary btn-large" onClick={() => navigate('/')}>
                🗺️ Перейти к карте
              </button>
            </div>
          </div>
        )}

        {!isLoading && !error && dashboardItems.length > 0 && (
          <div className="dashboard-grid">
            {dashboardItems.map(renderWidget)}
          </div>
        )}
      </div>
    </div>
    </>
  )
}

export default DashboardPage

