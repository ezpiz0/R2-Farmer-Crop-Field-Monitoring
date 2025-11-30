import React, { useState } from 'react';
import './FieldZoningTool.css';

/**
 * FieldZoningTool Component
 * Allows users to create management zones based on NDVI clustering
 */
function FieldZoningTool({ analysisId, fieldId, onZonesCreated }) {
  const [numZones, setNumZones] = useState(4);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [zoneData, setZoneData] = useState(null);

  const handleCreateZones = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Необходима авторизация');
      }

      const requestBody = {
        num_zones: numZones
      };

      if (analysisId) {
        requestBody.analysis_id = analysisId;
      } else if (fieldId) {
        requestBody.field_id = fieldId;
      } else {
        throw new Error('Необходимо указать analysis_id или field_id');
      }

      const response = await fetch('/api/v1/analyze/zones', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка при создании зон');
      }

      const data = await response.json();
      setZoneData(data);

      // Call parent callback with zone data
      if (onZonesCreated) {
        onZonesCreated(data);
      }

    } catch (err) {
      console.error('Error creating zones:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getZoneDescription = (zones) => {
    const descriptions = {
      3: ['Слабая', 'Средняя', 'Сильная'],
      4: ['Очень слабая', 'Слабая', 'Средняя', 'Сильная'],
      5: ['Очень слабая', 'Слабая', 'Средняя', 'Сильная', 'Очень сильная']
    };
    return descriptions[zones] || [];
  };

  return (
    <div className="field-zoning-tool">
      <div className="zoning-header">
        <h3>🗺️ Зонирование поля</h3>
        <p className="zoning-description">
          Разделите поле на зоны управления на основе NDVI для дифференцированного внесения удобрений
        </p>
      </div>

      <div className="zoning-controls">
        <div className="zone-selector">
          <label htmlFor="num-zones">
            Количество зон: <strong>{numZones}</strong>
          </label>
          <input
            type="range"
            id="num-zones"
            min="3"
            max="5"
            value={numZones}
            onChange={(e) => setNumZones(parseInt(e.target.value))}
            disabled={loading}
          />
          <div className="zone-marks">
            <span>3</span>
            <span>4</span>
            <span>5</span>
          </div>
        </div>

        <div className="zone-preview">
          <h4>Типы зон ({numZones}):</h4>
          <ul className="zone-list">
            {getZoneDescription(numZones).map((desc, idx) => (
              <li key={idx} className={`zone-item zone-${idx + 1}`}>
                <span className={`zone-color zone-color-${idx + 1}`}></span>
                <span>Зона {idx + 1}: {desc}</span>
              </li>
            ))}
          </ul>
        </div>

        <button
          className="btn-create-zones"
          onClick={handleCreateZones}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              Создание зон...
            </>
          ) : (
            <>
              <span>📊</span>
              Разделить на зоны
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="zoning-error">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {zoneData && (
        <div className="zoning-results">
          <div className="results-header">
            <h4>✅ Зоны успешно созданы!</h4>
            <p>{zoneData.message}</p>
          </div>

          <div className="zone-statistics">
            <h5>Статистика по зонам:</h5>
            <div className="stats-grid">
              {Object.entries(zoneData.zone_statistics || {}).map(([zoneId, stats]) => (
                <div key={zoneId} className={`stat-card zone-${zoneId}`}>
                  <div className="stat-header">
                    <span className={`zone-badge zone-color-${zoneId}`}>Зона {zoneId}</span>
                    <span className="zone-label">
                      {zoneData.zone_geojson?.features?.find(f => f.properties.zone_id === parseInt(zoneId))?.properties.zone_label}
                    </span>
                  </div>
                  <div className="stat-values">
                    <div className="stat-item">
                      <span className="stat-label">Средний NDVI:</span>
                      <span className="stat-value">{stats.mean_ndvi.toFixed(3)}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Мин-Макс:</span>
                      <span className="stat-value">
                        {stats.min_ndvi.toFixed(2)} - {stats.max_ndvi.toFixed(2)}
                      </span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Пикселей:</span>
                      <span className="stat-value">{stats.pixel_count.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="download-section">
            <h5>💾 Скачать зоны:</h5>
            <div className="download-buttons">
              <a
                href={zoneData.download_links.geojson}
                className="btn-download geojson"
                download
              >
                <span>📄</span>
                GeoJSON
              </a>
              <a
                href={zoneData.download_links.shapefile}
                className="btn-download shapefile"
                download
              >
                <span>🗺️</span>
                Shapefile (ZIP)
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default FieldZoningTool;

