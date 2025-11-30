import React, { useState } from 'react'
import api from '../utils/api'
import './SaveFieldButton.css'

function SaveFieldButton({ geometry, onFieldSaved }) {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [fieldName, setFieldName] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const handleSaveField = async () => {
    if (!fieldName.trim()) {
      setError('Пожалуйста, введите название поля')
      return
    }

    if (!geometry) {
      setError('Геометрия поля не выбрана')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await api.post('/api/v1/fields', {
        name: fieldName.trim(),
        geometry: geometry
      })

      setSuccess(true)
      setTimeout(() => {
        setIsModalOpen(false)
        setFieldName('')
        setSuccess(false)
        if (onFieldSaved) {
          onFieldSaved(response.data)
        }
      }, 1500)
    } catch (err) {
      console.error('Error saving field:', err)
      setError(err.response?.data?.detail || 'Ошибка при сохранении поля')
    } finally {
      setIsLoading(false)
    }
  }

  const openModal = () => {
    if (!geometry) {
      alert('Сначала нарисуйте поле на карте!')
      return
    }
    setIsModalOpen(true)
    setError(null)
    setSuccess(false)
  }

  const closeModal = () => {
    if (!isLoading) {
      setIsModalOpen(false)
      setFieldName('')
      setError(null)
      setSuccess(false)
    }
  }

  return (
    <>
      <button 
        className="btn btn-save-field" 
        onClick={openModal}
        disabled={!geometry}
        title={!geometry ? 'Сначала нарисуйте поле на карте' : 'Сохранить поле'}
      >
        💾 Сохранить поле
      </button>

      {isModalOpen && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content save-field-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>💾 Сохранение поля</h3>
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
                  ✅ Поле успешно сохранено!
                </div>
              ) : (
                <>
                  <div className="form-group">
                    <label htmlFor="field-name">Название поля</label>
                    <input
                      id="field-name"
                      type="text"
                      className="form-control"
                      value={fieldName}
                      onChange={(e) => setFieldName(e.target.value)}
                      placeholder="Например: Поле №1, Пшеничное поле"
                      maxLength={200}
                      disabled={isLoading}
                      autoFocus
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          handleSaveField()
                        }
                      }}
                    />
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
                      onClick={handleSaveField}
                      disabled={isLoading || !fieldName.trim()}
                    >
                      {isLoading ? (
                        <>
                          <span className="spinner-small"></span>
                          Сохранение...
                        </>
                      ) : (
                        'Сохранить'
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

export default SaveFieldButton

