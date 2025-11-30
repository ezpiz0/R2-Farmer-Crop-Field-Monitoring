import React, { useState, useEffect, useRef } from 'react'
import api from '../utils/api'
import aiService from '../utils/aiService'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import SaveFieldButton from './SaveFieldButton'
import AddToDashboardButton from './AddToDashboardButton'
import './TimeSeriesModal.css'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

const VEGETATION_INDICES_OPTIONS = [
  { value: 'NDVI', label: 'NDVI - Нормализованный вегетационный индекс', color: '#22c55e', bgColor: 'rgba(34, 197, 94, 0.1)' },
  { value: 'EVI', label: 'EVI - Улучшенный вегетационный индекс', color: '#3b82f6', bgColor: 'rgba(59, 130, 246, 0.1)' },
  { value: 'PSRI', label: 'PSRI - Индекс старения растений', color: '#f59e0b', bgColor: 'rgba(245, 158, 11, 0.1)' },
  { value: 'NBR', label: 'NBR - Нормализованный индекс гари', color: '#ef4444', bgColor: 'rgba(239, 68, 68, 0.1)' },
  { value: 'NDSI', label: 'NDSI - Нормализованный снежный индекс', color: '#06b6d4', bgColor: 'rgba(6, 182, 212, 0.1)' },
]

