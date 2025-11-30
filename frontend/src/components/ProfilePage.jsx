import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import ThemeToggle from './ThemeToggle'
import Header from './Header'
import api from '../utils/api'
import './ProfilePage.css'

const CROP_OPTIONS = [
  'Пшеница', 'Кукуруза', 'Подсолнечник', 'Ячмень', 'Рожь', 'Овес',
  'Соя', 'Рапс', 'Горох', 'Чечевица', 'Нут', 'Картофель',
  'Свекла', 'Морковь', 'Лук', 'Томаты', 'Огурцы', 'Капуста'
]

function ProfilePage() {
  const { logout, updateUser } = useAuth()
  const { isDarkTheme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  
  // States
  const [profile, setProfile] = useState(null)
  const [formData, setFormData] = useState({
    full_name: '',
    farm_name: '',
    country: '',
    region: '',
    phone_number: '',
    preferred_units: 'hectares',
    primary_crops: [],
    farming_type: '',
    irrigation_method: ''
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [stats, setStats] = useState({
    fields: 0,
    analyses: 0,
    dashboardItems: 0
  })
  const [isEditing, setIsEditing] = useState(false)

  useEffect(() => {
    loadProfile()
    loadStats()
  }, [])

  const loadProfile = async () => {
    try {
      const response = await api.get('/api/v1/auth/me/profile')
      setProfile(response.data)
      setFormData({
        full_name: response.data.full_name || '',
        farm_name: response.data.farm_name || '',
        country: response.data.country || '',
        region: response.data.region || '',
        phone_number: response.data.phone_number || '',
        preferred_units: response.data.preferred_units || 'hectares',
        primary_crops: response.data.primary_crops || [],
        farming_type: response.data.farming_type || '',
        irrigation_method: response.data.irrigation_method || ''
      })
    } catch (error) {
      console.error('Error loading profile:', error)
      setMessage({ type: 'error', text: 'Ошибка загрузки профиля' })
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const [fieldsRes, dashboardRes] = await Promise.all([
        api.get('/api/v1/fields'),
        api.get('/api/v1/dashboard/items')
      ])
      
      setStats({
        fields: fieldsRes.data.length,
        analyses: dashboardRes.data.length,
        dashboardItems: dashboardRes.data.length
      })
    } catch (error) {
      console.error('Error loading stats:', error)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleCropToggle = (crop) => {
    setFormData(prev => ({
      ...prev,
      primary_crops: prev.primary_crops.includes(crop)
        ? prev.primary_crops.filter(c => c !== crop)
        : [...prev.primary_crops, crop]
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage(null)

    try {
      const response = await api.put('/api/v1/auth/me/profile', formData)
      setProfile(response.data)
      setIsEditing(false)
      setMessage({ type: 'success', text: '✅ Профиль успешно обновлен!' })
      
      // Update user in AuthContext if available
      if (updateUser) {
        updateUser(response.data)
      }
    } catch (error) {
      console.error('Error updating profile:', error)
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Ошибка при сохранении профиля' 
      })
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    setFormData({
      full_name: profile?.full_name || '',
      farm_name: profile?.farm_name || '',
      country: profile?.country || '',
      region: profile?.region || '',
      phone_number: profile?.phone_number || '',
      preferred_units: profile?.preferred_units || 'hectares',
      primary_crops: profile?.primary_crops || [],
      farming_type: profile?.farming_type || '',
      irrigation_method: profile?.irrigation_method || ''
    })
    setIsEditing(false)
    setMessage(null)
  }

  const handleLogout = () => {
    if (window.confirm('Вы уверены, что хотите выйти?')) {
      logout()
      navigate('/auth')
    }
  }

  if (loading) {
    return (
      <div className="profile-page-wrapper">
        <Header />
        <div className="profile-page loading-state">
          <div className="spinner-large"></div>
          <p>Загрузка профиля...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="profile-page-wrapper">
      <Header />
      <div className="profile-page">
        <div className="profile-container">
          {/* Header */}
          <div className="profile-header">
            <div className="profile-avatar">
              <span className="avatar-icon">👤</span>
            </div>
            <h1>{profile?.full_name || profile?.email || 'Пользователь'}</h1>
            <p className="profile-email">{profile?.email}</p>
          </div>

          {/* Message */}
          {message && (
            <div className={`profile-message ${message.type}`}>
              {message.text}
            </div>
          )}

          {/* Stats Overview */}
          <div className="profile-section">
            <h2>📊 Статистика активности</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">📍</div>
                <div className="stat-value">{stats.fields}</div>
                <div className="stat-label">Сохраненных полей</div>
              </div>

              <div className="stat-card">
                <div className="stat-icon">📊</div>
                <div className="stat-value">{stats.analyses}</div>
                <div className="stat-label">Анализов</div>
              </div>

              <div className="stat-card">
                <div className="stat-icon">📈</div>
                <div className="stat-value">{stats.dashboardItems}</div>
                <div className="stat-label">На дашборде</div>
              </div>
            </div>
          </div>

          {/* Profile Form */}
          <div className="profile-section">
            <div className="section-header">
              <h2>👤 Личная информация</h2>
              {!isEditing && (
                <button className="btn-edit" onClick={() => setIsEditing(true)}>
                  ✏️ Редактировать
                </button>
              )}
            </div>

            <form onSubmit={handleSubmit} className="profile-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="full_name">Полное имя</label>
                  <input
                    type="text"
                    id="full_name"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    placeholder="Иван Иванович Иванов"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="phone_number">Номер телефона</label>
                  <input
                    type="tel"
                    id="phone_number"
                    name="phone_number"
                    value={formData.phone_number}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    placeholder="+7 (900) 123-45-67"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="country">Страна</label>
                  <input
                    type="text"
                    id="country"
                    name="country"
                    value={formData.country}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    placeholder="Россия"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="region">Регион/Область</label>
                  <input
                    type="text"
                    id="region"
                    name="region"
                    value={formData.region}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    placeholder="Воронежская область"
                  />
                </div>
              </div>

              <div className="form-divider"></div>

              <h3>🚜 Информация о ферме</h3>

              <div className="form-group">
                <label htmlFor="farm_name">Название фермы/хозяйства</label>
                <input
                  type="text"
                  id="farm_name"
                  name="farm_name"
                  value={formData.farm_name}
                  onChange={handleInputChange}
                  disabled={!isEditing}
                  placeholder='ООО "Агро Рассвет"'
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="preferred_units">Единицы измерения</label>
                  <select
                    id="preferred_units"
                    name="preferred_units"
                    value={formData.preferred_units}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                  >
                    <option value="hectares">Гектары (га)</option>
                    <option value="acres">Акры (ac)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="farming_type">Тип земледелия</label>
                  <select
                    id="farming_type"
                    name="farming_type"
                    value={formData.farming_type}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                  >
                    <option value="">Не указано</option>
                    <option value="conventional">Традиционное</option>
                    <option value="organic">Органическое</option>
                    <option value="mixed">Смешанное</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="irrigation_method">Метод орошения</label>
                  <select
                    id="irrigation_method"
                    name="irrigation_method"
                    value={formData.irrigation_method}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                  >
                    <option value="">Не указано</option>
                    <option value="rainfed">Богарное (без орошения)</option>
                    <option value="irrigated">Орошаемое</option>
                    <option value="mixed">Смешанное</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Основные культуры</label>
                <div className="crops-grid">
                  {CROP_OPTIONS.map((crop) => (
                    <label key={crop} className="crop-checkbox">
                      <input
                        type="checkbox"
                        checked={formData.primary_crops.includes(crop)}
                        onChange={() => handleCropToggle(crop)}
                        disabled={!isEditing}
                      />
                      <span>{crop}</span>
                    </label>
                  ))}
                </div>
                {formData.primary_crops.length > 0 && (
                  <div className="selected-crops">
                    Выбрано: {formData.primary_crops.join(', ')}
                  </div>
                )}
              </div>

              {isEditing && (
                <div className="form-actions">
                  <button 
                    type="button" 
                    className="btn btn-secondary"
                    onClick={handleCancel}
                    disabled={saving}
                  >
                    Отмена
                  </button>
                  <button 
                    type="submit" 
                    className="btn btn-primary"
                    disabled={saving}
                  >
                    {saving ? (
                      <>
                        <span className="spinner-small"></span>
                        Сохранение...
                      </>
                    ) : (
                      'Сохранить изменения'
                    )}
                  </button>
                </div>
              )}
            </form>
          </div>

          {/* Settings */}
          <div className="profile-section">
            <h2>⚙️ Настройки</h2>
            <div className="settings-list">
              <div className="setting-item">
                <div className="setting-info">
                  <span className="setting-label">Тема оформления</span>
                  <span className="setting-description">
                    Переключение между светлой и темной темой
                  </span>
                </div>
                <ThemeToggle isDark={isDarkTheme} onToggle={toggleTheme} />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="profile-actions">
            <button 
              className="profile-btn primary"
              onClick={() => navigate('/map')}
            >
              <span>📍</span>
              Перейти к карте
            </button>
            
            <button 
              className="profile-btn secondary"
              onClick={() => navigate('/dashboard')}
            >
              <span>📊</span>
              Мой дашборд
            </button>
            
            <button 
              className="profile-btn danger"
              onClick={handleLogout}
            >
              <span>🚪</span>
              Выйти из аккаунта
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProfilePage
