import React, { useState, useEffect } from 'react'
import { Line } from 'react-chartjs-2'
import api from '../utils/api'
import './DashboardWidget.css'

function TimeSeriesWidget({ item, onDelete }) {
  const [chartData, setChartData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadTimeSeriesData()
  }, [item])

  const loadTimeSeriesData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await api.post('/api/v1/analyze/timeseries', {
        geometry: item.field_geometry,
        start_date: item.start_date,
        end_date: item.end_date,
        index_type: item.index_type || 'NDVI'
      })

      const data = response.data
      setChartData({
        labels: data.dates,
        datasets: [
          {
            label: `${data.index_type}`,
            data: data.values,
            fill: true,
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            borderColor: 'rgba(102, 126, 234, 1)',
            tension: 0.3,
            pointRadius: 3,
            pointHoverRadius: 5,
          },
        ],
      })
    } catch (err) {
      console.error('Error loading time series:', err)
      setError('Ошибка загрузки данных временного ряда')
    } finally {
      setIsLoading(false)
    }
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(3)}`
          }
        }
      }
    },
    scales: {
      x: {
        ticks: {
          maxRotation: 45,
          minRotation: 0,
          font: { size: 10 }
        },
        grid: {
          display: false,
        },
      },
      y: {
        min: -0.2,
        max: 1,
        ticks: {
          font: { size: 10 }
        },
      },
    },
  }

  return (
    <div className="dashboard-widget">
      <div className="widget-header">
        <h3 className="widget-title">
          📈 {item.field_name} - {item.index_type || 'NDVI'}
        </h3>
        <div className="widget-actions">
          <button 
            className="widget-btn widget-btn-delete" 
            onClick={() => onDelete(item.id)}
            title="Удалить"
          >
            🗑️
          </button>
        </div>
      </div>

      <div className="widget-field-info">
        📅 {item.start_date} — {item.end_date}
      </div>

      <div className="widget-body">
        {isLoading && (
          <div className="widget-loading">
            <div className="spinner"></div>
            <p>Загрузка данных...</p>
          </div>
        )}

        {error && !isLoading && (
          <div className="widget-error">{error}</div>
        )}

        {chartData && !isLoading && (
          <div className="widget-chart-container">
            <Line data={chartData} options={chartOptions} />
          </div>
        )}
      </div>
    </div>
  )
}

export default TimeSeriesWidget

