import React, { useState, useEffect } from 'react'
import api from '../utils/api'
import './AddToDashboardButton.css'

function AddToDashboardButton({ 
  geometry, 
  analysisParams = {}, 
  itemType = 'time_series_chart',
  onAdded 
}) {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [fields, setFields] = useState([])
  const [selectedFieldId, setSelectedFieldId] = useState(null)
  const [isLoadingFields, setIsLoadingFields] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (isModalOpen) {
      loadFields()
    }
  }, [isModalOpen])

  const loadFields = async () => {
    setIsLoadingFields(true)
    setError(null)
    try {
      const response = await api.get('/api/v1/fields')
      setFields(response.data)
      if (response.data.length > 0) {
        setSelectedFieldId(response.data[0].id)
      }
    } catch (err) {
      console.error('Error loading fields:', err)
      setError('Ошибка при загрузке списка полей')
    } finally {
      setIsLoadingFields(false)
    }
  }

  const handleAddToDashboard = async () => {
    if (!selectedFieldId) {
      setError('Пожалуйста, выберите или создайте поле')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const dashboardItem = {
        field_id: selectedFieldId,
        item_type: itemType,
        start_date: analysisParams.startDate || null,
        end_date: analysisParams.endDate || null,
        index_type: analysisParams.indexType || 'NDVI'
      }

      const response = await api.post('/api/v1/dashboard/items', dashboardItem)

      setSuccess(true)
      setTimeout(() => {
        setIsModalOpen(false)
        setSuccess(false)
        if (onAdded) {
          onAdded(response.data)
        }
      }, 1500)
    } catch (err) {
      console.error('Error adding to dashboard:', err)
      setError(err.response?.data?.detail || 'Ошибка при добавлении на дашборд')
    } finally {
      setIsLoading(false)
    }
  }

  const openModal = () => {
    if (!geometry && itemType !== 'field_stats') {
      alert('Сначала выполните анализ поля!')
      return
    }
    setIsModalOpen(true)
    setError(null)
    setSuccess(false)
  }

  const closeModal = () => {
    if (!isLoading) {
      setIsModalOpen(false)
      setError(null)
      setSuccess(false)
    }
  }

  const getItemTypeLabel = () => {
    switch (itemType) {
      case 'time_series_chart':
        return 'График временного ряда'
      case 'latest_ndvi_map':
        return 'Карта NDVI'
      case 'field_stats':
        return 'Статистика поля'
      default:
        return 'Анализ'
    }
  }

  return (
    <>
      <button 
        className="btn btn-add-dashboard" 
        onClick={openModal}
        title="Добавить на дашборд"
      >
        📊 Добавить на дашборд
      </button>

      {isModalOpen && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content add-dashboard-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📊 Добавление на дашборд</h3>
              <button 
                className="modal-close" 
                onClick={closeModal}
                disabled={isLoading}
              >
                &times;
              </button>
            </div>

            <div className="modal-body">
              {success ? (
                <div className="success-message">
                  ✅ Анализ добавлен на дашборд!
                </div>
              ) : (
                <>
                  <div className="info-box">
                    <strong>Тип виджета:</strong> {getItemTypeLabel()}
                    {analysisParams.indexType && (
                      <div><strong>Индекс:</strong> {analysisParams.indexType}</div>
                    )}
                    {analysisParams.startDate && analysisParams.endDate && (
                      <div>
                        <strong>Период:</strong> {analysisParams.startDate} - {analysisParams.endDate}
                      </div>
                    )}
                  </div>

                  <div className="form-group">
                    <label htmlFor="field-select">Выберите поле</label>
                    {isLoadingFields ? (
                      <div className="loading-fields">Загрузка полей...</div>
                    ) : fields.length === 0 ? (
                      <div className="no-fields">
                        <p>У вас пока нет сохраненных полей.</p>
                        <p>Сначала нарисуйте поле на карте и сохраните его с помощью кнопки "Сохранить поле".</p>
                      </div>
                    ) : (
                      <select
                        id="field-select"
                        className="form-control"
                        value={selectedFieldId || ''}
                        onChange={(e) => setSelectedFieldId(parseInt(e.target.value))}
                        disabled={isLoading}
                      >
                        {fields.map((field) => (
                          <option key={field.id} value={field.id}>
                            {field.name}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>

                  {error && (
                    <div className="error-message">
                      {error}
                    </div>
                  )}

                  <div className="modal-actions">
                    <button
                      className="btn btn-secondary"
                      onClick={closeModal}
                      disabled={isLoading}
                    >
                      Отмена
                    </button>
                    <button
                      className="btn btn-primary"
                      onClick={handleAddToDashboard}
                      disabled={isLoading || !selectedFieldId || fields.length === 0}
                    >
                      {isLoading ? (
                        <>
                          <span className="spinner-small"></span>
                          Добавление...
                        </>
                      ) : (
                        'Добавить'
                      )}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default AddToDashboardButton

