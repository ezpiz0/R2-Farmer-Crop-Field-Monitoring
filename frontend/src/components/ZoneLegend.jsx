import React from 'react';
import './ZoneLegend.css';

/**
 * ZoneLegend Component
 * Displays a legend explaining the zone color scheme
 */
function ZoneLegend({ numZones = 4, zoneStatistics = {} }) {
  const zoneLabelsSets = {
    3: ['Слабая', 'Средняя', 'Сильная'],
    4: ['Очень слабая', 'Слабая', 'Средняя', 'Сильная'],
    5: ['Очень слабая', 'Слабая', 'Средняя', 'Сильная', 'Очень сильная']
  };

  const zoneLabels = zoneLabelsSets[numZones] || zoneLabelsSets[4];

  const zoneColors = {
    1: '#d32f2f',
    2: '#f57c00',
    3: '#fbc02d',
    4: '#7cb342',
    5: '#388e3c'
  };

  return (
    <div className="zone-legend">
      <div className="legend-header">
        <h4>Зоны управления</h4>
        <span className="legend-subtitle">{numZones} зон</span>
      </div>
      
      <div className="legend-items">
        {Array.from({ length: numZones }, (_, i) => i + 1).map((zoneId) => {
          const stats = zoneStatistics[zoneId];
          const label = zoneLabels[zoneId - 1] || `Зона ${zoneId}`;
          
          return (
            <div key={zoneId} className="legend-item">
              <div className="legend-color-row">
                <span 
                  className="legend-color" 
                  style={{ backgroundColor: zoneColors[zoneId] }}
                ></span>
                <div className="legend-text">
                  <span className="legend-zone-id">Зона {zoneId}</span>
                  <span className="legend-zone-label">{label}</span>
                </div>
              </div>
              {stats && (
                <div className="legend-stats">
                  <span className="legend-ndvi">
                    NDVI: {stats.mean_ndvi.toFixed(3)}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="legend-footer">
        <div className="legend-gradient">
          <div className="gradient-bar"></div>
          <div className="gradient-labels">
            <span>Низкая продуктивность</span>
            <span>Высокая продуктивность</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ZoneLegend;

