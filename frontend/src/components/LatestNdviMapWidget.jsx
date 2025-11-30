import React, { useState, useEffect } from 'react'
import api from '../utils/api'
import './DashboardWidget.css'

function LatestNdviMapWidget({ item, onDelete }) {
  const [imageUrl, setImageUrl] = useState(null)
  const [stats, setStats] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadLatestNdvi()
  }, [item])

  const loadLatestNdvi = async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Get latest data (last 7 days)
      const endDate = new Date().toISOString().split('T')[0]
      const startDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

      const response = await api.post('/api/v1/analyze', {
        geometry: item.field_geometry,
        date_range: [startDate, endDate],
        indices: [item.index_type || 'NDVI']
      })

      // Convert relative URL to absolute
      // baseURL теперь пустой, поэтому просто используем image_url напрямую
      setImageUrl(response.data.image_url)
      setStats(response.data.stats)
    } catch (err) {
      console.error('Error loading NDVI map:', err)
      setError('Ошибка загрузки карты NDVI')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="dashboard-widget">
      <div className="widget-header">
        <h3 className="widget-title">
          🗺️ {item.field_name} - {item.index_type || 'NDVI'}
        </h3>
        <div className="widget-actions">
          <button 
            className="widget-btn" 
            onClick={loadLatestNdvi}
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

      {stats && (
        <div className="widget-field-info">
          📅 {stats.capture_date} | NDVI: {stats.mean_ndvi.toFixed(3)}
        </div>
      )}

      <div className="widget-body">
        {isLoading && (
          <div className="widget-loading">
            <div className="spinner"></div>
            <p>Загрузка карты...</p>
          </div>
        )}

        {error && !isLoading && (
          <div className="widget-error">{error}</div>
        )}

        {imageUrl && !isLoading && (
          <div className="widget-map-container">
            <img 
              src={imageUrl} 
              alt={`NDVI карта для ${item.field_name}`}
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default LatestNdviMapWidget

