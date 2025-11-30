import React, { useState } from 'react'
import api from '../utils/api'
import SaveFieldButton from './SaveFieldButton'
import AddToDashboardButton from './AddToDashboardButton'

const VEGETATION_INDICES = {
  NDVI: {
    name: 'NDVI',
    description: 'Нормализованный разностный вегетационный индекс',
    detail: 'Основной индекс для оценки здоровья растений',
    disabled: true // NDVI всегда включен
  },
  EVI: {
    name: 'EVI',
    description: 'Улучшенный вегетационный индекс',
    detail: 'Более чувствителен к густой растительности'
  },
  PSRI: {
    name: 'PSRI',
    description: 'Индекс старения растений',
    detail: 'Для определения созревания и стресса'
  },
  NBR: {
    name: 'NBR',
    description: 'Нормализованный индекс гари',
    detail: 'Для мониторинга пожаров и повреждений'
  },
  NDSI: {
    name: 'NDSI',
    description: 'Нормализованный снежный индекс',
    detail: 'Для обнаружения снега и льда'
  }
}

function Sidebar({ 
  selectedGeometry, 
  analysisResult, 
  isAnalyzing,
  onAnalysisStart,
  onAnalysisComplete,
  onAnalysisError,
  onClearSelection,
  onOpenTimeSeries,
  onOpenAIPanel
}) {
  const [dateRange, setDateRange] = useState({
    start: getDefaultStartDate(),
    end: getDefaultEndDate()
  })
  const [selectedIndices, setSelectedIndices] = useState(['NDVI'])
  const [error, setError] = useState(null)

  function getDefaultStartDate() {
    const date = new Date()
    date.setDate(1) // First day of current month
    return date.toISOString().split('T')[0]
  }

  function getDefaultEndDate() {
    return new Date().toISOString().split('T')[0]
  }

  const handleIndexToggle = (indexName) => {
    if (indexName === 'NDVI') return // NDVI always included
    
    setSelectedIndices(prev => {
      if (prev.includes(indexName)) {
        return prev.filter(idx => idx !== indexName)
      } else {
        return [...prev, indexName]
      }
    })
  }

  const handleAnalyze = async () => {
    if (!selectedGeometry) {
      setError('Пожалуйста, нарисуйте область для анализа на карте')
      return
    }

    setError(null)
    onAnalysisStart()

    try {
      const response = await api.post('/api/v1/analyze', {
        geometry: selectedGeometry,
        date_range: [dateRange.start, dateRange.end],
        indices: selectedIndices
      })

      onAnalysisComplete(response.data)
    } catch (err) {
      console.error('Analysis failed:', err)
      setError(
        err.response?.data?.detail || 
        'Произошла ошибка при анализе. Пожалуйста, попробуйте снова.'
      )
      onAnalysisError()
    }
  }

  return (
    <div className="sidebar">
      {/* Controls Section */}
      <div className="sidebar-section">
        <h2>Параметры анализа</h2>
        
        <div className="draw-instructions">
          <strong>Инструкция:</strong>
          Используйте инструменты рисования на карте (справа вверху) для выбора области поля
        </div>

        <div className="controls">
          <div className="control-group">
            <label>Дата начала</label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
              max={dateRange.end}
            />
          </div>

          <div className="control-group">
            <label>Дата окончания</label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
              min={dateRange.start}
              max={getDefaultEndDate()}
            />
          </div>

          <div className="control-group">
            <label>Дополнительные индексы</label>
            <div className="indices-selector">
              {Object.entries(VEGETATION_INDICES).map(([key, index]) => (
                <div key={key} className="index-checkbox">
                  <label>
                    <input
                      type="checkbox"
                      checked={selectedIndices.includes(key)}
                      disabled={index.disabled}
                      onChange={() => handleIndexToggle(key)}
                    />
                    <span className="index-name">{index.name}</span>
                    <span className="index-description">{index.description}</span>
                    <small className="index-detail">{index.detail}</small>
                  </label>
                </div>
              ))}
            </div>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleAnalyze}
            disabled={!selectedGeometry || isAnalyzing}
          >
            {isAnalyzing ? 'Анализ...' : 'Анализировать поле'}
          </button>

          {selectedGeometry && (
            <button
              className="btn btn-secondary"
              onClick={onClearSelection}
            >
              Очистить выбор
            </button>
          )}
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {!selectedGeometry && !error && (
          <div className="info-message">
            Нарисуйте полигон на карте, чтобы начать анализ
          </div>
        )}
      </div>

      {/* Loading State */}
      {isAnalyzing && (
        <div className="sidebar-section">
          <div className="loading">
            <div className="spinner"></div>
            <p>Обработка спутниковых данных...</p>
          </div>
        </div>
      )}

      {/* Results Section */}
      {analysisResult && !isAnalyzing && (
        <>
          <div className="sidebar-section">
            <h2>Статистика поля</h2>
            
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Площадь</div>
                <div className="stat-value">
                  {analysisResult.stats.area_ha.toFixed(1)}
                  <span className="stat-unit">га</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Средний NDVI</div>
                <div className="stat-value">
                  {analysisResult.stats.mean_ndvi.toFixed(3)}
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Дата съемки</div>
                <div className="stat-value" style={{ fontSize: '1rem' }}>
                  {analysisResult.stats.capture_date}
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Облачность</div>
                <div className="stat-value">
                  {analysisResult.stats.cloud_coverage_percent.toFixed(1)}
                  <span className="stat-unit">%</span>
                </div>
              </div>
            </div>

            <div className="info-message" style={{ marginTop: '1rem' }}>
              Валидных пикселей: {analysisResult.stats.valid_pixels_percent.toFixed(1)}%
            </div>
          </div>

          <div className="sidebar-section">
            <h2>Распределение зон</h2>
            
            <div className="zones-chart">
              {Object.entries(analysisResult.stats.zones_percent).map(([zone, percent]) => {
                const colors = {
                  'low (<0.3)': '#FFD700',
                  'medium (0.3-0.6)': '#ADFF2F',
                  'high (>0.6)': '#228B22'
                }
                
                return (
                  <div key={zone} className="zone-item">
                    <div className="zone-info">
                      <div 
                        className="zone-color" 
                        style={{ background: colors[zone] }}
                      ></div>
                      <span className="zone-label">{zone}</span>
                    </div>
                    <span className="zone-value">{percent.toFixed(1)}%</span>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="sidebar-section">
            <h2>Интерпретация</h2>
            <div style={{ fontSize: '0.9rem', lineHeight: '1.6', color: '#555' }}>
              {getInterpretation(analysisResult.stats.mean_ndvi)}
            </div>
          </div>

          {/* Additional Indices Section */}
          {analysisResult.additional_indices && Object.keys(analysisResult.additional_indices).length > 0 && (
            <div className="sidebar-section">
              <h2>Дополнительные индексы</h2>
              
              {Object.entries(analysisResult.additional_indices).map(([indexName, imageUrl]) => (
                <div key={indexName} className="additional-index-item">
                  <h3 className="index-title">{VEGETATION_INDICES[indexName]?.name || indexName}</h3>
                  <p className="index-desc">{VEGETATION_INDICES[indexName]?.description}</p>
                  
                  {/* Show image */}
                  <div className="index-image">
                    <img 
                      src={imageUrl} 
                      alt={`${indexName} visualization`}
                      style={{ width: '100%', borderRadius: '8px', marginTop: '0.5rem' }}
                    />
                  </div>
                  
                  {/* Show stats if available */}
                  {analysisResult.stats.indices_stats && analysisResult.stats.indices_stats[indexName] && (
                    <div className="index-stats">
                      <div className="stat-row">
                        <span className="stat-label-small">Среднее:</span>
                        <span className="stat-value-small">{analysisResult.stats.indices_stats[indexName].mean.toFixed(3)}</span>
                      </div>
                      <div className="stat-row">
                        <span className="stat-label-small">Мин:</span>
                        <span className="stat-value-small">{analysisResult.stats.indices_stats[indexName].min.toFixed(3)}</span>
                      </div>
                      <div className="stat-row">
                        <span className="stat-label-small">Макс:</span>
                        <span className="stat-value-small">{analysisResult.stats.indices_stats[indexName].max.toFixed(3)}</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}
      
      {/* AI Agronomist Button */}
      {analysisResult && (
        <div className="sidebar-section" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', borderRadius: '12px', padding: '1.5rem' }}>
          <h2 style={{ color: 'white', display: 'flex', alignItems: 'center', gap: '8px' }}>
            🤖 AI Агроном
          </h2>
          <p className="section-description" style={{ color: 'rgba(255,255,255,0.9)' }}>
            Получите персонализированные рекомендации на основе анализа данных вашего поля
          </p>
          <button
            className="btn btn-primary"
            onClick={onOpenAIPanel}
            style={{ 
              width: '100%',
              background: 'white',
              color: '#667eea',
              fontWeight: 'bold',
              border: 'none',
              marginTop: '12px'
            }}
          >
            Открыть AI Агроном
          </button>
        </div>
      )}

      {/* Time Series Analysis Button */}
      <div className="sidebar-section">
        <h2>📈 Анализ динамики</h2>
        <p className="section-description">
          Отслеживайте изменение вегетационных индексов во времени
        </p>
        <button
          className="btn btn-secondary"
          onClick={onOpenTimeSeries}
          disabled={!selectedGeometry}
          style={{ width: '100%' }}
        >
          Открыть анализ динамики
        </button>
        {!selectedGeometry && (
          <p className="info-message" style={{ marginTop: '12px' }}>
            ℹ️ Сначала выберите область на карте
          </p>
        )}
      </div>

      {/* Save Field and Dashboard Actions */}
      <div className="sidebar-section">
        <h2>💾 Сохранение и Дашборд</h2>
        <p className="section-description">
          Сохраните поле и добавьте анализ на персональный дашборд
        </p>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <SaveFieldButton 
            geometry={selectedGeometry}
            onFieldSaved={(field) => {
              console.log('Field saved:', field)
            }}
          />
          
          {analysisResult && (
            <AddToDashboardButton 
              geometry={selectedGeometry}
              analysisParams={{
                startDate: dateRange.start,
                endDate: dateRange.end,
                indexType: 'NDVI'
              }}
              itemType="field_stats"
              onAdded={(item) => {
                console.log('Added to dashboard:', item)
              }}
            />
          )}
        </div>
        
        {!selectedGeometry && (
          <p className="info-message" style={{ marginTop: '12px' }}>
            ℹ️ Нарисуйте поле на карте, чтобы сохранить его
          </p>
        )}
      </div>
    </div>
  )
}

function getInterpretation(meanNDVI) {
  if (meanNDVI < 0.2) {
    return 'Очень низкие показатели вегетации. Возможно, поле находится под паром, недавно вспахано или покрыто водой.'
  } else if (meanNDVI < 0.4) {
    return 'Низкая вегетация. Растения могут находиться в стрессовом состоянии или на ранней стадии роста. Рекомендуется проверить условия выращивания.'
  } else if (meanNDVI < 0.6) {
    return 'Средние показатели вегетации. Растения развиваются нормально, но есть потенциал для улучшения здоровья культур.'
  } else {
    return 'Отличные показатели! Высокая плотность здоровой растительности. Поле находится в хорошем состоянии.'
  }
}

export default Sidebar