function TimeSeriesModal({ selectedGeometry, onClose }) {
  const chartRef = useRef(null)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [selectedIndices, setSelectedIndices] = useState(['NDVI']) // Multiple indices support
  const [chartData, setChartData] = useState(null)
  const [rawData, setRawData] = useState(null) // Store raw data for CSV export
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [forecastData, setForecastData] = useState(null) // ML Forecast data
  const [isForecastLoading, setIsForecastLoading] = useState(false)
  const [forecastHorizon, setForecastHorizon] = useState(30) // Forecast horizon in days
  const [showForecast, setShowForecast] = useState(false)

  useEffect(() => {
    // Set default dates to last 3 months
    const today = new Date()
    const threeMonthsAgo = new Date(today)
    threeMonthsAgo.setMonth(today.getMonth() - 3)

    setStartDate(threeMonthsAgo.toISOString().split('T')[0])
    setEndDate(today.toISOString().split('T')[0])
  }, [])

  const handleAnalyzeDynamics = async () => {
    if (!selectedGeometry) {
      setError('Пожалуйста, выберите область на карте.')
      return
    }

    if (!startDate || !endDate) {
      setError('Пожалуйста, выберите диапазон дат.')
      return
    }

    if (selectedIndices.length === 0) {
      setError('Пожалуйста, выберите хотя бы один индекс.')
      return
    }

    // Validate Sentinel-2 availability (launched June 23, 2015)
    const sentinel2Start = new Date('2015-06-23')
    const selectedStart = new Date(startDate)
    
    if (selectedStart < sentinel2Start) {
      setError('Данные Sentinel-2 доступны только с 23 июня 2015 года. Пожалуйста, выберите более позднюю дату начала.')
      return
    }

    // Warn if range is too large
    const daysDiff = Math.floor((new Date(endDate) - new Date(startDate)) / (1000 * 60 * 60 * 24))
    if (daysDiff > 365) {
      if (!window.confirm('Выбран большой диапазон дат (>1 года). Анализ может занять несколько минут. Продолжить?')) {
        return
      }
    }

    setError(null)
    setIsLoading(true)

    try {
      // Fetch data for all selected indices in parallel with extended timeout
      const requests = selectedIndices.map(indexType => 
        api.post('/api/v1/analyze/timeseries', {
          geometry: selectedGeometry,
          start_date: startDate,
          end_date: endDate,
          index_type: indexType,
        }, {
          timeout: 300000 // 5 minutes timeout for long time series
        })
      )

      const responses = await Promise.all(requests)
      const allData = responses.map(response => response.data)

      // Check if we have any data
      if (allData.length === 0 || allData[0].dates.length === 0) {
        setError('Нет данных за выбранный период.')
        setIsLoading(false)
        return
      }

      // Store raw data for CSV export (all indices)
      setRawData(allData)

      // Create datasets for each index with unique colors
      const datasets = allData.map((data, index) => {
        const indexConfig = VEGETATION_INDICES_OPTIONS.find(opt => opt.value === selectedIndices[index])
        return {
          label: indexConfig.label.split(' - ')[0], // Short name
          data: data.values,
          fill: true,
          backgroundColor: indexConfig.bgColor,
          borderColor: indexConfig.color,
          tension: 0.4, // Smoother curves
          pointRadius: 3,
          pointHoverRadius: 6,
          pointBackgroundColor: indexConfig.color,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          borderWidth: 3,
        }
      })

      setChartData({
        labels: allData[0].dates, // All should have same dates
        datasets: datasets,
      })
    } catch (err) {
      console.error('Error fetching time series data:', err)
      setError(err.response?.data?.detail || 'Ошибка при получении данных временного ряда. Убедитесь, что credentials Sentinel Hub настроены правильно.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleGenerateForecast = async () => {
    if (!rawData || rawData.length === 0 || !chartData) {
      setError('Сначала загрузите данные временного ряда')
      return
    }

    // Only forecast the first selected index for simplicity
    const indexToForecast = selectedIndices[0]
    const dataToForecast = rawData[0] // First index data

    // Prepare historical data in required format: [{date, value}, ...]
    const historicalData = dataToForecast.dates.map((date, index) => ({
      date: date,
      value: dataToForecast.values[index]
    }))

    // Validate minimum data points
    if (historicalData.length < 10) {
      setError('Недостаточно исторических данных. Требуется минимум 10 наблюдений для прогнозирования.')
      return
    }

    setIsForecastLoading(true)
    setError(null)

    try {
      const forecastResponse = await aiService.forecastTimeSeries(
        historicalData,
        indexToForecast,
        forecastHorizon
      )

      setForecastData(forecastResponse)
      setShowForecast(true)

      // Update chart to include forecast
      updateChartWithForecast(forecastResponse, indexToForecast)
    } catch (err) {
      console.error('Error generating forecast:', err)
      setError(err.message || 'Ошибка при генерации прогноза')
    } finally {
      setIsForecastLoading(false)
    }
  }

  const updateChartWithForecast = (forecastResponse, indexName) => {
    const indexConfig = VEGETATION_INDICES_OPTIONS.find(opt => opt.value === indexName)
    
    // Separate historical, interpolated, and forecast data
    const historicalPoints = forecastResponse.forecast.filter(p => p.type === 'Historical')
    const interpolatedPoints = forecastResponse.forecast.filter(p => p.type === 'Interpolated')
    const forecastPoints = forecastResponse.forecast.filter(p => p.type === 'Forecast')

    // Create datasets
    const newDatasets = []

    // Historical data dataset
    if (historicalPoints.length > 0) {
      newDatasets.push({
        label: `${indexName} (Исторические)`,
        data: historicalPoints.map(p => ({ x: p.date, y: p.value })),
        fill: false,
        backgroundColor: indexConfig.color,
        borderColor: indexConfig.color,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointStyle: 'circle',
        borderWidth: 3,
        tension: 0,
      })
    }

    // Interpolated data dataset (if any)
    if (interpolatedPoints.length > 0) {
      newDatasets.push({
        label: `${indexName} (Интерполированные)`,
        data: interpolatedPoints.map(p => ({ x: p.date, y: p.value })),
        fill: false,
        backgroundColor: '#9ca3af',
        borderColor: '#9ca3af',
        pointRadius: 3,
        pointHoverRadius: 5,
        pointStyle: 'crossRot',
        borderWidth: 2,
        borderDash: [5, 5],
        tension: 0.4,
      })
    }

    // Forecast data dataset
    if (forecastPoints.length > 0) {
      newDatasets.push({
        label: `${indexName} (Прогноз ML)`,
        data: forecastPoints.map(p => ({ x: p.date, y: p.value })),
        fill: true,
        backgroundColor: 'rgba(168, 85, 247, 0.1)',
        borderColor: '#a855f7',
        pointRadius: 4,
        pointHoverRadius: 6,
        pointStyle: 'rectRot',
        borderWidth: 3,
        borderDash: [10, 5],
        tension: 0.4,
      })
    }

    // Extract all dates for x-axis
    const allDates = forecastResponse.forecast.map(p => p.date)

    setChartData({
      labels: allDates,
      datasets: newDatasets,
    })
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: 'var(--text-color-primary)',
          font: {
            family: 'Inter, sans-serif',
            size: 14,
            weight: '500',
          },
          padding: 15,
          usePointStyle: true,
          pointStyle: 'circle',
        },
      },
      title: {
        display: true,
        text: `🛰️ Динамика вегетационных индексов (Sentinel-2)`,
        color: 'var(--text-color-primary)',
        font: {
          family: 'Inter, sans-serif',
          size: 20,
          weight: '700',
        },
        padding: {
          top: 15,
          bottom: 25
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'var(--border-color)',
        borderWidth: 1,
        padding: 12,
        displayColors: true,
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += context.parsed.y.toFixed(4);
            }
            return label;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: '📅 Дата',
          color: 'var(--text-color-primary)',
          font: {
            family: 'Inter, sans-serif',
            size: 14,
            weight: '600',
          },
        },
        ticks: {
          color: 'var(--text-color-secondary)',
          maxRotation: 45,
          minRotation: 0,
          font: {
            size: 11,
          },
        },
        grid: {
          color: 'var(--border-color-light)',
          drawBorder: false,
        },
      },
      y: {
        title: {
          display: true,
          text: '📊 Значение индекса',
          color: 'var(--text-color-primary)',
          font: {
            family: 'Inter, sans-serif',
            size: 14,
            weight: '600',
          },
        },
        min: -1,
        max: 1,
        ticks: {
          color: 'var(--text-color-secondary)',
          font: {
            size: 11,
          },
        },
        grid: {
          color: 'var(--border-color-light)',
          drawBorder: false,
        },
      },
    },
  }

  // Export chart as PNG
  const exportChartAsPNG = () => {
    if (chartRef.current) {
      const url = chartRef.current.toBase64Image('image/png', 1.0)
      const link = document.createElement('a')
      const indicesStr = selectedIndices.join('_')
      link.download = `timeseries_${indicesStr}_${startDate}_${endDate}.png`
      link.href = url
      link.click()
    }
  }

  // Export data as CSV
  const exportDataAsCSV = () => {
    if (!rawData || rawData.length === 0) {
      alert('Нет данных для экспорта')
      return
    }

    // Create CSV header with all indices
    let csvContent = 'Date,' + selectedIndices.join(',') + '\n'
    
    // Add data rows
    const numRows = rawData[0].dates.length
    for (let i = 0; i < numRows; i++) {
      const row = [rawData[0].dates[i]]
      // Add values for each index
      rawData.forEach(data => {
        row.push(data.values[i])
      })
      csvContent += row.join(',') + '\n'
    }

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    const indicesStr = selectedIndices.join('_')
    link.download = `timeseries_${indicesStr}_${startDate}_${endDate}.csv`
    link.href = url
    link.click()
    URL.revokeObjectURL(url)
  }

  // Toggle index selection
  const toggleIndex = (indexValue) => {
    setSelectedIndices(prev => {
      if (prev.includes(indexValue)) {
        // Don't allow removing if it's the last one
        if (prev.length === 1) return prev
        return prev.filter(i => i !== indexValue)
      } else {
        return [...prev, indexValue]
      }
    })
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📈 Анализ динамики вегетационных индексов</h2>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          <div className="ts-controls">
            <div className="ts-control-row">
              <div className="ts-control-group">
                <label>Начальная дата <span className="hint">(с 23.06.2015)</span></label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  min="2015-06-23"
                  max={endDate || undefined}
                  className="ts-input"
                />
              </div>

              <div className="ts-control-group">
                <label>Конечная дата</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  min={startDate || "2015-06-23"}
                  max={new Date().toISOString().split('T')[0]}
                  className="ts-input"
                />
              </div>

              <div className="ts-control-group ts-indices-group">
                <label>Индексы для анализа</label>
                <div className="ts-indices-checkboxes">
                  {VEGETATION_INDICES_OPTIONS.map((option) => (
                    <label key={option.value} className="ts-checkbox-label">
                      <input
                        type="checkbox"
                        checked={selectedIndices.includes(option.value)}
                        onChange={() => toggleIndex(option.value)}
                        className="ts-checkbox"
                      />
                      <span className="ts-checkbox-custom" style={{ borderColor: option.color }}>
                        {selectedIndices.includes(option.value) && <span style={{ backgroundColor: option.color }}>✓</span>}
                      </span>
                      <span className="ts-checkbox-text">
                        <span className="ts-index-dot" style={{ backgroundColor: option.color }}></span>
                        {option.label.split(' - ')[0]}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <button
              onClick={handleAnalyzeDynamics}
              className="btn btn-primary ts-analyze-btn"
              disabled={isLoading || !selectedGeometry}
            >
              {isLoading ? (
                <>
                  <span className="spinner-small"></span>
                  Загрузка...
                </>
              ) : (
                'Анализировать динамику'
              )}
            </button>

            {chartData && !showForecast && (
              <div className="ts-forecast-controls">
                <label className="ts-label">
                  Горизонт прогноза (дней):
                  <input
                    type="number"
                    min="7"
                    max="90"
                    value={forecastHorizon}
                    onChange={(e) => setForecastHorizon(Number(e.target.value))}
                    className="ts-input-small"
                  />
                </label>
                <button
                  onClick={handleGenerateForecast}
                  className="btn btn-secondary ts-forecast-btn"
                  disabled={isForecastLoading}
                  title="Прогноз на основе ML (Gradient Boosting)"
                >
                  {isForecastLoading ? (
                    <>
                      <span className="spinner-small"></span>
                      Генерация прогноза...
                    </>
                  ) : (
                    <>🤖 ML Прогноз ({selectedIndices[0]})</>
                  )}
                </button>
              </div>
            )}

            {showForecast && forecastData && (
              <div className="ts-forecast-info">
                <p>✅ Прогноз сгенерирован: <strong>{selectedIndices[0]}</strong> на <strong>{forecastHorizon} дней</strong></p>
                <p>Модель: <em>{forecastData.metadata.model_type}</em></p>
                <button
                  onClick={() => {
                    setShowForecast(false)
                    setForecastData(null)
                    handleAnalyzeDynamics() // Reload original data
                  }}
                  className="btn btn-small"
                >
                  Вернуться к исходным данным
                </button>
              </div>
            )}
          </div>

          {error && <div className="error-message">{error}</div>}

          {!selectedGeometry && !error && (
            <div className="info-message">
              ℹ️ Пожалуйста, выберите область на карте для анализа динамики
            </div>
          )}

          {chartData && (
            <>
              <div className="ts-export-buttons">
                <button 
                  className="btn btn-export" 
                  onClick={exportChartAsPNG}
                  title="Скачать график как PNG"
                >
                  📥 Скачать график (PNG)
                </button>
                <button 
                  className="btn btn-export" 
                  onClick={exportDataAsCSV}
                  title="Скачать данные как CSV"
                >
                  📄 Скачать данные (CSV)
                </button>
              </div>
              <div className="ts-chart-container">
                <Line ref={chartRef} data={chartData} options={options} />
              </div>
              <div className="ts-save-buttons">
                <SaveFieldButton 
                  geometry={selectedGeometry}
                  onFieldSaved={(field) => {
                    console.log('Field saved from time series:', field)
                  }}
                />
                <AddToDashboardButton 
                  geometry={selectedGeometry}
                  analysisParams={{
                    startDate: startDate,
                    endDate: endDate,
                    indexType: selectedIndices[0] // Use first selected index for dashboard
                  }}
                  itemType="time_series_chart"
                  onAdded={(item) => {
                    console.log('Added to dashboard from time series:', item)
                  }}
                />
              </div>
            </>
          )}

          {isLoading && (
            <div className="ts-loading">
              <div className="spinner"></div>
              <p>Анализ данных временного ряда...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default TimeSeriesModal

