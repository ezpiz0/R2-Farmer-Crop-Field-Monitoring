import React, { useState, useEffect } from 'react'
import api from '../utils/api'
import './DashboardWidget.css'

function FieldStatsWidget({ item, onDelete }) {
  const [stats, setStats] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadFieldStats()
  }, [item])

  const loadFieldStats = async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Get current date range (last 30 days)
      const endDate = new Date().toISOString().split('T')[0]
      const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

      const response = await api.post('/api/v1/analyze', {
        geometry: item.field_geometry,
        date_range: [startDate, endDate],
        indices: ['NDVI']
      })

      setStats(response.data.stats)
    } catch (err) {
      console.error('Error loading field stats:', err)
      setError('Ошибка загрузки статистики поля')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="dashboard-widget">
      <div className="widget-header">
        <h3 className="widget-title">
          📊 {item.field_name} - Статистика
        </h3>
        <div className="widget-actions">
          <button 
            className="widget-btn" 
            onClick={loadFieldStats}
            title="Обновить"
          >
            🔄
          </button>
          <button 
            className="widget-btn widget-btn-delete" 
            onClick={() => onDelete(item.id)}
            title="Удалить"
          >
            🗑️
          </button>
        </div>
      </div>

      <div className="widget-body">
        {isLoading && (
          <div className="widget-loading">
            <div className="spinner"></div>
            <p>Загрузка статистики...</p>
          </div>
        )}

        {error && !isLoading && (
          <div className="widget-error">{error}</div>
        )}

        {stats && !isLoading && (
          <div className="widget-stats">
            <div className="stat-item">
              <div className="stat-label">Площадь</div>
              <div className="stat-value">{stats.area_ha.toFixed(2)} га</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Средний NDVI</div>
              <div className="stat-value">{stats.mean_ndvi.toFixed(3)}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Дата съемки</div>
              <div className="stat-value" style={{ fontSize: '14px' }}>{stats.capture_date}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Облачность</div>
              <div className="stat-value">{stats.cloud_coverage_percent.toFixed(1)}%</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default FieldStatsWidget

